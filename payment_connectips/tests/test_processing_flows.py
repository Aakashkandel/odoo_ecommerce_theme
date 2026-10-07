# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from ..controllers.main import ConnectipsController
from .common import ConnectipsCommon


@tagged("post_install", "-at_install")
class TestProcessingFlows(ConnectipsCommon, PaymentHttpCommon):
    def _return(self, route=ConnectipsController._return_url, **params):
        params = {"TXNID": self.reference, **params}
        return self._make_http_get_request(self._build_url(route), params=params)

    def test_success_redirection_is_validated_server_side(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()) as mock:
            response = self._return()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_success_redirection_alone_never_confirms_payment(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data("FAILED")):
            self._return()
        self.assertEqual(tx.state, "error")

    def test_failure_redirection_is_validated_server_side(self):
        """
        The failure URL cannot fail a payment that connectIPS reports as successful.
        """
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()):
            self._return(route=ConnectipsController._failure_url)
        self.assertEqual(tx.state, "done")

    def test_post_redirection_is_supported(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()):
            self._make_http_post_request(
                self._build_url(ConnectipsController._return_url),
                data={"TXNID": self.reference},
            )
        self.assertEqual(tx.state, "done")

    @mute_logger("odoo.addons.payment_connectips.controllers.main")
    def test_malformed_redirections_are_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()) as mock:
            for txnid in ("", "S00042-1,TXNAMT=1", "A" * 21, "' OR 1=1 --"):
                response = self._return(TXNID=txnid)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment.models.payment_transaction")
    def test_unknown_reference_is_ignored(self):
        with self._mock_validation_api(self._validation_data()) as mock:
            response = self._return(TXNID="UNKNOWN-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)

    def test_replayed_redirection_is_harmless(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_validation_api(self._validation_data()) as mock:
            self._return()
            self._return()
            self._return(route=ConnectipsController._failure_url)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")
