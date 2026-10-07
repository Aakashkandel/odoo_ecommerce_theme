# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import json

from odoo import http
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from ..controllers.main import EsewaController
from .common import EsewaCommon


@tagged("post_install", "-at_install")
class TestProcessingFlows(EsewaCommon, PaymentHttpCommon):
    def _return(self, data):
        url = self._build_url(EsewaController._return_url)
        return self._make_http_get_request(url, params={"data": data})

    def test_valid_redirection_is_verified_server_side(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            response = self._return(self._redirect_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_redirection_alone_never_confirms_payment(self):
        """
        A validly signed "COMPLETE" redirection is not trusted if eSewa's server
        disagrees.
        """
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data("PENDING")):
            self._return(self._redirect_data())
        self.assertEqual(tx.state, "pending")

    @mute_logger("odoo.addons.payment_esewa.controllers.main")
    def test_invalid_signature_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            self._return(self._redirect_data(signature="Zm9yZ2Vk"))
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_esewa.controllers.main")
    def test_tampered_payload_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            self._return(self._redirect_data(status="CANCELED"))  # Signed as COMPLETE.
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_esewa.controllers.main")
    def test_unexpected_signed_fields_are_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            self._return(self._redirect_data(signed_field_names="transaction_uuid"))
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_esewa.controllers.main")
    def test_malformed_payloads_are_rejected(self):
        tx = self._create_transaction(flow="redirect")
        malformed_payloads = [
            "",
            "not-base64!!",
            base64.b64encode(b"not json").decode(),
            base64.b64encode(json.dumps(["a", "list"]).encode()).decode(),
            base64.b64encode(
                json.dumps({"transaction_uuid": self.reference}).encode()
            ).decode(),
            "A" * 5000,
        ]
        with self._mock_status_api(self._status_data()) as mock:
            for payload in malformed_payloads:
                response = self._return(payload)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment.models.payment_transaction")
    def test_unknown_reference_is_ignored(self):
        with self._mock_status_api(self._status_data()) as mock:
            response = self._return(self._redirect_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)

    def test_replayed_redirection_is_harmless(self):
        tx = self._create_transaction(flow="redirect")
        data = self._redirect_data()
        with self._mock_status_api(self._status_data()) as mock:
            self._return(data)
            self._return(data)
            self._return(data)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_failure_redirection_checks_monitored_transaction(self):
        tx = self._create_transaction(flow="redirect")
        session = self.authenticate(None, None)
        session[PaymentPostProcessing.MONITORED_TX_ID_KEY] = tx.id
        http.root.session_store.save(session)
        with self._mock_status_api(self._status_data("CANCELED")) as mock:
            self.url_open(self._build_url(EsewaController._failure_url))
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "cancel")

    def test_failure_redirection_without_session_does_nothing(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_status_api(self._status_data()) as mock:
            response = self.url_open(self._build_url(EsewaController._failure_url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")
