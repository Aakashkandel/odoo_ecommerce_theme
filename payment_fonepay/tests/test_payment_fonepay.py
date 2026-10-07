# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hashlib
import hmac

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .. import const
from .common import TEST_BASE_URL, FonepayCommon


@tagged("post_install", "-at_install")
class TestPaymentFonepay(FonepayCommon):
    # === DV === #

    def test_dv_is_hmac_sha512_of_ordered_values(self):
        data = {
            field: f"v{index}"
            for index, field in enumerate(const.REQUEST_SIGNED_FIELDS)
        }
        expected_dv = (
            hmac.new(
                b"dummy-test-secret-key",
                ",".join(f"v{index}" for index in range(9)).encode(),
                hashlib.sha512,
            )
            .hexdigest()
            .upper()
        )
        self.assertEqual(
            self.fonepay._fonepay_calculate_dv(data, const.REQUEST_SIGNED_FIELDS),
            expected_dv,
        )

    # === CONFIGURATION === #

    def test_only_npr_is_supported(self):
        self.assertEqual(self.fonepay.available_currency_ids, self.currency_npr)

    def test_urls_follow_provider_state(self):
        self.assertEqual(
            self.fonepay._fonepay_get_url(const.PAYMENT_PATH),
            f"{TEST_BASE_URL}/api/merchantRequest",
        )
        with self.assertRaises(ValidationError):
            # No silent fallback on the test environment when enabled.
            self.fonepay.state = "enabled"
        self.fonepay.write(
            {
                "state": "enabled",
                "fonepay_production_base_url": "https://live.example.test",
            }
        )
        self.assertEqual(
            self.fonepay._build_request_url(const.VERIFICATION_PATH),
            "https://live.example.test/api/merchantRequest/verificationMerchant",
        )

    def test_disabled_provider_has_no_url(self):
        self.fonepay.state = "disabled"
        with self.assertRaises(ValidationError):
            self.fonepay._fonepay_get_url(const.PAYMENT_PATH)

    def test_insecure_base_url_is_rejected(self):
        for url in ("http://dev.example.test", "https://dev.example.test/api?x=1"):
            with self.assertRaises(ValidationError):
                self.fonepay.fonepay_test_base_url = url

    def test_only_supported_features_are_declared(self):
        self.assertFalse(self.fonepay.support_tokenization)
        self.assertFalse(self.fonepay.support_express_checkout)
        self.assertFalse(self.fonepay.support_manual_capture)
        self.assertEqual(self.fonepay.support_refund, "none")

    def test_reference_is_accepted_as_prn(self):
        Transaction = self.env["payment.transaction"]
        for prefix in (
            "INV/2026/00001",
            "A-very-long-reference-prefix-1234567",
            "é",
            "S1",
        ):
            reference = Transaction._compute_reference("fonepay", prefix=prefix)
            self.assertRegex(reference, r"^[A-Za-z0-9-]{3,25}$")

    def test_reference_is_unique_for_fonepay(self):
        reference = self.env["payment.transaction"]._compute_reference(
            "fonepay", prefix="S00001"
        )
        self.assertRegex(reference, r"^S00001-\d{12}$")

    # === RENDERING === #

    def test_redirect_form_values(self):
        tx = self._create_transaction(flow="redirect")
        processing_values = tx._get_processing_values()
        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )
        self.assertEqual(form_info["action"], f"{TEST_BASE_URL}/api/merchantRequest")
        self.assertEqual(form_info["method"], "get")
        inputs = form_info["inputs"]
        self.assertEqual(inputs["PID"], "TESTMERCHANT")
        self.assertEqual(inputs["MD"], "P")
        self.assertEqual(inputs["PRN"], self.reference)
        self.assertEqual(inputs["AMT"], "1000.00")
        self.assertEqual(inputs["CRN"], "NPR")
        self.assertRegex(inputs["DT"], r"^\d{2}/\d{2}/\d{4}$")
        self.assertTrue(inputs["RU"].endswith("/payment/fonepay/return"))
        self.assertEqual(
            inputs["DV"],
            self.fonepay._fonepay_calculate_dv(inputs, const.REQUEST_SIGNED_FIELDS),
        )
        self.assertNotIn(
            "dummy-test-secret-key", processing_values["redirect_form_html"]
        )

    def test_rendering_rejects_other_currencies(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})

    # === REDIRECTION PROCESSING === #

    def test_successful_payment_is_verified_server_side(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.provider_reference, "1234567")
        params = mock.call_args.kwargs["params"]
        self.assertEqual(
            params["AMT"], "1000.00"
        )  # Odoo's amount, not the redirection's.
        self.assertEqual(params["BID"], "NIBLNPKT")
        self.assertEqual(
            params["DV"],
            self.fonepay._fonepay_calculate_dv(
                params, const.VERIFICATION_SIGNED_FIELDS
            ),
        )
        self.assertEqual(mock.call_args.kwargs["timeout"], 10)

    @mute_logger("odoo.addons.payment_fonepay.models.payment_transaction")
    def test_unverified_payment_is_not_confirmed(self):
        tx = self._create_transaction(flow="redirect")
        for xml in (
            self._verification_xml(success="false", response_code="failed"),
            self._verification_xml(success="true", response_code="failed"),
            self._verification_xml(success="false", response_code="successful"),
            "<response/>",
        ):
            with self._mock_verification_api(xml):
                tx._fonepay_process_redirection(self._redirection_data())
            self.assertEqual(tx.state, "draft")

    def test_amount_mismatch_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml(amount="10.0")):
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "error")

    def test_currency_mismatch_sets_error(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self._mock_verification_api(self._verification_xml()):
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_fonepay.models.payment_transaction")
    def test_uid_mismatch_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml(uid="7654321")):
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "draft")

    def test_canceled_payment_cancels_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            tx._fonepay_process_redirection(
                self._redirection_data(ps="false", rc="cancel")
            )
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "cancel")

    def test_failed_payment_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            tx._fonepay_process_redirection(
                self._redirection_data(ps="false", rc="failed")
            )
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_fonepay.models.payment_transaction")
    def test_inconsistent_status_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            tx._fonepay_process_redirection(
                self._redirection_data(ps="false", rc="successful")
            )
            tx._fonepay_process_redirection(
                self._redirection_data(ps="true", rc="cancel")
            )
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_fonepay.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_malformed_verification_response_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        for content in (
            "not xml",
            '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>',
        ):
            with self._mock_verification_api(content):
                tx._fonepay_process_redirection(self._redirection_data())
            self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_fonepay.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_verification_timeout_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(side_effect=requests.exceptions.Timeout()):
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "draft")
        # The scheduled action verifies the payment once Fonepay is reachable again.
        with self._mock_verification_api(self._verification_xml()):
            self.env[
                "payment.transaction"
            ]._fonepay_cron_verify_unsettled_transactions()
        self.assertEqual(tx.state, "done")

    @mute_logger(
        "odoo.addons.payment_fonepay.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_provider_outage_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(
            side_effect=requests.exceptions.ConnectionError()
        ):
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(tx.state, "draft")

    def test_duplicate_notification_does_not_reprocess(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            tx._fonepay_process_redirection(self._redirection_data())
            tx._fonepay_process_redirection(self._redirection_data())
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_out_of_order_status_does_not_revert_done(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()):
            tx._fonepay_process_redirection(self._redirection_data())
        tx._process("fonepay", {"PRN": self.reference, "status": "cancel"})
        self.assertEqual(tx.state, "done")

    def test_cron_ignores_transactions_without_payment(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            self.env[
                "payment.transaction"
            ]._fonepay_cron_verify_unsettled_transactions()
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")
