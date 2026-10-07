# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .. import const
from .common import KhaltiCommon


@tagged("post_install", "-at_install")
class TestPaymentKhalti(KhaltiCommon):
    # === CONFIGURATION === #

    def test_only_npr_is_supported(self):
        self.assertEqual(self.khalti.available_currency_ids, self.currency_npr)

    def test_api_urls_follow_provider_state(self):
        self.assertEqual(
            self.khalti._build_request_url(const.LOOKUP_ENDPOINT),
            "https://dev.khalti.com/api/v2/epayment/lookup/",
        )
        self.khalti.state = "enabled"
        self.assertEqual(
            self.khalti._build_request_url(const.LOOKUP_ENDPOINT),
            "https://khalti.com/api/v2/epayment/lookup/",
        )

    def test_disabled_provider_has_no_fallback_url(self):
        self.khalti.state = "disabled"
        with self.assertRaises(ValidationError):
            self.khalti._build_request_url(const.LOOKUP_ENDPOINT)

    def test_authorization_header(self):
        headers = self.khalti._build_request_headers("POST", const.LOOKUP_ENDPOINT, {})
        self.assertEqual(headers["Authorization"], "Key dummy-test-secret-key")

    def test_reference_is_unique_for_khalti(self):
        reference = self.env["payment.transaction"]._compute_reference(
            "khalti", prefix="S00001"
        )
        self.assertRegex(reference, r"^S00001-\d{12}$")

    def test_only_supported_features_are_declared(self):
        self.assertFalse(self.khalti.support_tokenization)
        self.assertFalse(self.khalti.support_express_checkout)
        self.assertFalse(self.khalti.support_manual_capture)
        self.assertEqual(self.khalti.support_refund, "none")

    # === INITIATION === #

    def test_initiation_redirects_to_payment_url(self):
        tx = self._create_transaction(flow="redirect")
        initiate_data = {
            "pidx": self.pidx,
            "payment_url": f"https://test-pay.khalti.com/?pidx={self.pidx}",
            "expires_at": "2026-10-07T12:00:00+05:45",
            "expires_in": 1800,
        }
        with self._mock_khalti_api(initiate_data) as mock:
            processing_values = tx._get_processing_values()
        payload = mock.call_args.kwargs["json"]
        self.assertEqual(payload["amount"], 100000)  # In paisa.
        self.assertEqual(payload["purchase_order_id"], self.reference)
        self.assertTrue(payload["return_url"].endswith("/payment/khalti/return"))
        self.assertEqual(mock.call_args.kwargs["timeout"], 10)
        self.assertEqual(tx.provider_reference, self.pidx)
        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )
        self.assertEqual(form_info["action"], "https://test-pay.khalti.com/")
        self.assertEqual(form_info["inputs"], {"pidx": self.pidx})
        self.assertNotIn(
            "dummy-test-secret-key", processing_values["redirect_form_html"]
        )

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_initiation_rejects_foreign_payment_url(self):
        tx = self._create_transaction(flow="redirect")
        initiate_data = {
            "pidx": self.pidx,
            "payment_url": "https://evil.example.com/?pidx=x",
        }
        with self._mock_khalti_api(initiate_data), self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})

    def test_initiation_rejects_amounts_below_minimum(self):
        tx = self._create_transaction(flow="redirect", amount=9.99)
        with self._mock_khalti_api({}) as mock, self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})
        self.assertEqual(mock.call_count, 0)

    def test_initiation_rejects_other_currencies(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})

    @mute_logger("odoo.addons.payment.models.payment_provider")
    def test_initiation_failure_is_reported(self):
        tx = self._create_transaction(flow="redirect")
        error = {"detail": "Invalid token.", "status_code": 401}
        with (
            self._mock_khalti_api(error, status_code=401),
            self.assertRaises(ValidationError),
        ):
            tx._get_specific_rendering_values({})

    # === LOOKUP PROCESSING === #

    def test_completed_lookup_confirms_transaction(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            tx._khalti_verify_and_process()
        self.assertEqual(mock.call_args.kwargs["json"], {"pidx": self.pidx})
        self.assertEqual(tx.state, "done")

    def test_pending_lookup_sets_pending(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Pending")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "pending")

    def test_initiated_lookup_sets_pending(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Initiated")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "pending")

    def test_user_canceled_lookup_cancels_transaction(self):
        """Khalti answers with HTTP 400 for canceled payments."""
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("User canceled"), status_code=400):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "cancel")

    def test_expired_lookup_cancels_transaction(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Expired"), status_code=400):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "cancel")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_refunded_lookup_is_never_a_success(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Refunded")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_completed_but_refunded_lookup_is_never_a_success(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data(refunded=True)):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_unknown_status_sets_error(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Whatever")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_amount_mismatch_sets_error(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data(total_amount=1000)):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_malformed_amount_sets_error(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data(total_amount="100000")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_currency_mismatch_sets_error(self):
        tx = self._create_initiated_transaction(currency_id=self.currency_euro.id)
        with self._mock_khalti_api(self._lookup_data()):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_pidx_mismatch_is_ignored(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data(pidx="AnotherPidx")):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_not_initiated_transaction_is_not_looked_up(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_khalti_api(self._lookup_data()) as mock:
            tx._khalti_verify_and_process()
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_khalti.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_lookup_not_found_keeps_transaction_open(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api({"detail": "Not found."}, status_code=404):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_khalti.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_malformed_lookup_response_keeps_transaction_open(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(["not", "a", "dict"]):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_lookup_timeout_keeps_transaction_open(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(side_effect=requests.exceptions.Timeout()):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_khalti.models.payment_transaction")
    def test_provider_outage_keeps_transaction_open(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(side_effect=requests.exceptions.ConnectionError()):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "draft")

    def test_duplicate_notification_does_not_reprocess(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            tx._khalti_verify_and_process()
            tx._khalti_verify_and_process()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_out_of_order_status_does_not_revert_done(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()):
            tx._khalti_verify_and_process()
        tx._process("khalti", self._lookup_data("Pending"))
        tx._process("khalti", self._lookup_data("Expired"))
        self.assertEqual(tx.state, "done")

    def test_pending_then_completed_confirms_transaction(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Pending")):
            tx._khalti_verify_and_process()
        with self._mock_khalti_api(self._lookup_data()):
            tx._khalti_verify_and_process()
        self.assertEqual(tx.state, "done")

    # === SCHEDULED ACTION === #

    def test_cron_settles_recent_unsettled_transactions(self):
        tx = self._create_initiated_transaction()
        recent_tx = self._create_transaction(
            flow="redirect", reference="S00043", provider_reference="Other"
        )
        not_initiated_tx = self._create_transaction(flow="redirect", reference="S00044")
        old_date = tx.create_date - timedelta(
            minutes=const.UNSETTLED_TX_MIN_AGE_MINUTES + 1
        )
        self.env.cr.execute(
            "UPDATE payment_transaction SET create_date = %s WHERE id IN %s",
            (old_date, (tx.id, not_initiated_tx.id)),
        )
        (tx | recent_tx | not_initiated_tx).invalidate_recordset()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            self.env["payment.transaction"]._khalti_cron_check_unsettled_transactions()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")
        self.assertEqual(recent_tx.state, "draft")
        self.assertEqual(not_initiated_tx.state, "draft")
