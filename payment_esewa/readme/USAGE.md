Customers select *eSewa* on the payment form, are redirected to eSewa to pay, and are
redirected back to Odoo's payment status page.

The transaction is confirmed only when eSewa's status check API confirms the payment.
Transactions that stay unconfirmed (closed browser, eSewa outage) are checked again by
the scheduled action every 15 minutes during two days. Transactions unknown to eSewa
for more than one hour (expired payment session) are cancelled.

Refunds must be made from the eSewa merchant portal; a payment reported as refunded by
eSewa is never confirmed in Odoo.
