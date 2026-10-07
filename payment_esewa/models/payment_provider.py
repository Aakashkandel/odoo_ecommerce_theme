# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import hmac

from odoo import fields, models
from odoo.exceptions import ValidationError

from .. import const


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("esewa", "eSewa")], ondelete={"esewa": "set default"}
    )
    esewa_product_code = fields.Char(
        string="eSewa Merchant Code",
        help="The merchant code (product_code) issued by eSewa.",
        required_if_provider="esewa",
        copy=False,
    )
    esewa_secret_key = fields.Char(
        string="eSewa Secret Key",
        help="The secret key issued by eSewa to sign payment requests and responses.",
        required_if_provider="esewa",
        copy=False,
        groups="base.group_system",
    )

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "esewa":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        self.ensure_one()
        if self.code != "esewa":
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === BUSINESS METHODS === #

    def _esewa_get_environment_url(self, urls):
        """Return the URL of the provider state, never falling back on another one.

        :param dict urls: The URLs, indexed by provider state.
        :return: The URL of the environment matching the provider state.
        :rtype: str
        :raise ValidationError: If the provider is disabled.
        """
        self.ensure_one()
        if self.state not in urls:
            raise ValidationError(self.env._("The eSewa payment provider is disabled."))
        return urls[self.state]

    def _esewa_calculate_signature(self, data, signed_fields):
        """Compute the signature of the given data as specified by eSewa.

        The signed message is the comma-separated list of `<field>=<value>` pairs, in
        the order of `signed_fields`, hashed with HMAC-SHA256 using the secret key and
        encoded in base64.

        :param dict data: The data to sign. Values are used as-is, as strings.
        :param iterable signed_fields: The names of the fields to sign, in order.
        :return: The base64-encoded signature.
        :rtype: str
        """
        self.ensure_one()
        message = ",".join(f"{field}={data[field]}" for field in signed_fields)
        digest = hmac.new(
            self.sudo().esewa_secret_key.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode()

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL."""
        if self.code != "esewa":
            return super()._build_request_url(endpoint, **kwargs)
        return self._esewa_get_environment_url(const.STATUS_CHECK_URLS)

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        """Override of `payment` to build the request headers."""
        if self.code != "esewa":
            return super()._build_request_headers(method, endpoint, payload, **kwargs)
        return {"Accept": "application/json"}
