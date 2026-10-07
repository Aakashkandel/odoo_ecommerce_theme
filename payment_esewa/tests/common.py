# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import json
from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.addons.payment.tests.common import PaymentCommon

REQUESTS_PATH = "odoo.addons.payment.models.payment_provider.requests.request"

# The public sandbox values published in the eSewa ePay v2 documentation. These are not
# merchant secrets: https://developer.esewa.com.np/pages/Epay
SANDBOX_PRODUCT_CODE = "EPAYTEST"
SANDBOX_SECRET_KEY = "8gBm/:&EnhH.1/q"


class EsewaCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_npr = cls._enable_currency("NPR")
        cls.esewa = cls._prepare_provider(
            "esewa",
            update_values={
                "esewa_product_code": SANDBOX_PRODUCT_CODE,
                "esewa_secret_key": SANDBOX_SECRET_KEY,
            },
        )
        cls.provider = cls.esewa
        cls.payment_method = cls.env.ref("payment_esewa.payment_method_esewa")
        cls.payment_method_id = cls.payment_method.id
        cls.currency = cls.currency_npr
        cls.amount = 1000.0
        cls.reference = "S00042-1"

    def _status_data(self, status="COMPLETE", **overrides):
        """Return status check API data for the default transaction."""
        data = {
            "product_code": SANDBOX_PRODUCT_CODE,
            "transaction_uuid": self.reference,
            "total_amount": self.amount,
            "status": status,
            "ref_id": "0001TS9" if status != "NOT_FOUND" else None,
        }
        data.update(overrides)
        return data

    def _redirect_data(self, **overrides):
        """
        Return the base64-encoded, signed redirection data for the default transaction.
        """
        data = {
            "transaction_code": "000AWEO",
            "status": "COMPLETE",
            "total_amount": "1000.0",
            "transaction_uuid": self.reference,
            "product_code": SANDBOX_PRODUCT_CODE,
            "signed_field_names": (
                "transaction_code,status,total_amount,transaction_uuid,product_code,"
                "signed_field_names"
            ),
        }
        data["signature"] = self.esewa._esewa_calculate_signature(
            data, data["signed_field_names"].split(",")
        )
        data.update(overrides)
        # eSewa sends the amount as a JSON number.
        raw = json.dumps(data).replace(
            '"total_amount": "1000.0"', '"total_amount": 1000.0'
        )
        return base64.b64encode(raw.encode()).decode()

    @staticmethod
    def _mock_response(json_data, status_code=200):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(json_data).encode()
        response.url = "https://rc.esewa.com.np/api/epay/transaction/status/"
        return response

    @contextmanager
    def _mock_status_api(self, json_data=None, side_effect=None):
        """Mock the eSewa status check API and yield the mock."""
        kwargs = (
            {"side_effect": side_effect}
            if side_effect
            else {"return_value": self._mock_response(json_data)}
        )
        with patch(REQUESTS_PATH, **kwargs) as mock:
            yield mock
