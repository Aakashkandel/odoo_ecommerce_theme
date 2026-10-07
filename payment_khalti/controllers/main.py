# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import hmac
import re

from odoo import http
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class KhaltiController(http.Controller):
    _return_url = "/payment/khalti/return"

    @http.route(_return_url, type="http", auth="public", methods=["GET"])
    def khalti_return_from_checkout(self, pidx=None, purchase_order_id=None, **kwargs):
        """Process the redirection from Khalti after a payment attempt.

        Khalti appends the payment details to the URL, but only the payment identifier
        and the reference are used, to find the transaction. Its status is then fetched
        from Khalti's lookup API, as required by Khalti: the redirection data never
        confirm a payment.

        :param str pidx: The payment identifier.
        :param str purchase_order_id: The reference of the transaction.
        :return: A redirection to the payment status page.
        """
        if (
            not isinstance(pidx, str)
            or not re.match(const.PIDX_PATTERN, pidx)
            or not isinstance(purchase_order_id, str)
        ):
            _logger.warning(
                "Received Khalti redirection with missing or malformed data."
            )
            return request.redirect("/payment/status")

        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            ._search_by_reference("khalti", {"purchase_order_id": purchase_order_id})
        )
        if (
            tx_sudo
            and tx_sudo.provider_reference
            and hmac.compare_digest(pidx.encode(), tx_sudo.provider_reference.encode())
        ):
            tx_sudo._khalti_verify_and_process()
        elif tx_sudo:
            _logger.warning(
                "Received Khalti redirection for transaction %s with a mismatching "
                "payment"
                " identifier.",
                tx_sudo.reference,
            )
        return request.redirect("/payment/status")
