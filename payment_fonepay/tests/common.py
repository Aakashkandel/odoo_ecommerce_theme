# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.addons.payment.tests.common import PaymentCommon

from .. import const

REQUESTS_PATH = "odoo.addons.payment.models.payment_provider.requests.request"

# Throwaway values for the tests; they are not Fonepay credentials.
TEST_BASE_URL = "https://fonepay-test.example.test"


class FonepayCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_npr = cls._enable_currency("NPR")
        cls.fonepay = cls._prepare_provider(
            "fonepay",
            update_values={
                "fonepay_merchant_code": "TESTMERCHANT",
                "fonepay_secret_key": "dummy-test-secret-key",
                "fonepay_test_base_url": TEST_BASE_URL,
            },
        )
        cls.provider = cls.fonepay
        cls.payment_method = cls.env.ref("payment_fonepay.payment_method_fonepay")
        cls.payment_method_id = cls.payment_method.id
        cls.currency = cls.currency_npr
        cls.amount = 1000.0
        cls.reference = "S00042-1"

    def _redirection_data(self, ps="true", rc="successful", **overrides):
        data = {
            "PRN": self.reference,
            "PID": "TESTMERCHANT",
            "PS": ps,
            "RC": rc,
            "UID": "1234567" if ps == "true" else "",
            "BC": "NIBLNPKT" if ps == "true" else "",
            "INI": "9800000000",
            "P_AMT": "1000.00",
            "R_AMT": "0",
        }
        data["DV"] = self.fonepay._fonepay_calculate_dv(
            data, const.RESPONSE_SIGNED_FIELDS
        )
        data.update(overrides)
        return data

    @staticmethod
    def _verification_xml(
        success="true", response_code="successful", amount="1000.0", uid=None
    ):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            "<response>"
            f"<amount>{amount}</amount>"
            "<bankCode>NIBLNPKT</bankCode>"
            "<initiator>9800000000</initiator>"
            "<message>RES000</message>"
            f"<response_code>{response_code}</response_code>"
            "<statusCode>0</statusCode>"
            f"<success>{success}</success>"
            f"<txnAmount>{amount}</txnAmount>"
            f"<uniqueId>{uid or '1234567'}</uniqueId>"
            "</response>"
        )

    @staticmethod
    def _mock_response(content, status_code=200):
        response = requests.Response()
        response.status_code = status_code
        response._content = content.encode()
        response.url = TEST_BASE_URL
        return response

    @contextmanager
    def _mock_verification_api(self, content=None, side_effect=None):
        """Mock Fonepay's verification API and yield the mock."""
        kwargs = (
            {"side_effect": side_effect}
            if side_effect
            else {"return_value": self._mock_response(content)}
        )
        with patch(REQUESTS_PATH, **kwargs) as mock:
            yield mock
