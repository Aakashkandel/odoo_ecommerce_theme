# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hmac

from odoo import http
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class FonepayController(http.Controller):
    _return_url = "/payment/fonepay/return"

    @http.route(_return_url, type="http", auth="public", methods=["GET"])
    def fonepay_return_from_checkout(self, **data):
        """Process the redirection from Fonepay after a payment attempt.

        The DV of the redirection data is checked before anything else. Successful
        payments are then verified with Fonepay's server: the redirection alone never
        confirms a payment.

        :param dict data: The redirection data.
        :return: A redirection to the payment status page.
        """
        redirection_data = self._fonepay_extract_redirection_data(data)
        if redirection_data is not None:
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                ._search_by_reference("fonepay", redirection_data)
            )
            if tx_sudo and self._fonepay_has_valid_dv(redirection_data, tx_sudo):
                tx_sudo._fonepay_process_redirection(redirection_data)
        return request.redirect("/payment/status")

    @staticmethod
    def _fonepay_extract_redirection_data(data):
        """Extract the expected fields from the redirection data.

        :param dict data: The redirection data.
        :return: The expected fields, or None if the data are malformed.
        :rtype: dict|None
        """
        expected_fields = (*const.RESPONSE_SIGNED_FIELDS, "DV")
        redirection_data = {field: data.get(field) for field in expected_fields}
        if not all(
            isinstance(value, str) and len(value) <= const.MAX_RESPONSE_VALUE_LENGTH
            for value in redirection_data.values()
        ) or not (redirection_data["PRN"] and redirection_data["DV"]):
            _logger.warning(
                "Received Fonepay redirection with missing or malformed data."
            )
            return None
        return redirection_data

    @staticmethod
    def _fonepay_has_valid_dv(redirection_data, tx_sudo):
        """Check that the redirection data were hashed by Fonepay for the merchant.

        :param dict redirection_data: The redirection data.
        :param payment.transaction tx_sudo: The sudoed transaction referenced by the
                 data.
        :return: Whether the DV is valid.
        :rtype: bool
        """
        provider = tx_sudo.provider_id
        if redirection_data["PID"] != provider.fonepay_merchant_code:
            _logger.warning("Received Fonepay redirection for another merchant.")
            return False
        expected_dv = provider._fonepay_calculate_dv(
            redirection_data, const.RESPONSE_SIGNED_FIELDS
        )
        if not hmac.compare_digest(
            redirection_data["DV"].upper().encode(), expected_dv.encode()
        ):
            _logger.warning("Received Fonepay redirection with invalid DV.")
            return False
        return True
