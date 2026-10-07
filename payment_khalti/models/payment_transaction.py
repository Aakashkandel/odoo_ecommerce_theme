# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL, urls

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger

from .. import const
from ..controllers.main import KhaltiController

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator="-", **kwargs):
        """Override of `payment` to generate unique Khalti purchase order identifiers.

        Khalti requires the purchase order identifier to be unique for the merchant,
        including across databases. The prefix is therefore suffixed with the current date
        and time.
        """
        if provider_code == "khalti":
            if not prefix:
                prefix = self.sudo()._compute_reference_prefix(separator, **kwargs)
            timestamp = fields.Datetime.now().strftime(const.REFERENCE_DATE_FORMAT)
            prefix = f"{prefix or 'tx'}-{timestamp}"
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to initiate the payment with Khalti and return its URL.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        if self.provider_code != "khalti":
            return super()._get_specific_rendering_values(processing_values)

        if self.currency_id.name not in const.SUPPORTED_CURRENCIES:
            raise ValidationError(
                self.env._("Khalti only accepts payments in Nepalese Rupees (NPR).")
            )
        amount_paisa = payment_utils.to_minor_currency_units(
            self.amount, self.currency_id
        )
        if amount_paisa < const.MINIMUM_AMOUNT_PAISA:
            raise ValidationError(
                self.env._("Khalti only accepts payments of at least Rs. 10.")
            )

        base_url = self.provider_id.get_base_url()
        payload = {
            "return_url": urls.urljoin(base_url, KhaltiController._return_url),
            "website_url": base_url,
            "amount": amount_paisa,
            "purchase_order_id": self.reference,
            "purchase_order_name": self.reference,
        }
        initiation_data = self._send_api_request(
            "POST", const.INITIATE_ENDPOINT, json=payload
        )
        pidx = initiation_data.get("pidx")
        payment_url = initiation_data.get("payment_url")
        if not pidx or not self.provider_id._khalti_is_valid_payment_url(payment_url):
            _logger.error(
                "Received invalid Khalti initiation data for transaction %s.",
                self.reference,
            )
            raise ValidationError(
                self.env._("Khalti returned an invalid payment initiation response.")
            )
        self.provider_reference = pidx

        # The query string of a GET form's action is dropped by browsers: send it as
        # inputs.
        split_url = urlsplit(payment_url)
        return {
            "api_url": urlunsplit(split_url._replace(query="", fragment="")),
            "url_params": dict(parse_qsl(split_url.query)),
        }

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _khalti_lock_for_update(self):
        """Lock the transaction row until the end of the database transaction.

        Concurrent notifications for the same transaction are thus processed one after
        the other, and each one sees the state written by the previous one.

        :return: None
        """
        self.ensure_one()
        self.env.cr.execute(
            SQL(
                "SELECT id FROM %s WHERE id = %s FOR UPDATE",
                SQL.identifier(self._table),
                self.id,
            )
        )
        self.invalidate_recordset()

    def _khalti_verify_and_process(self):
        """Fetch the status of the transaction from Khalti's lookup API and process it.

        The lookup is made with the payment identifier stored at initiation, never with
        values received from the customer's browser. Transactions that already reached a
        final state are left untouched, which makes repeated notifications harmless.

        :return: None
        """
        self.ensure_one()
        self._khalti_lock_for_update()
        if self.state in ("done", "cancel"):
            _logger.info(
                "Ignored Khalti notification for transaction %s already in state %s.",
                self.reference,
                self.state,
            )
            return
        if not self.provider_reference:
            _logger.warning(
                "Khalti transaction %s was never initiated.", self.reference
            )
            return

        try:
            payment_data = self.provider_id._khalti_lookup(
                self.provider_reference, reference=self.reference
            )
        except ValidationError as error:
            # Leave the transaction as is: it will be checked again by the scheduled
            # action.
            _logger.warning(
                "Unable to look up the Khalti payment of transaction %s: %s",
                self.reference,
                error,
            )
            return

        if payment_data.get("pidx") != self.provider_reference:
            _logger.error(
                "Received Khalti lookup data for transaction %s with a mismatching "
                "payment"
                " identifier; ignored.",
                self.reference,
            )
            return
        self._process("khalti", payment_data)

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data."""
        if provider_code != "khalti":
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get("purchase_order_id")

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to extract the amount and currency from the payment data.
        """
        if self.provider_code != "khalti":
            return super()._extract_amount_data(payment_data)

        if payment_data.get("status") not in const.PAYMENT_STATUS_MAPPING["done"]:
            return None  # The amount is only checked to confirm a payment.

        amount_paisa = payment_data.get("total_amount")
        if not isinstance(amount_paisa, int) or isinstance(amount_paisa, bool):
            amount = None  # Makes `_validate_amount` reject the payment data.
        else:
            amount = payment_utils.to_major_currency_units(
                amount_paisa, self.currency_id
            )
        return {
            "amount": amount,
            # Khalti only processes NPR; the transaction's currency is checked at
            # rendering.
            "currency_code": const.SUPPORTED_CURRENCIES[0],
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != "khalti":
            return super()._apply_updates(payment_data)

        status = payment_data.get("status")
        if status in const.PAYMENT_STATUS_MAPPING["done"] and payment_data.get(
            "refunded"
        ):
            status = "Refunded"

        if status in const.PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING["cancel"]:
            self._set_canceled(
                state_message=self.env._("Khalti reported the payment as %s.", status)
            )
        elif status in const.PAYMENT_STATUS_MAPPING["refunded"]:
            # Refunds are made from the Khalti merchant portal and are not handled by
            # Odoo.
            _logger.warning(
                "Khalti reported transaction %s as refunded (%s).",
                self.reference,
                status,
            )
            self._set_error(
                self.env._("Khalti reported this payment as refunded (%s).", status)
            )
        else:
            _logger.warning(
                "Received invalid Khalti payment status (%s) for transaction %s.",
                status,
                self.reference,
            )
            self._set_error(
                self.env._("Received an unknown payment status from Khalti: %s", status)
            )

    # === BUSINESS METHODS - SCHEDULED ACTION === #

    @api.model
    def _khalti_cron_check_unsettled_transactions(self):
        """Fetch the status of recent unsettled Khalti transactions from Khalti.

        This recovers payments whose redirection never reached Odoo (closed browser,
        network failure) and settles pending ones.

        :return: None
        """
        now = fields.Datetime.now()
        transactions = self.search(
            [
                ("provider_code", "=", "khalti"),
                ("state", "in", ("draft", "pending")),
                ("provider_reference", "!=", False),
                (
                    "create_date",
                    "<=",
                    now - timedelta(minutes=const.UNSETTLED_TX_MIN_AGE_MINUTES),
                ),
                (
                    "create_date",
                    ">=",
                    now - timedelta(days=const.UNSETTLED_TX_MAX_AGE_DAYS),
                ),
            ],
            order="create_date",
            limit=const.UNSETTLED_TX_BATCH_SIZE,
        )
        for tx in transactions:
            try:
                with self.env.cr.savepoint():
                    tx._khalti_verify_and_process()
            except Exception:
                _logger.exception(
                    "Unable to check the Khalti status of transaction %s.", tx.reference
                )
