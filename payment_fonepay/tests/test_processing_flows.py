# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from ..controllers.main import FonepayController
from .common import FonepayCommon


@tagged("post_install", "-at_install")
class TestProcessingFlows(FonepayCommon, PaymentHttpCommon):
    def _return(self, data):
        url = self._build_url(FonepayController._return_url)
        return self._make_http_get_request(url, params=data)

    def test_valid_redirection_is_verified_server_side(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            response = self._return(self._redirection_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_lowercase_dv_is_accepted(self):
        tx = self._create_transaction(flow="redirect")
        data = self._redirection_data()
        data["DV"] = data["DV"].lower()
        with self._mock_verification_api(self._verification_xml()):
            self._return(data)
        self.assertEqual(tx.state, "done")

    @mute_logger("odoo.addons.payment_fonepay.controllers.main")
    def test_invalid_dv_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            self._return(self._redirection_data(DV="A" * 128))
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_fonepay.controllers.main")
    def test_tampered_redirection_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            self._return(self._redirection_data(P_AMT="1.00"))
            self._return(
                self._redirection_data(ps="false", rc="cancel", RC="successful")
            )
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_fonepay.controllers.main")
    def test_other_merchant_is_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            self._return(self._redirection_data(PID="OTHERMERCHANT"))
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_fonepay.controllers.main")
    def test_malformed_redirections_are_rejected(self):
        tx = self._create_transaction(flow="redirect")
        with self._mock_verification_api(self._verification_xml()) as mock:
            for data in (
                {},
                {"PRN": self.reference},
                {**self._redirection_data(), "DV": ""},
                {**self._redirection_data(), "UID": "A" * 1000},
            ):
                response = self._return(data)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment.models.payment_transaction")
    def test_unknown_reference_is_ignored(self):
        with self._mock_verification_api(self._verification_xml()) as mock:
            response = self._return(self._redirection_data(PRN="UNKNOWN"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)

    def test_replayed_redirection_is_harmless(self):
        tx = self._create_transaction(flow="redirect")
        data = self._redirection_data()
        with self._mock_verification_api(self._verification_xml()) as mock:
            self._return(data)
            self._return(data)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")
