# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .. import const
from .common import EsewaCommon


@tagged("post_install", "-at_install")
class TestPaymentEsewa(EsewaCommon):
    # === SIGNATURE === #

    def test_signature_matches_documented_example(self):
        """
        The request signature matches the sample form of the official documentation.
        """
        signature = self.esewa._esewa_calculate_signature(
            {
                "total_amount": "110",
                "transaction_uuid": "241028",
                "product_code": "EPAYTEST",
            },
            const.REQUEST_SIGNED_FIELDS,
        )
        self.assertEqual(signature, "i94zsd3oXF6ZsSr/kGqT4sSzYQzjj1W/waxjWyRwaME=")

    def test_signature_depends_on_secret(self):
        data = {
            "total_amount": "100",
            "transaction_uuid": "1",
            "product_code": "EPAYTEST",
        }
        signature = self.esewa._esewa_calculate_signature(
            data, const.REQUEST_SIGNED_FIELDS
        )
        self.esewa.esewa_secret_key = "another-secret"
        self.assertNotEqual(
            signature,
            self.esewa._esewa_calculate_signature(data, const.REQUEST_SIGNED_FIELDS),
        )

    # === CONFIGURATION === #

    def test_only_npr_is_supported(self):
        self.assertEqual(self.esewa.available_currency_ids, self.currency_npr)

    def test_environment_urls_follow_provider_state(self):
        self.assertEqual(
            self.esewa._esewa_get_environment_url(const.PAYMENT_FORM_URLS),
            "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        )
        self.esewa.state = "enabled"
        self.assertEqual(
            self.esewa._esewa_get_environment_url(const.PAYMENT_FORM_URLS),
            "https://epay.esewa.com.np/api/epay/main/v2/form",
        )
        self.assertEqual(
            self.esewa._build_request_url(""),
            "https://esewa.com.np/api/epay/transaction/status/",
        )

    def test_disabled_provider_has_no_fallback_url(self):
        self.esewa.state = "disabled"
        with self.assertRaises(ValidationError):
            self.esewa._esewa_get_environment_url(const.PAYMENT_FORM_URLS)

    def test_reference_only_contains_allowed_characters(self):
        reference = self.env["payment.transaction"]._compute_reference(
            "esewa", prefix="INV/2026/0001 é"
        )
        self.assertRegex(reference, r"^[A-Za-z0-9-]+$")

    def test_reference_is_unique_for_esewa(self):
        """References are timestamped so that eSewa never sees a transaction UUID twice,
        even after a database reset or on the shared test merchant."""
        reference = self.env["payment.transaction"]._compute_reference(
            "esewa", prefix="S00001"
        )
        self.assertRegex(reference, r"^S00001-\d{12}$")

    # === RENDERING === #

    def test_redirect_form_values(self):
        tx = self._create_transaction(flow="redirect")
        processing_values = tx._get_processing_values()
        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )
        self.assertEqual(form_info["action"], const.PAYMENT_FORM_URLS["test"])
        self.assertEqual(form_info["method"], "post")
        inputs = form_info["inputs"]
        self.assertEqual(inputs["total_amount"], "1000.00")
        self.assertEqual(inputs["transaction_uuid"], self.reference)
        self.assertEqual(inputs["product_code"], "EPAYTEST")
        self.assertEqual(
            inputs["signed_field_names"], "total_amount,transaction_uuid,product_code"
        )
        self.assertEqual(
            inputs["signature"],
            self.esewa._esewa_calculate_signature(inputs, const.REQUEST_SIGNED_FIELDS),
        )
        self.assertNotIn(
            self.esewa.esewa_secret_key, processing_values["redirect_form_html"]
        )

    def test_rendering_rejects_other_currencies(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})

    # === STATUS PROCESSING === #

    def test_complete_status_confirms_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, "0001TS9")
        # The status is requested with Odoo's own values, never the customer's.
        self.assertEqual(
            mock.call_args.kwargs["params"],
            {
                "product_code": "EPAYTEST",
                "total_amount": "1000.00",
                "transaction_uuid": "S00042-1",
            },
        )
        self.assertEqual(mock.call_args.kwargs["timeout"], 10)

    def test_pending_status_sets_pending(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("PENDING", ref_id=None)):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "pending")

    def test_ambiguous_status_sets_pending(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("AMBIGUOUS")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "pending")

    def test_canceled_status_cancels_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("CANCELED")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "cancel")

    def test_refund_status_is_never_a_success(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("FULL_REFUND")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_recent_not_found_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("NOT_FOUND")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    def test_expired_not_found_cancels_transaction(self):
        tx = self._create_transaction(flow="redirect")
        old_date = tx.create_date - timedelta(
            minutes=const.NOT_FOUND_CANCEL_DELAY_MINUTES + 1
        )
        self.env.cr.execute(
            "UPDATE payment_transaction SET create_date = %s WHERE id = %s",
            (old_date, tx.id),
        )
        tx.invalidate_recordset()
        with self._mock_status_api(self._status_data("NOT_FOUND")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "cancel")

    @mute_logger("odoo.addons.payment_esewa.models.payment_transaction")
    def test_unknown_status_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("WHATEVER")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_amount_mismatch_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data(total_amount=10.0)):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_missing_amount_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data(total_amount=None)):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_currency_mismatch_sets_error(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self._mock_status_api(self._status_data()):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_esewa.models.payment_transaction")
    def test_reference_mismatch_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data(transaction_uuid="S00099")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_esewa.models.payment_transaction")
    def test_merchant_mismatch_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data(product_code="OTHER")):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_esewa.models.payment_transaction")
    def test_complete_status_without_identity_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        data = self._status_data()
        del data["product_code"]
        with self._mock_status_api(data):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_esewa.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_verification_timeout_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(side_effect=requests.exceptions.Timeout()):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_esewa.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_provider_outage_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(side_effect=requests.exceptions.ConnectionError()):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "draft")

    def test_duplicate_notification_does_not_reprocess(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            tx._esewa_verify_and_process()
            tx._esewa_verify_and_process()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_out_of_order_status_does_not_revert_done(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()):
            tx._esewa_verify_and_process()
        tx._process("esewa", self._status_data("PENDING"))
        self.assertEqual(tx.state, "done")

    def test_pending_then_complete_confirms_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("PENDING")):
            tx._esewa_verify_and_process()
        with self._mock_status_api(self._status_data()):
            tx._esewa_verify_and_process()
        self.assertEqual(tx.state, "done")

    # === SCHEDULED ACTION === #

    def test_cron_settles_recent_unsettled_transactions(self):
        tx = self._create_transaction(flow="redirect")
        recent_tx = self._create_transaction(flow="redirect", reference="S00043")
        old_date = tx.create_date - timedelta(
            minutes=const.UNSETTLED_TX_MIN_AGE_MINUTES + 1
        )
        self.env.cr.execute(
            "UPDATE payment_transaction SET create_date = %s WHERE id = %s",
            (old_date, tx.id),
        )
        (tx | recent_tx).invalidate_recordset()
        with self._mock_status_api(self._status_data()) as mock:
            self.env["payment.transaction"]._esewa_cron_check_unsettled_transactions()
        self.assertEqual(mock.call_count, 1)  # Too-recent transactions are left alone.
        self.assertEqual(tx.state, "done")
        self.assertEqual(recent_tx.state, "draft")

    def test_only_supported_features_are_declared(self):
        self.assertFalse(self.esewa.support_tokenization)
        self.assertFalse(self.esewa.support_express_checkout)
        self.assertFalse(self.esewa.support_manual_capture)
        self.assertEqual(self.esewa.support_refund, "none")
        self.assertEqual(
            self.esewa.payment_method_ids,
            self.env.ref("payment_esewa.payment_method_esewa"),
        )
