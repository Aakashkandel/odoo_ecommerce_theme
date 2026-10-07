# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import binascii
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .. import const


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("connectips", "connectIPS")],
        ondelete={"connectips": "set default"},
    )
    connectips_merchant_id = fields.Char(
        string="connectIPS Merchant ID",
        help="The numeric merchant ID issued by NCHL.",
        required_if_provider="connectips",
        copy=False,
    )
    connectips_app_id = fields.Char(
        string="connectIPS App ID",
        help="The application ID issued by NCHL. Also used as the API user name.",
        required_if_provider="connectips",
        copy=False,
    )
    connectips_app_name = fields.Char(
        string="connectIPS App Name",
        help="The application name registered with NCHL.",
        required_if_provider="connectips",
        copy=False,
    )
    connectips_app_password = fields.Char(
        string="connectIPS API Password",
        help="The password issued by NCHL for the validation API.",
        required_if_provider="connectips",
        copy=False,
        groups="base.group_system",
    )
    connectips_certificate = fields.Binary(
        string="connectIPS Certificate (PFX)",
        help="The PKCS#12 (.pfx) file holding the private key used to sign requests.",
        required_if_provider="connectips",
        attachment=True,
        copy=False,
        groups="base.group_system",
    )
    connectips_certificate_password = fields.Char(
        string="connectIPS Certificate Password",
        help="The password protecting the PFX file, if any.",
        copy=False,
        groups="base.group_system",
    )
    connectips_test_base_url = fields.Char(
        string="connectIPS Test Base URL",
        help="The base URL of the connectIPS test (UAT) environment, as provided by "
        "NCHL."
        " Only used in test mode.",
        copy=False,
    )
    connectips_production_base_url = fields.Char(
        string="connectIPS Production Base URL",
        help="The base URL of the connectIPS live environment, as provided by NCHL. "
        "Only used"
        " when the provider is enabled.",
        copy=False,
    )

    # === CONSTRAINT METHODS === #

    @api.constrains("connectips_merchant_id")
    def _check_connectips_merchant_id(self):
        for provider in self.filtered("connectips_merchant_id"):
            if not provider.connectips_merchant_id.isdigit():
                raise ValidationError(
                    self.env._("The connectIPS Merchant ID must be a number.")
                )

    @api.constrains("connectips_app_id", "connectips_app_name")
    def _check_connectips_app_lengths(self):
        for provider in self:
            for field_name, key in (
                ("connectips_app_id", "APPID"),
                ("connectips_app_name", "APPNAME"),
            ):
                if len(provider[field_name] or "") > const.FIELD_MAX_LENGTHS[key]:
                    raise ValidationError(
                        self.env._(
                            "The connectIPS %(field)s cannot exceed %(length)s "
                            "characters.",
                            field=self._fields[field_name].string,
                            length=const.FIELD_MAX_LENGTHS[key],
                        )
                    )

    @api.constrains("connectips_test_base_url", "connectips_production_base_url")
    def _check_connectips_base_urls(self):
        for provider in self:
            for base_url in (
                provider.connectips_test_base_url,
                provider.connectips_production_base_url,
            ):
                if base_url and not self._connectips_is_valid_base_url(base_url):
                    raise ValidationError(
                        self.env._(
                            "The connectIPS base URLs must be HTTPS URLs without path "
                            "or query."
                        )
                    )

    @api.constrains("connectips_certificate", "connectips_certificate_password")
    def _check_connectips_certificate(self):
        for provider in self.sudo().filtered("connectips_certificate"):
            provider._connectips_load_private_key()

    @staticmethod
    def _connectips_is_valid_base_url(base_url):
        parsed_url = urlsplit(base_url)
        return (
            parsed_url.scheme == "https"
            and bool(parsed_url.hostname)
            and parsed_url.path in ("", "/")
            and not parsed_url.query
            and not parsed_url.fragment
        )

    def _check_required_if_provider(self):
        """
        Override of `payment` to require the base URL of the environment of the state.
        """
        res = super()._check_required_if_provider()
        for provider in self.filtered(lambda p: p.code == "connectips"):
            if provider.state == "test" and not provider.connectips_test_base_url:
                raise ValidationError(
                    self.env._("The connectIPS Test Base URL must be filled.")
                )
            if (
                provider.state == "enabled"
                and not provider.connectips_production_base_url
            ):
                raise ValidationError(
                    self.env._("The connectIPS Production Base URL must be filled.")
                )
        return res

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "connectips":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        self.ensure_one()
        if self.code != "connectips":
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === BUSINESS METHODS === #

    def _connectips_get_url(self, path):
        """Return the URL of the given path in the environment of the provider state.

        There is no fallback on another environment: the base URL configured for the
        state is always used.

        :param str path: The path of the endpoint.
        :return: The URL of the endpoint.
        :rtype: str
        :raise ValidationError: If the provider is disabled or its base URL is not
                 configured.
        """
        self.ensure_one()
        if self.state == "test":
            base_url = self.connectips_test_base_url
        elif self.state == "enabled":
            base_url = self.connectips_production_base_url
        else:
            raise ValidationError(
                self.env._("The connectIPS payment provider is disabled.")
            )
        if not base_url or not self._connectips_is_valid_base_url(base_url):
            raise ValidationError(
                self.env._("The connectIPS base URL is not configured.")
            )
        return base_url.rstrip("/") + path

    def _connectips_load_private_key(self):
        """Load the RSA private key from the PFX file of the provider.

        :return: The private key.
        :rtype: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey
        :raise ValidationError: If the file cannot be read or holds no RSA private key.
        """
        self.ensure_one()
        provider_sudo = self.sudo()
        password = provider_sudo.connectips_certificate_password
        try:
            pfx_data = base64.b64decode(provider_sudo.connectips_certificate or b"")
            private_key, _certificate, _additional_certificates = (
                pkcs12.load_key_and_certificates(
                    pfx_data, password.encode() if password else None
                )
            )
        except (binascii.Error, ValueError, TypeError) as error:
            # The error message is not forwarded as it could leak details about the
            # secrets.
            raise ValidationError(
                self.env._(
                    "The connectIPS certificate could not be read. Check the file and "
                    "password."
                )
            ) from error
        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise ValidationError(
                self.env._("The connectIPS certificate holds no RSA private key.")
            )
        return private_key

    def _connectips_calculate_token(self, data, signed_fields):
        """Compute the token (digital signature) of the data as specified by connectIPS.

        The signed message is the comma-separated list of `<FIELD>=<value>` pairs, in
        the order of `signed_fields`, signed with SHA256withRSA using the private key of
        the PFX file and encoded in base64. The payment request's message also ends with
        the literal `TOKEN=TOKEN`.

        :param dict data: The data to sign. Values are used as-is, as strings.
        :param tuple signed_fields: The names of the fields to sign, in order.
        :return: The base64-encoded token.
        :rtype: str
        """
        self.ensure_one()
        message = ",".join(f"{field}={data[field]}" for field in signed_fields)
        if signed_fields == const.LOGIN_PAGE_SIGNED_FIELDS:
            message += ",TOKEN=TOKEN"
        signature = self._connectips_load_private_key().sign(
            message.encode(), padding.PKCS1v15(), hashes.SHA256()
        )
        return base64.b64encode(signature).decode()

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL."""
        if self.code != "connectips":
            return super()._build_request_url(endpoint, **kwargs)
        return self._connectips_get_url(endpoint)

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        """Override of `payment` to build the request headers."""
        if self.code != "connectips":
            return super()._build_request_headers(method, endpoint, payload, **kwargs)
        return {"Content-Type": "application/json", "Accept": "application/json"}

    def _build_request_auth(self, **kwargs):
        """
        Override of `payment` to authenticate with the App ID and the API password.
        """
        if self.code != "connectips":
            return super()._build_request_auth(**kwargs)
        return (self.connectips_app_id, self.sudo().connectips_app_password)
