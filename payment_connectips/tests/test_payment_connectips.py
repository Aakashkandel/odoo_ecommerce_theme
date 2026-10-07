# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
from datetime import timedelta

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .. import const
from .common import TEST_BASE_URL, ConnectipsCommon, generate_test_pfx


@tagged("post_install", "-at_install")
class TestPaymentConnectips(ConnectipsCommon):
    def _assert_valid_token(self, token, message):
        self.private_key.public_key().verify(
            base64.b64decode(token),
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

    # === TOKEN === #

    def test_login_page_token_is_documented_signature(self):
        data = {
            "MERCHANTID": "550",
            "APPID": "MER-550-APP-1",
            "APPNAME": "Odoo Test",
            "TXNID": "txn-123",
            "TXNDATE": "07-10-2026",
            "TXNCRNCY": "NPR",
            "TXNAMT": "50000",
            "REFERENCEID": "txn-123",
            "REMARKS": "txn-123",
            "PARTICULARS": "Company",
        }
        token = self.connectips._connectips_calculate_token(
            data, const.LOGIN_PAGE_SIGNED_FIELDS
        )
        self._assert_valid_token(
            token,
            "MERCHANTID=550,APPID=MER-550-APP-1,APPNAME=Odoo Test,TXNID=txn-123,"
            "TXNDATE=07-10-2026,TXNCRNCY=NPR,TXNAMT=50000,REFERENCEID=txn-123,REMARKS=txn-123,"
            "PARTICULARS=Company,TOKEN=TOKEN",
        )

    def test_validation_token_is_documented_signature(self):
        data = {
            "MERCHANTID": "550",
            "APPID": "MER-550-APP-1",
            "REFERENCEID": "txn-123",
            "TXNAMT": "500",
        }
        token = self.connectips._connectips_calculate_token(
            data, const.VALIDATE_TXN_SIGNED_FIELDS
        )
        self._assert_valid_token(
            token, "MERCHANTID=550,APPID=MER-550-APP-1,REFERENCEID=txn-123,TXNAMT=500"
        )

    def test_token_from_another_key_is_rejected(self):
        data = {"MERCHANTID": "550", "APPID": "A", "REFERENCEID": "R", "TXNAMT": "1"}
        token = self.connectips._connectips_calculate_token(
            data, const.VALIDATE_TXN_SIGNED_FIELDS
        )
        with self.assertRaises(InvalidSignature):
            self._assert_valid_token(
                token, "MERCHANTID=550,APPID=A,REFERENCEID=R,TXNAMT=2"
            )

    # === CONFIGURATION === #

    def test_only_npr_is_supported(self):
        self.assertEqual(self.connectips.available_currency_ids, self.currency_npr)

    def test_urls_follow_provider_state(self):
        self.assertEqual(
            self.connectips._connectips_get_url(const.LOGIN_PAGE_PATH),
            f"{TEST_BASE_URL}/connectipswebgw/loginpage",
        )
        with self.assertRaises(ValidationError):
            # No silent fallback on the test environment when enabled.
            self.connectips.state = "enabled"
        self.connectips.write(
            {
                "state": "enabled",
                "connectips_production_base_url": "https://live.example.test/",
            }
        )
        self.assertEqual(
            self.connectips._build_request_url(const.VALIDATE_TXN_PATH),
            "https://live.example.test/connectipswebws/api/creditor/validatetxn",
        )

    def test_disabled_provider_has_no_url(self):
        self.connectips.state = "disabled"
        with self.assertRaises(ValidationError):
            self.connectips._connectips_get_url(const.LOGIN_PAGE_PATH)

    def test_insecure_base_url_is_rejected(self):
        for url in ("http://uat.example.test", "https://uat.example.test/path?x=1"):
            with self.assertRaises(ValidationError):
                self.connectips.connectips_test_base_url = url

    def test_non_numeric_merchant_id_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.connectips.connectips_merchant_id = "55O"

    def test_wrong_certificate_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.connectips.connectips_certificate_password = "wrong-password"

    def test_invalid_certificate_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.connectips.connectips_certificate = base64.b64encode(b"not a pfx")

    def test_certificate_without_password_is_supported(self):
        _private_key, pfx_data = generate_test_pfx(password="")
        self.connectips.write(
            {
                "connectips_certificate": base64.b64encode(pfx_data),
                "connectips_certificate_password": False,
            }
        )
        self.assertTrue(self.connectips._connectips_load_private_key())

    def test_api_authentication(self):
        self.assertEqual(
            self.connectips._build_request_auth(),
            ("MER-550-APP-1", "dummy-api-password"),
        )

    def test_only_supported_features_are_declared(self):
        self.assertFalse(self.connectips.support_tokenization)
        self.assertFalse(self.connectips.support_express_checkout)
        self.assertFalse(self.connectips.support_manual_capture)
        self.assertEqual(self.connectips.support_refund, "none")

    def test_reference_is_accepted_as_txnid(self):
        Transaction = self.env["payment.transaction"]
        for prefix in ("INV/2026/00001", "A-very-long-reference-prefix-123", "é"):
            reference = Transaction._compute_reference("connectips", prefix=prefix)
            self.assertRegex(reference, const.TXNID_PATTERN)

    def test_reference_is_unique_for_connectips(self):
        reference = self.env["payment.transaction"]._compute_reference(
            "connectips", prefix="S00001"
        )
        self.assertRegex(reference, r"^S00001-[0-9A-Z]{6}$")

    # === RENDERING === #

    def test_redirect_form_values(self):
        tx = self._create_transaction(flow="redirect")
        processing_values = tx._get_processing_values()
        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )
        self.assertEqual(
            form_info["action"], f"{TEST_BASE_URL}/connectipswebgw/loginpage"
        )
        self.assertEqual(form_info["method"], "post")
        inputs = form_info["inputs"]
        self.assertEqual(inputs["TXNID"], self.reference)
        self.assertEqual(inputs["TXNAMT"], "50000")  # In paisa.
        self.assertEqual(inputs["TXNCRNCY"], "NPR")
        self.assertRegex(inputs["TXNDATE"], r"^\d{2}-\d{2}-\d{4}$")
        self._assert_valid_token(
            inputs["TOKEN"],
            ",".join(
                f"{field}={inputs[field]}" for field in const.LOGIN_PAGE_SIGNED_FIELDS
            )
            + ",TOKEN=TOKEN",
        )
        html = processing_values["redirect_form_html"]
        self.assertNotIn("dummy-api-password", html)
        self.assertNotIn("dummy-pfx-password", html)

    def test_rendering_rejects_other_currencies(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self.assertRaises(ValidationError):
            tx._get_specific_rendering_values({})

    # === VALIDATION PROCESSING === #

    def test_success_confirms_transaction(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()) as mock:
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "done")
        payload = mock.call_args.kwargs["json"]
        self.assertEqual(payload["referenceId"], self.reference)
        self.assertEqual(payload["txnAmt"], 50000)
        self.assertEqual(payload["merchantId"], 550)
        self._assert_valid_token(
            payload["token"],
            "MERCHANTID=550,APPID=MER-550-APP-1,REFERENCEID=S00042-1,TXNAMT=50000",
        )
        self.assertEqual(
            mock.call_args.kwargs["auth"], ("MER-550-APP-1", "dummy-api-password")
        )
        self.assertEqual(mock.call_args.kwargs["timeout"], 10)

    def test_failed_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data("FAILED")):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_recent_not_found_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data("ERROR")):
            tx._connectips_verify_and_process()
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
        with self._mock_validation_api(self._validation_data("ERROR")):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "cancel")

    @mute_logger("odoo.addons.payment_connectips.models.payment_transaction")
    def test_unknown_status_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data("WHATEVER")):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_amount_mismatch_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data(txnAmt=500)):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_missing_amount_sets_error(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data(txnAmt=None)):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "error")

    def test_currency_mismatch_sets_error(self):
        tx = self._create_transaction(
            flow="redirect", currency_id=self.currency_euro.id
        )
        with self._mock_validation_api(self._validation_data()):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_connectips.models.payment_transaction")
    def test_identity_mismatch_is_ignored(self):
        tx = self._create_transaction(flow="redirect")
        for overrides in (
            {"referenceId": "S00099"},
            {"merchantId": 551},
            {"appId": "OTHER"},
        ):
            with self._mock_validation_api(self._validation_data(**overrides)):
                tx._connectips_verify_and_process()
            self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_connectips.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_validation_timeout_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(side_effect=requests.exceptions.Timeout()):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "draft")

    @mute_logger(
        "odoo.addons.payment_connectips.models.payment_transaction",
        "odoo.addons.payment.models.payment_provider",
    )
    def test_provider_outage_keeps_transaction_open(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(
            side_effect=requests.exceptions.ConnectionError()
        ):
            tx._connectips_verify_and_process()
        self.assertEqual(tx.state, "draft")

    def test_duplicate_notification_does_not_reprocess(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()) as mock:
            tx._connectips_verify_and_process()
            tx._connectips_verify_and_process()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_out_of_order_status_does_not_revert_done(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()):
            tx._connectips_verify_and_process()
        tx._process("connectips", self._validation_data("FAILED"))
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
        with self._mock_validation_api(self._validation_data()) as mock:
            self.env[
                "payment.transaction"
            ]._connectips_cron_check_unsettled_transactions()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")
        self.assertEqual(recent_tx.state, "draft")
