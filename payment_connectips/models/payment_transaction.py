# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re
import unicodedata
from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger

from .. import const

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator="-", **kwargs):
        """Override of `payment` to generate references accepted as connectIPS TXNID.

        The TXNID is limited to 20 characters and must be unique for the application,
        including across databases; only alphanumeric characters and hyphens are used. The
        prefix is therefore suffixed with the current time, in base 36 to fit the limit.
        """
        if provider_code == "connectips":
            if not prefix:
                prefix = self.sudo()._compute_reference_prefix(separator, **kwargs)
            timestamp = self._connectips_compact_timestamp()
            # Keep room for the timestamp and for the sequence number that is appended to
            # duplicated prefixes.
            max_prefix_length = const.FIELD_MAX_LENGTHS["TXNID"] - len(timestamp) - 4
            prefix = self._connectips_sanitize(prefix or "")[:max_prefix_length].strip(
                "-"
            )
            prefix = f"{prefix or 'T'}-{timestamp}"
            separator = "-"
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    @api.model
    def _connectips_compact_timestamp(self):
        """Return the current time, in seconds since the epoch, encoded in base 36.

        :return: The encoded timestamp, e.g. `T3X0QK`.
        :rtype: str
        """
        seconds = int(fields.Datetime.now().timestamp())
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        encoded = ""
        while seconds:
            seconds, remainder = divmod(seconds, 36)
            encoded = digits[remainder] + encoded
        return encoded

    @staticmethod
    def _connectips_sanitize(value):
        """Return the value restricted to the characters safely accepted by connectIPS.

        :param str value: The value to sanitize.
        :return: The sanitized value.
        :rtype: str
        """
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        return re.sub(const.FORBIDDEN_CHARS_PATTERN, "-", value).strip("-")

    def _connectips_get_amount_paisa(self):
        self.ensure_one()
        return payment_utils.to_minor_currency_units(self.amount, self.currency_id)

    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return connectIPS-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        if self.provider_code != "connectips":
            return super()._get_specific_rendering_values(processing_values)

        if self.currency_id.name not in const.SUPPORTED_CURRENCIES:
            raise ValidationError(
                self.env._("connectIPS only accepts payments in Nepalese Rupees (NPR).")
            )
        if (
            len(self.reference) > const.FIELD_MAX_LENGTHS["TXNID"]
            or self._connectips_sanitize(self.reference) != self.reference
        ):
            raise ValidationError(
                self.env._("The transaction reference is not accepted by connectIPS.")
            )

        provider = self.provider_id
        txn_date = pytz.utc.localize(fields.Datetime.now()).astimezone(
            pytz.timezone(const.TXN_DATE_TIMEZONE)
        )
        particulars = self._connectips_sanitize(self.company_id.name or "")[
            : const.FIELD_MAX_LENGTHS["PARTICULARS"]
        ]
        form_values = {
            "MERCHANTID": provider.connectips_merchant_id,
            "APPID": provider.connectips_app_id,
            "APPNAME": provider.connectips_app_name,
            "TXNID": self.reference,
            "TXNDATE": txn_date.strftime(const.TXN_DATE_FORMAT),
            "TXNCRNCY": self.currency_id.name,
            "TXNAMT": str(self._connectips_get_amount_paisa()),
            "REFERENCEID": self.reference,
            "REMARKS": self.reference,
            "PARTICULARS": particulars or self.reference,
        }
        form_values["TOKEN"] = provider._connectips_calculate_token(
            form_values, const.LOGIN_PAGE_SIGNED_FIELDS
        )
        return {
            "api_url": provider._connectips_get_url(const.LOGIN_PAGE_PATH),
            "form_values": form_values,
        }

    # === BUSINESS METHODS - PAYMENT FLOW === #

    def _connectips_lock_for_update(self):
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

    def _connectips_verify_and_process(self):
        """Validate the transaction with connectIPS's API and process the result.

        The validation is requested with the transaction's own reference and amount,
        never with values received from the customer's browser. Transactions that
        already reached a final state are left untouched, which makes repeated
        notifications harmless.

        :return: None
        """
        self.ensure_one()
        self._connectips_lock_for_update()
        if self.state in ("done", "cancel"):
            _logger.info(
                "Ignored connectIPS notification for transaction %s already in state "
                "%s.",
                self.reference,
                self.state,
            )
            return

        provider = self.provider_id
        amount_paisa = self._connectips_get_amount_paisa()
        token_data = {
            "MERCHANTID": provider.connectips_merchant_id,
            "APPID": provider.connectips_app_id,
            "REFERENCEID": self.reference,
            "TXNAMT": str(amount_paisa),
        }
        try:
            payload = {
                "merchantId": int(provider.connectips_merchant_id),
                "appId": provider.connectips_app_id,
                "referenceId": self.reference,
                "txnAmt": amount_paisa,
                "token": provider._connectips_calculate_token(
                    token_data, const.VALIDATE_TXN_SIGNED_FIELDS
                ),
            }
            payment_data = self._send_api_request(
                "POST", const.VALIDATE_TXN_PATH, json=payload
            )
        except ValidationError as error:
            # Leave the transaction as is: it will be checked again by the scheduled
            # action.
            _logger.warning(
                "Unable to validate the connectIPS transaction %s: %s",
                self.reference,
                error,
            )
            return

        if not isinstance(payment_data, dict):
            _logger.warning(
                "Received malformed connectIPS validation for transaction %s.",
                self.reference,
            )
            return
        expected_identity = {
            "merchantId": provider.connectips_merchant_id,
            "appId": provider.connectips_app_id,
            "referenceId": self.reference,
        }
        if any(
            str(payment_data.get(key)) != value
            for key, value in expected_identity.items()
        ):
            _logger.error(
                "Received connectIPS validation for transaction %s with a mismatching "
                "merchant,"
                " application or reference; ignored.",
                self.reference,
            )
            return
        self._process("connectips", payment_data)

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Override of `payment` to extract the reference from the payment data."""
        if provider_code != "connectips":
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get("referenceId")

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to extract the amount and currency from the payment data.
        """
        if self.provider_code != "connectips":
            return super()._extract_amount_data(payment_data)

        if payment_data.get("status") not in const.PAYMENT_STATUS_MAPPING["done"]:
            return None  # The amount is only checked to confirm a payment.

        try:
            amount_paisa = int(str(payment_data.get("txnAmt")))
        except ValueError:
            amount = None  # Makes `_validate_amount` reject the payment data.
        else:
            amount = payment_utils.to_major_currency_units(
                amount_paisa, self.currency_id
            )
        return {
            "amount": amount,
            # connectIPS only processes NPR; the transaction's currency is checked at
            # rendering.
            "currency_code": const.SUPPORTED_CURRENCIES[0],
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != "connectips":
            return super()._apply_updates(payment_data)

        status = payment_data.get("status")
        status_description = payment_data.get("statusDesc") or ""
        if status in const.PAYMENT_STATUS_MAPPING["done"]:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING["error"]:
            self._set_error(
                self.env._(
                    "connectIPS reported the payment as unsuccessful: %s",
                    status_description,
                )
            )
        elif status in const.PAYMENT_STATUS_MAPPING["not_found"]:
            cancel_threshold = fields.Datetime.now() - timedelta(
                minutes=const.NOT_FOUND_CANCEL_DELAY_MINUTES
            )
            if self.create_date <= cancel_threshold:
                self._set_canceled(
                    state_message=self.env._(
                        "The connectIPS payment was not completed: %s",
                        status_description,
                    )
                )
            else:
                _logger.info(
                    "connectIPS reported transaction %s as %s; it will be checked "
                    "again.",
                    self.reference,
                    status_description,
                )
        else:
            _logger.warning(
                "Received invalid connectIPS payment status (%s) for transaction %s.",
                status,
                self.reference,
            )
            self._set_error(
                self.env._(
                    "Received an unknown payment status from connectIPS: %s", status
                )
            )

    # === BUSINESS METHODS - SCHEDULED ACTION === #

    @api.model
    def _connectips_cron_check_unsettled_transactions(self):
        """Validate recent unsettled connectIPS transactions with connectIPS's server.

        This recovers payments whose redirection never reached Odoo (closed browser,
        network failure).

        :return: None
        """
        now = fields.Datetime.now()
        transactions = self.search(
            [
                ("provider_code", "=", "connectips"),
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
                    tx._connectips_verify_and_process()
            except Exception:
                _logger.exception(
                    "Unable to check the connectIPS status of transaction %s.",
                    tx.reference,
                )
