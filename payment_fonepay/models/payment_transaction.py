# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re
import unicodedata
from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL, float_repr, urls

from odoo.addons.payment.logging import get_payment_logger

from .. import const
from ..controllers.main import FonepayController

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    fonepay_bank_code = fields.Char(
        help="The code of the bank (BC) that processed the Fonepay payment, required "
        "to verify it.",
        readonly=True,
        copy=False,
    )

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator="-", **kwargs):
        """Override of `payment` to generate references accepted as Fonepay PRN.

        The PRN is 3 to 25 characters long and must be unique for the merchant,
        including across databases; only alphanumeric characters and hyphens are used.
        The prefix is therefore suffixed with the current date and time.
        """
        if provider_code == "fonepay":
            if not prefix:
                prefix = self.sudo()._compute_reference_prefix(separator, **kwargs)
            timestamp = fields.Datetime.now().strftime(const.REFERENCE_DATE_FORMAT)
            # Keep room for the timestamp and for the sequence number that is appended
            # to duplicated prefixes.
            max_prefix_length = const.PRN_MAX_LENGTH - len(timestamp) - 4
            prefix = self._fonepay_sanitize(prefix or "")[:max_prefix_length].strip("-")
            prefix = f"{prefix or 'tx'}-{timestamp}"
            separator = "-"
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    @staticmethod
    def _fonepay_sanitize(value):
        """Return the value restricted to the characters safely accepted by Fonepay.

        :param str value: The value to sanitize.
        :return: The sanitized value.
        :rtype: str
        """
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        return re.sub(const.FORBIDDEN_CHARS_PATTERN, "-", value).strip("-")

    def _fonepay_format_amount(self):
        self.ensure_one()
        return float_repr(self.amount, self.currency_id.decimal_places)

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return Fonepay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        if self.provider_code != "fonepay":
            return super()._get_specific_rendering_values(processing_values)

        if self.currency_id.name not in const.SUPPORTED_CURRENCIES:
            raise ValidationError(
                self.env._("Fonepay only accepts payments in Nepalese Rupees (NPR).")
            )
        if (
            not const.PRN_MIN_LENGTH <= len(self.reference) <= const.PRN_MAX_LENGTH
            or self._fonepay_sanitize(self.reference) != self.reference
        ):
            raise ValidationError(
                self.env._("The transaction reference is not accepted by Fonepay.")
            )

        provider = self.provider_id
        request_date = pytz.utc.localize(fields.Datetime.now()).astimezone(
            pytz.timezone(const.REQUEST_DATE_TIMEZONE)
        )
        url_params = {
            "PID": provider.fonepay_merchant_code,
            "MD": const.PAYMENT_MODE,
            "PRN": self.reference,
            "AMT": self._fonepay_format_amount(),
            "CRN": self.currency_id.name,
            "DT": request_date.strftime(const.REQUEST_DATE_FORMAT),
            "R1": self.reference,
            "R2": const.DEFAULT_REMARK,
            "RU": urls.urljoin(provider.get_base_url(), FonepayController._return_url),
        }
        url_params["DV"] = provider._fonepay_calculate_dv(
            url_params, const.REQUEST_SIGNED_FIELDS
        )
        return {
            "api_url": provider._fonepay_get_url(const.PAYMENT_PATH),
            "url_params": url_params,
        }

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _fonepay_lock_for_update(self):
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

    def _fonepay_process_redirection(self, redirection_data):
        """Process the verified redirection data of Fonepay.

        Successful payments are only confirmed after their verification by Fonepay's
        server. Transactions that already reached a final state are left untouched,
        which makes repeated notifications harmless.

        Note: the DV of the redirection data must have been verified by the caller.

        :param dict redirection_data: The redirection data, with a valid DV.
        :return: None
        """
        self.ensure_one()
        self._fonepay_lock_for_update()
        if self.state in ("done", "cancel"):
            _logger.info(
                "Ignored Fonepay notification for transaction %s already in state %s.",
                self.reference,
                self.state,
            )
            return

        response_code = redirection_data["RC"]
        is_paid = redirection_data["PS"] == "true"
        if is_paid and response_code in const.RESPONSE_CODE_MAPPING["done"]:
            if not redirection_data["UID"] or not redirection_data["BC"]:
                _logger.warning(
                    "Received Fonepay redirection without payment identifiers for "
                    "transaction %s.",
                    self.reference,
                )
                return
            self.write(
                {
                    "provider_reference": redirection_data["UID"],
                    "fonepay_bank_code": redirection_data["BC"],
                }
            )
            self._fonepay_verify_and_process()
        elif not is_paid and response_code in const.RESPONSE_CODE_MAPPING["cancel"]:
            self._process("fonepay", {"PRN": self.reference, "status": response_code})
        elif not is_paid and response_code in const.RESPONSE_CODE_MAPPING["error"]:
            self._process("fonepay", {"PRN": self.reference, "status": response_code})
        else:
            _logger.warning(
                "Received inconsistent Fonepay payment status (PS=%s, RC=%s) for "
                "transaction %s.",
                redirection_data["PS"],
                response_code,
                self.reference,
            )

    def _fonepay_verify_and_process(self):
        """Verify the payment with Fonepay's verification API and process the result.

        The verification is requested with the transaction's own reference and amount,
        never with an amount received from the customer's browser. Only an explicit
        success confirms the payment: any other answer leaves the transaction unchanged.

        Note: the caller must hold the lock on the transaction.

        :return: None
        """
        self.ensure_one()
        provider = self.provider_id
        params = {
            "PRN": self.reference,
            "PID": provider.fonepay_merchant_code,
            "BID": self.fonepay_bank_code,
            "AMT": self._fonepay_format_amount(),
            "UID": self.provider_reference,
        }
        params["DV"] = provider._fonepay_calculate_dv(
            params, const.VERIFICATION_SIGNED_FIELDS
        )
        try:
            verification_data = self._send_api_request(
                "GET", const.VERIFICATION_PATH, params=params
            )
        except ValidationError as error:
            # Leave the transaction as is: it will be checked again by the scheduled
            # action.
            _logger.warning(
                "Unable to verify the Fonepay payment of transaction %s: %s",
                self.reference,
                error,
            )
            return

        if not (
            verification_data.get("success", "").lower() == "true"
            and verification_data.get("response_code", "").lower() == "successful"
        ):
            _logger.warning(
                "Fonepay did not verify the payment of transaction %s (%s).",
                self.reference,
                verification_data.get("message")
                or verification_data.get("response_code"),
            )
            return
        unique_id = verification_data.get("uniqueId")
        if unique_id and unique_id != self.provider_reference:
            _logger.error(
                "Received Fonepay verification for transaction %s with a mismatching "
                "payment"
                " identifier; ignored.",
                self.reference,
            )
            return
        self._process(
            "fonepay",
            {
                "PRN": self.reference,
                "status": "successful",
                "amount": verification_data.get("txnAmount")
                or verification_data.get("amount"),
            },
        )

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data."""
        if provider_code != "fonepay":
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get("PRN")

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to extract the amount and currency from the payment data.
        """
        if self.provider_code != "fonepay":
            return super()._extract_amount_data(payment_data)

        if payment_data.get("status") not in const.RESPONSE_CODE_MAPPING["done"]:
            return None  # The amount is only checked to confirm a payment.

        try:
            amount = float(str(payment_data.get("amount")).replace(",", ""))
        except ValueError:
            amount = None  # Makes `_validate_amount` reject the payment data.
        return {
            "amount": amount,
            # Fonepay only processes NPR; the transaction's currency is checked at
            # rendering.
            "currency_code": const.SUPPORTED_CURRENCIES[0],
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != "fonepay":
            return super()._apply_updates(payment_data)

        status = payment_data.get("status")
        if status in const.RESPONSE_CODE_MAPPING["done"]:
            self._set_done()
        elif status in const.RESPONSE_CODE_MAPPING["cancel"]:
            self._set_canceled(
                state_message=self.env._("The Fonepay payment was canceled.")
            )
        elif status in const.RESPONSE_CODE_MAPPING["error"]:
            self._set_error(self.env._("Fonepay reported the payment as failed."))
        else:
            _logger.warning(
                "Received invalid Fonepay payment status (%s) for transaction %s.",
                status,
                self.reference,
            )
            self._set_error(
                self.env._(
                    "Received an unknown payment status from Fonepay: %s", status
                )
            )

    # === BUSINESS METHODS - SCHEDULED ACTION === #

    @api.model
    def _fonepay_cron_verify_unsettled_transactions(self):
        """Verify recent paid Fonepay transactions that are not verified yet.

        Only transactions for which Fonepay reported a payment (and returned its
        identifiers) can be verified; Fonepay offers no way to look up a payment from
        the reference alone.

        :return: None
        """
        now = fields.Datetime.now()
        transactions = self.search(
            [
                ("provider_code", "=", "fonepay"),
                ("state", "in", ("draft", "pending")),
                ("provider_reference", "!=", False),
                ("fonepay_bank_code", "!=", False),
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
                    tx._fonepay_lock_for_update()
                    if tx.state in ("draft", "pending"):
                        tx._fonepay_verify_and_process()
            except Exception:
                _logger.exception(
                    "Unable to verify the Fonepay transaction %s.", tx.reference
                )
