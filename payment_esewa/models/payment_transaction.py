# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re
import unicodedata
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL, float_repr, urls

from odoo.addons.payment.logging import get_payment_logger

from .. import const
from ..controllers.main import EsewaController

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator="-", **kwargs):
        """Override of `payment` to generate transaction UUIDs accepted by eSewa.

        eSewa only accepts alphanumeric characters and hyphens, and rejects any UUID it
        already received for the merchant ("Duplicate transaction UUID"), including
        UUIDs sent from another database or, in test mode, by other users of the shared
        test merchant. The prefix is therefore suffixed with the current date and time.
        """
        if provider_code == "esewa":
            if not prefix:
                prefix = self.sudo()._compute_reference_prefix(separator, **kwargs)
            prefix = (
                unicodedata.normalize("NFKD", prefix or "")
                .encode("ascii", "ignore")
                .decode()
            )
            prefix = re.sub(const.REFERENCE_FORBIDDEN_CHARS_PATTERN, "-", prefix)
            prefix = prefix.strip("-") or "tx"
            timestamp = fields.Datetime.now().strftime(const.REFERENCE_DATE_FORMAT)
            prefix = f"{prefix}-{timestamp}"
            separator = "-"
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return eSewa-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        if self.provider_code != "esewa":
            return super()._get_specific_rendering_values(processing_values)

        if self.currency_id.name not in const.SUPPORTED_CURRENCIES:
            raise ValidationError(
                self.env._("eSewa only accepts payments in Nepalese Rupees (NPR).")
            )

        provider = self.provider_id
        base_url = provider.get_base_url()
        total_amount = self._esewa_format_amount()
        form_values = {
            "amount": total_amount,
            "tax_amount": "0",
            "total_amount": total_amount,
            "transaction_uuid": self.reference,
            "product_code": provider.esewa_product_code,
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": urls.urljoin(base_url, EsewaController._return_url),
            "failure_url": urls.urljoin(base_url, EsewaController._failure_url),
            "signed_field_names": ",".join(const.REQUEST_SIGNED_FIELDS),
        }
        form_values["signature"] = provider._esewa_calculate_signature(
            form_values, const.REQUEST_SIGNED_FIELDS
        )
        return {
            "api_url": provider._esewa_get_environment_url(const.PAYMENT_FORM_URLS),
            "form_values": form_values,
        }

    def _esewa_format_amount(self):
        """Return the amount of the transaction formatted as sent to eSewa.

        :return: The formatted amount.
        :rtype: str
        """
        self.ensure_one()
        return float_repr(self.amount, self.currency_id.decimal_places)

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _esewa_lock_for_update(self):
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

    def _esewa_verify_and_process(self):
        """Fetch the status of the transaction from eSewa's server and process it.

        The status is fetched with the transaction's own reference, amount and merchant
        code, and never with values received from the customer's browser. Transactions
        that already reached a final state are left untouched, which makes repeated
        notifications harmless.

        :return: None
        """
        self.ensure_one()
        self._esewa_lock_for_update()
        if self.state in ("done", "cancel"):
            _logger.info(
                "Ignored eSewa notification for transaction %s already in state %s.",
                self.reference,
                self.state,
            )
            return

        try:
            payment_data = self._send_api_request(
                "GET",
                "",
                params={
                    "product_code": self.provider_id.esewa_product_code,
                    "total_amount": self._esewa_format_amount(),
                    "transaction_uuid": self.reference,
                },
            )
        except ValidationError as error:
            # Leave the transaction as is: it will be checked again by the scheduled
            # action.
            _logger.warning(
                "Unable to fetch the eSewa status of transaction %s: %s",
                self.reference,
                error,
            )
            return

        if not isinstance(payment_data, dict):
            _logger.warning(
                "Received malformed eSewa status for transaction %s.", self.reference
            )
            return
        is_complete = payment_data.get("status") in const.PAYMENT_STATUS_MAPPING["done"]
        expected_identity = {
            "transaction_uuid": self.reference,
            "product_code": self.provider_id.esewa_product_code,
        }
        if any(
            # The identity is mandatory to confirm a payment, and must match whenever
            # present.
            (is_complete or payment_data.get(key) is not None)
            and payment_data.get(key) != value
            for key, value in expected_identity.items()
        ):
            _logger.error(
                "Received eSewa status for transaction %s with a mismatching reference "
                "or merchant"
                " code; ignored.",
                self.reference,
            )
            return
        self._process("esewa", payment_data)

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data."""
        if provider_code != "esewa":
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get("transaction_uuid")

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to extract the amount and currency from the payment data.
        """
        if self.provider_code != "esewa":
            return super()._extract_amount_data(payment_data)

        if payment_data.get("status") not in const.PAYMENT_STATUS_MAPPING["done"]:
            return None  # The amount is only checked to confirm a payment.

        try:
            amount = float(str(payment_data.get("total_amount")).replace(",", ""))
        except ValueError:
            amount = None  # Makes `_validate_amount` reject the payment data.
        return {
            "amount": amount,
            # eSewa only processes NPR; the transaction's currency is checked at
            # rendering.
            "currency_code": const.SUPPORTED_CURRENCIES[0],
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != "esewa":
            return super()._apply_updates(payment_data)

        if ref_id := payment_data.get("ref_id"):
            self.provider_reference = ref_id

        status = payment_data.get("status")
        if status in const.PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING["pending"]:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING["cancel"]:
            self._set_canceled(
                state_message=self.env._("The payment was reversed by eSewa.")
            )
        elif status in const.PAYMENT_STATUS_MAPPING["refunded"]:
            # Refunds are made from the eSewa merchant portal and are not handled by
            # Odoo.
            _logger.warning(
                "eSewa reported transaction %s as refunded (%s).",
                self.reference,
                status,
            )
            self._set_error(
                self.env._("eSewa reported this payment as refunded (%s).", status)
            )
        elif status in const.PAYMENT_STATUS_MAPPING["not_found"]:
            cancel_threshold = fields.Datetime.now() - timedelta(
                minutes=const.NOT_FOUND_CANCEL_DELAY_MINUTES
            )
            if self.create_date <= cancel_threshold:
                self._set_canceled(
                    state_message=self.env._("The eSewa payment session expired.")
                )
            else:
                _logger.info(
                    "eSewa does not know transaction %s yet; its status will be "
                    "checked again.",
                    self.reference,
                )
        else:
            _logger.warning(
                "Received invalid eSewa payment status (%s) for transaction %s.",
                status,
                self.reference,
            )
            self._set_error(
                self.env._("Received an unknown payment status from eSewa: %s", status)
            )

    # === BUSINESS METHODS - SCHEDULED ACTION === #

    @api.model
    def _esewa_cron_check_unsettled_transactions(self):
        """Fetch the status of recent unsettled eSewa transactions from eSewa's server.

        This recovers payments whose redirection never reached Odoo (closed browser,
        network failure) and settles pending ones.

        :return: None
        """
        now = fields.Datetime.now()
        transactions = self.search(
            [
                ("provider_code", "=", "esewa"),
                ("state", "in", ("draft", "pending")),
                ("operation", "!=", "validation"),
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
                    tx._esewa_verify_and_process()
            except Exception:
                _logger.exception(
                    "Unable to check the eSewa status of transaction %s.", tx.reference
                )
