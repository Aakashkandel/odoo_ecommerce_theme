# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import binascii
import hmac
import json

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class EsewaController(http.Controller):
    _return_url = "/payment/esewa/return"
    _failure_url = "/payment/esewa/failure"

    @http.route(_return_url, type="http", auth="public", methods=["GET"])
    def esewa_return_from_checkout(self, data=None, **kwargs):
        """Process the redirection from eSewa after a successful payment.

        eSewa appends a base64-encoded, signed JSON to the URL. Its signature is checked
        to find the transaction, whose status is then fetched from eSewa's server before
        being processed: the redirection data alone never confirm a payment.

        :param str data: The base64-encoded payment data.
        :return: A redirection to the payment status page.
        """
        payment_data = self._esewa_decode_payment_data(data)
        if payment_data is not None:
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                ._search_by_reference("esewa", payment_data)
            )
            if tx_sudo and self._esewa_has_valid_signature(payment_data, tx_sudo):
                tx_sudo._esewa_verify_and_process()
        return request.redirect("/payment/status")

    @http.route(_failure_url, type="http", auth="public", methods=["GET"])
    def esewa_return_from_failure(self, **kwargs):
        """Process the redirection from eSewa after a failed or abandoned payment.

        eSewa sends no payment data to this URL; the status of the transaction monitored
        in the customer's session is fetched from eSewa's server instead.

        :return: A redirection to the payment status page.
        """
        monitored_tx = PaymentPostProcessing()._get_monitored_transaction()
        if monitored_tx and monitored_tx.provider_code == "esewa":
            monitored_tx.sudo()._esewa_verify_and_process()
        return request.redirect("/payment/status")

    @staticmethod
    def _esewa_decode_payment_data(data):
        """Decode the payment data sent by eSewa.

        Numbers are kept as their original string representation so that the signature
        can be verified against the exact values that eSewa signed.

        :param str data: The base64-encoded JSON payment data.
        :return: The decoded payment data, or None if it is malformed.
        :rtype: dict|None
        """
        if not data or len(data) > const.MAX_RESPONSE_PAYLOAD_LENGTH:
            _logger.warning(
                "Received eSewa redirection with missing or oversized payment data."
            )
            return None
        try:
            decoded_data = base64.b64decode(
                data + "=" * (-len(data) % 4), validate=True
            )
            payment_data = json.loads(decoded_data, parse_float=str, parse_int=str)
        except (binascii.Error, ValueError):
            _logger.warning("Received eSewa redirection with malformed payment data.")
            return None
        if not isinstance(payment_data, dict) or not all(
            isinstance(payment_data.get(field), str)
            for field in const.RESPONSE_SIGNED_FIELDS
        ):
            _logger.warning("Received eSewa redirection with incomplete payment data.")
            return None
        return payment_data

    @staticmethod
    def _esewa_has_valid_signature(payment_data, tx_sudo):
        """Check that the payment data were signed by eSewa for the merchant.

        Only the documented list of signed fields is accepted, so that a forged payload
        cannot choose which fields are covered by the signature.

        :param dict payment_data: The decoded payment data.
        :param payment.transaction tx_sudo: The sudoed transaction referenced by the
                 data.
        :return: Whether the signature is valid.
        :rtype: bool
        """
        received_signature = payment_data.get("signature")
        if not isinstance(received_signature, str) or not received_signature:
            _logger.warning("Received eSewa payment data with missing signature.")
            return False
        if payment_data["signed_field_names"] != ",".join(const.RESPONSE_SIGNED_FIELDS):
            _logger.warning(
                "Received eSewa payment data with unexpected signed fields."
            )
            return False
        if payment_data["product_code"] != tx_sudo.provider_id.esewa_product_code:
            _logger.warning("Received eSewa payment data for another merchant.")
            return False

        expected_signature = tx_sudo.provider_id._esewa_calculate_signature(
            payment_data, const.RESPONSE_SIGNED_FIELDS
        )
        if not hmac.compare_digest(
            received_signature.encode(), expected_signature.encode()
        ):
            _logger.warning("Received eSewa payment data with invalid signature.")
            return False
        return True
