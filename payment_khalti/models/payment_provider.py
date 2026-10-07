# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from urllib.parse import urlsplit

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import urls

from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("khalti", "Khalti")], ondelete={"khalti": "set default"}
    )
    khalti_secret_key = fields.Char(
        string="Khalti Live Secret Key",
        help="The live secret key of the merchant account. Use the key of the sandbox "
        "merchant"
        " account (test-admin.khalti.com) in test mode and the key of the production "
        "merchant"
        " account (admin.khalti.com) when enabled.",
        required_if_provider="khalti",
        copy=False,
        groups="base.group_system",
    )

    # === COMPUTE METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "khalti":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    # === CRUD METHODS === #

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        self.ensure_one()
        if self.code != "khalti":
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === BUSINESS METHODS === #

    def _khalti_is_valid_payment_url(self, payment_url):
        """Check that the payment URL is an HTTPS URL of Khalti's domain.

        :param str payment_url: The payment URL to check.
        :return: Whether the payment URL is valid.
        :rtype: bool
        """
        if not isinstance(payment_url, str):
            return False
        parsed_url = urlsplit(payment_url)
        hostname = parsed_url.hostname or ""
        return parsed_url.scheme == "https" and (
            hostname == const.PAYMENT_URL_DOMAIN
            or hostname.endswith(f".{const.PAYMENT_URL_DOMAIN}")
        )

    def _khalti_lookup(self, pidx, reference=None):
        """Fetch the status of a payment from Khalti's lookup API.

        Khalti answers with HTTP 400 for expired and canceled payments, so the response
        body is parsed for both HTTP 200 and 400 rather than through the generic request
        helper.

        :param str pidx: The payment identifier returned by Khalti at initiation.
        :param str reference: The reference of the transaction, for logging purposes.
        :return: The payment data returned by Khalti.
        :rtype: dict
        :raise ValidationError: If the request fails or the response cannot be
                 interpreted.
        """
        self.ensure_one()
        url = self._build_request_url(const.LOOKUP_ENDPOINT)
        payload = {"pidx": pidx}
        self._log_request("POST", url, payload, reference=reference)
        try:
            response = requests.request(
                "POST",
                url,
                json=payload,
                headers=self._build_request_headers(
                    "POST", const.LOOKUP_ENDPOINT, payload
                ),
                timeout=10,
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:
            raise ValidationError(
                self.env._(
                    "Could not establish the connection to the payment provider."
                )
            ) from error
        if response.status_code == 400:
            # Expected answer for expired and canceled payments: not worth an error log.
            _logger.info(
                "Received HTTP 400 lookup response from Khalti for transaction %s:\n%s",
                reference,
                response.text,
            )
        else:
            self._log_response(response, reference=reference)

        if response.status_code in (200, 400):
            try:
                payment_data = response.json()
            except ValueError:
                payment_data = None
            if isinstance(payment_data, dict) and isinstance(
                payment_data.get("status"), str
            ):
                return payment_data
        raise ValidationError(
            self.env._(
                "Khalti could not look up the payment (HTTP %s).", response.status_code
            )
        )

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL.

        The URL always matches the provider state: there is no fallback on another
        environment.
        """
        if self.code != "khalti":
            return super()._build_request_url(endpoint, **kwargs)
        if self.state not in const.API_URLS:
            raise ValidationError(
                self.env._("The Khalti payment provider is disabled.")
            )
        return urls.urljoin(const.API_URLS[self.state], endpoint)

    def _build_request_headers(self, method, endpoint, payload, **kwargs):
        """Override of `payment` to build the request headers."""
        if self.code != "khalti":
            return super()._build_request_headers(method, endpoint, payload, **kwargs)
        return {
            "Authorization": f"Key {self.sudo().khalti_secret_key}",
            "Content-Type": "application/json",
        }

    def _parse_response_error(self, response):
        """Override of `payment` to parse the error messages returned by Khalti."""
        if self.code != "khalti":
            return super()._parse_response_error(response)
        content = response.json()
        if isinstance(content, dict):
            return content.get("detail") or content.get("error_key") or str(content)
        return str(content)
