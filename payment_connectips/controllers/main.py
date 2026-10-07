# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re

from odoo import http
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class ConnectipsController(http.Controller):
    # These URLs are registered with NCHL as the merchant's success and failure URLs.
    _return_url = "/payment/connectips/return"
    _failure_url = "/payment/connectips/failure"

    @http.route(
        [_return_url, _failure_url],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
    )
    def connectips_return_from_checkout(self, TXNID=None, **kwargs):  # noqa: N803
        """Process the redirection from connectIPS after a payment attempt.

        connectIPS only sends the TXNID, which is used to find the transaction. Its
        status is then fetched from connectIPS's validation API: the redirection never
        confirms a payment, and landing on the success or failure URL makes no
        difference.

        :param str TXNID: The reference of the transaction.
        :return: A redirection to the payment status page.
        """
        if not isinstance(TXNID, str) or not re.match(const.TXNID_PATTERN, TXNID):
            _logger.warning(
                "Received connectIPS redirection with missing or malformed TXNID."
            )
            return request.redirect("/payment/status")

        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            ._search_by_reference("connectips", {"referenceId": TXNID})
        )
        if tx_sudo:
            tx_sudo._connectips_verify_and_process()
        return request.redirect("/payment/status")
