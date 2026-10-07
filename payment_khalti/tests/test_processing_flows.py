# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from ..controllers.main import KhaltiController
from .common import KhaltiCommon


@tagged("post_install", "-at_install")
class TestProcessingFlows(KhaltiCommon, PaymentHttpCommon):
    def _return(self, **params):
        """
        Simulate Khalti's redirection, with the parameters it appends to the return URL.
        """
        redirect_params = {
            "pidx": self.pidx,
            "transaction_id": "GFq9PFS7b2iYvL8Lir9oXe",
            "tidx": "GFq9PFS7b2iYvL8Lir9oXe",
            "amount": "100000",
            "total_amount": "100000",
            "mobile": "98XXXXX904",
            "status": "Completed",
            "purchase_order_id": self.reference,
            "purchase_order_name": self.reference,
        }
        redirect_params.update(params)
        url = self._build_url(KhaltiController._return_url)
        return self._make_http_get_request(url, params=redirect_params)

    def test_redirection_is_verified_with_lookup(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            response = self._return()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")

    def test_redirection_alone_never_confirms_payment(self):
        """A "Completed" redirection is not trusted if Khalti's lookup API disagrees."""
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("Pending")):
            self._return(status="Completed")
        self.assertEqual(tx.state, "pending")

    def test_user_canceled_redirection(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data("User canceled"), status_code=400):
            self._return(status="User canceled", transaction_id="", tidx="")
        self.assertEqual(tx.state, "cancel")

    @mute_logger("odoo.addons.payment_khalti.controllers.main")
    def test_mismatching_pidx_is_rejected(self):
        """A pidx from another payment cannot be used to settle this transaction."""
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            self._return(pidx="AnotherPaymentPidx")
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment_khalti.controllers.main")
    def test_malformed_redirections_are_rejected(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            for params in (
                {"pidx": ""},
                {"pidx": "../../etc"},
                {"pidx": "A" * 200},
                {"purchase_order_id": ""},
            ):
                response = self._return(**params)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(tx.state, "draft")

    @mute_logger("odoo.addons.payment.models.payment_transaction")
    def test_unknown_reference_is_ignored(self):
        with self._mock_khalti_api(self._lookup_data()) as mock:
            response = self._return(purchase_order_id="UNKNOWN")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock.call_count, 0)

    def test_replayed_redirection_is_harmless(self):
        tx = self._create_initiated_transaction()
        with self._mock_khalti_api(self._lookup_data()) as mock:
            self._return()
            self._return()
            self._return()
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(tx.state, "done")
