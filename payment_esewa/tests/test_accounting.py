# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest import SkipTest

from odoo.fields import Command
from odoo.modules.registry import Registry
from odoo.tests import tagged
from odoo.tests.common import get_db_name

from .common import EsewaCommon

try:
    from odoo.addons.account_payment.tests.common import AccountPaymentCommon
except ImportError:  # pragma: no cover
    AccountPaymentCommon = None


@tagged("post_install", "-at_install")
class TestAccounting(
    EsewaCommon, *([AccountPaymentCommon] if AccountPaymentCommon else [])
):
    """
    Check that confirmed eSewa payments go through Odoo's standard accounting flow.
    """

    @classmethod
    def setUpClass(cls):
        registry = Registry(get_db_name())
        if (
            AccountPaymentCommon is None
            or "payment_id" not in registry["payment.transaction"]._fields
        ):
            raise SkipTest("The account_payment module is not installed.")
        super().setUpClass()
        bank_journal = cls.company_data["default_journal_bank"]
        cls.esewa.journal_id = bank_journal
        bank_journal.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_provider_id == cls.esewa
        ).payment_account_id = cls.inbound_payment_method_line.payment_account_id

        cls.npr_invoice = cls.init_invoice(
            "out_invoice",
            partner=cls.partner,
            amounts=[1000.0],
            taxes=[],
            currency=cls.currency_npr,
            post=True,
        )

    def _create_invoice_transaction(self):
        return self._create_transaction(
            flow="redirect",
            amount=self.npr_invoice.amount_total,
            invoice_ids=[Command.set(self.npr_invoice.ids)],
        )

    def _payment_count(self, tx):
        return self.env["account.payment"].search_count(
            [("payment_transaction_id", "=", tx.id)]
        )

    def test_confirmed_payment_pays_invoice_once(self):
        tx = self._create_invoice_transaction()
        status_data = self._status_data(total_amount=self.npr_invoice.amount_total)
        with self._mock_status_api(status_data):
            tx._esewa_verify_and_process()
        tx._post_process()
        self.assertEqual(tx.state, "done")
        self.assertTrue(tx.payment_id)
        self.assertEqual(tx.payment_id.amount, self.npr_invoice.amount_total)
        self.assertIn(self.npr_invoice.payment_state, ("paid", "in_payment"))

        # Duplicate notifications and post-processing create no additional payment.
        with self._mock_status_api(status_data):
            tx._esewa_verify_and_process()
        tx._process("esewa", status_data)
        tx._post_process()
        self.assertEqual(self._payment_count(tx), 1)

    def test_pending_payment_does_not_pay_invoice(self):
        tx = self._create_invoice_transaction()
        with self._mock_status_api(self._status_data("PENDING")):
            tx._esewa_verify_and_process()
        tx._post_process()
        self.assertEqual(tx.state, "pending")
        self.assertFalse(tx.payment_id)
        self.assertEqual(self.npr_invoice.payment_state, "not_paid")

    def test_mismatching_amount_does_not_pay_invoice(self):
        tx = self._create_invoice_transaction()
        with self._mock_status_api(self._status_data(total_amount=1.0)):
            tx._esewa_verify_and_process()
        tx._post_process()
        self.assertEqual(tx.state, "error")
        self.assertFalse(tx.payment_id)
        self.assertEqual(self.npr_invoice.payment_state, "not_paid")
