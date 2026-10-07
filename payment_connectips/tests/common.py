# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import datetime
import json
from contextlib import contextmanager
from unittest.mock import patch

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from odoo.addons.payment.tests.common import PaymentCommon

REQUESTS_PATH = "odoo.addons.payment.models.payment_provider.requests.request"

# Throwaway values generated for the tests; they are not connectIPS credentials.
TEST_PFX_PASSWORD = "dummy-pfx-password"
TEST_BASE_URL = "https://connectips-uat.example.test"


def generate_test_pfx(password=TEST_PFX_PASSWORD):
    """Generate a throwaway PKCS#12 file holding a self-signed RSA key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CREDITOR-TEST")])
    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    pfx_data = pkcs12.serialize_key_and_certificates(
        b"creditor",
        private_key,
        certificate,
        None,
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption(),
    )
    return private_key, pfx_data


class ConnectipsCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_npr = cls._enable_currency("NPR")
        cls.private_key, pfx_data = generate_test_pfx()
        cls.connectips = cls._prepare_provider(
            "connectips",
            update_values={
                "connectips_merchant_id": "550",
                "connectips_app_id": "MER-550-APP-1",
                "connectips_app_name": "Odoo Test",
                "connectips_app_password": "dummy-api-password",
                "connectips_certificate": base64.b64encode(pfx_data),
                "connectips_certificate_password": TEST_PFX_PASSWORD,
                "connectips_test_base_url": TEST_BASE_URL,
            },
        )
        cls.provider = cls.connectips
        cls.payment_method = cls.env.ref("payment_connectips.payment_method_connectips")
        cls.payment_method_id = cls.payment_method.id
        cls.currency = cls.currency_npr
        cls.amount = 500.0
        cls.reference = "S00042-1"

    def _validation_data(self, status="SUCCESS", **overrides):
        status_descriptions = {
            "SUCCESS": "TRANSACTION SUCCESSFUL",
            "FAILED": "TRANSACTION UNSUCCESSFUL",
            "ERROR": "TRANSACTION NOT FOUND",
        }
        data = {
            "merchantId": 550,
            "appId": "MER-550-APP-1",
            "referenceId": self.reference,
            "txnAmt": 50000,
            "token": None,
            "status": status,
            "statusDesc": status_descriptions.get(status, ""),
        }
        data.update(overrides)
        return data

    @staticmethod
    def _mock_response(json_data, status_code=200):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(json_data).encode()
        response.url = TEST_BASE_URL
        return response

    @contextmanager
    def _mock_validation_api(self, json_data=None, side_effect=None):
        """Mock connectIPS's validation API and yield the mock."""
        kwargs = (
            {"side_effect": side_effect}
            if side_effect
            else {"return_value": self._mock_response(json_data)}
        )
        with patch(REQUESTS_PATH, **kwargs) as mock:
            yield mock
