# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.addons.payment.tests.common import PaymentCommon

REQUESTS_PATH = "odoo.addons.payment.models.payment_provider.requests.request"


class KhaltiCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_npr = cls._enable_currency("NPR")
        cls.khalti = cls._prepare_provider(
            "khalti", update_values={"khalti_secret_key": "dummy-test-secret-key"}
        )
        cls.provider = cls.khalti
        cls.payment_method = cls.env.ref("payment_khalti.payment_method_khalti")
        cls.payment_method_id = cls.payment_method.id
        cls.currency = cls.currency_npr
        cls.amount = 1000.0
        cls.reference = "S00042-1"
        cls.pidx = "bZQLD9wRVWo4CdESSfuSsB"

    def _create_initiated_transaction(self, **values):
        return self._create_transaction(
            flow="redirect", provider_reference=self.pidx, **values
        )

    def _lookup_data(self, status="Completed", **overrides):
        data = {
            "pidx": self.pidx,
            "total_amount": 100000,
            "status": status,
            "transaction_id": "GFq9PFS7b2iYvL8Lir9oXe"
            if status == "Completed"
            else None,
            "fee": 0,
            "refunded": False,
        }
        data.update(overrides)
        return data

    @staticmethod
    def _mock_response(json_data, status_code=200):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(json_data).encode()
        response.url = "https://dev.khalti.com/api/v2/"
        return response

    @contextmanager
    def _mock_khalti_api(self, json_data=None, status_code=200, side_effect=None):
        """Mock Khalti's API and yield the mock."""
        kwargs = (
            {"side_effect": side_effect}
            if side_effect
            else {"return_value": self._mock_response(json_data, status_code)}
        )
        with patch(REQUESTS_PATH, **kwargs) as mock:
            yield mock
