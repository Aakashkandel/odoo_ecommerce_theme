# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hashlib
import hmac
from urllib.parse import urlsplit

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .. import const


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("fonepay", "Fonepay")], ondelete={"fonepay": "set default"}
    )
    fonepay_merchant_code = fields.Char(
        help="The merchant code (PID) issued by Fonepay or the acquiring bank.",
        required_if_provider="fonepay",
        copy=False,
    )
    fonepay_secret_key = fields.Char(
        help="The secret key issued by Fonepay or the acquiring bank to hash requests "
        "and"
        " responses.",
        required_if_provider="fonepay",
        copy=False,
        groups="base.group_system",
    )
    fonepay_test_base_url = fields.Char(
        string="Fonepay Test Base URL",
        help="The base URL of the Fonepay test environment, as given in the merchant "
        "integration"
        " specification. Only used in test mode.",
        copy=False,
    )
    fonepay_production_base_url = fields.Char(
        string="Fonepay Production Base URL",
        help="The base URL of the Fonepay live environment, as given in the merchant "
        "integration"
        " specification. Only used when the provider is enabled.",
        copy=False,
    )

    # === CONSTRAINT METHODS === #

    @api.constrains("fonepay_test_base_url", "fonepay_production_base_url")
    def _check_fonepay_base_urls(self):
        for provider in self:
            for base_url in (
                provider.fonepay_test_base_url,
                provider.fonepay_production_base_url,
            ):
                if base_url and not self._fonepay_is_valid_base_url(base_url):
                    raise ValidationError(
                        self.env._(
                            "The Fonepay base URLs must be HTTPS URLs without path or "
                            "query."
                        )
                    )

    @staticmethod
    def _fonepay_is_valid_base_url(base_url):
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
        for provider in self.filtered(lambda p: p.code == "fonepay"):
            if provider.state == "test" and not provider.fonepay_test_base_url:
                raise ValidationError(
                    self.env._("The Fonepay Test Base URL must be filled.")
                )
            if provider.state == "enabled" and not provider.fonepay_production_base_url:
                raise ValidationError(
                    self.env._("The Fonepay Production Base URL must be filled.")
                )
        return res

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "fonepay":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        self.ensure_one()
        if self.code != "fonepay":
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === BUSINESS METHODS === #

    def _fonepay_get_url(self, path):
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
            base_url = self.fonepay_test_base_url
        elif self.state == "enabled":
            base_url = self.fonepay_production_base_url
        else:
            raise ValidationError(
                self.env._("The Fonepay payment provider is disabled.")
            )
        if not base_url or not self._fonepay_is_valid_base_url(base_url):
            raise ValidationError(self.env._("The Fonepay base URL is not configured."))
        return base_url.rstrip("/") + path

    def _fonepay_calculate_dv(self, data, signed_fields):
        """Compute the secure data validation code (DV) of the given data.

        The hashed message is the comma-separated list of the values of `signed_fields`,
        in order, hashed with HMAC-SHA512 using the secret key and encoded in uppercase
        hexadecimal.

        :param dict data: The data to hash. Values are used as-is, as strings.
        :param tuple signed_fields: The names of the fields to hash, in order.
        :return: The DV.
        :rtype: str
        """
        self.ensure_one()
        message = ",".join(str(data[field]) for field in signed_fields)
        return (
            hmac.new(
                self.sudo().fonepay_secret_key.encode(),
                msg=message.encode(),
                digestmod=hashlib.sha512,
            )
            .hexdigest()
            .upper()
        )

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL."""
        if self.code != "fonepay":
            return super()._build_request_url(endpoint, **kwargs)
        return self._fonepay_get_url(endpoint)

    def _parse_response_content(self, response, **kwargs):
        """
        Override of `payment` to parse the XML content of the verification response.
        """
        if self.code != "fonepay":
            return super()._parse_response_content(response, **kwargs)
        parser = etree.XMLParser(
            resolve_entities=False, no_network=True, huge_tree=False
        )
        try:
            root = etree.fromstring(response.content, parser=parser)
        except (etree.XMLSyntaxError, ValueError) as error:
            raise ValidationError(
                self.env._("Fonepay returned a malformed response.")
            ) from error
        return {
            element.tag: (element.text or "").strip()
            for element in root
            if isinstance(element.tag, str)
        }
