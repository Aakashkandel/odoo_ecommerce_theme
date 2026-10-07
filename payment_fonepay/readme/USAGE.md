Customers select *Fonepay* on the payment form, are redirected to Fonepay to pay, and
are redirected back to Odoo's payment status page.

The transaction is confirmed only when Fonepay's verification API confirms the payment.
Cancelled and failed payments reported by a valid redirection are marked as such.
Fonepay offers no way to look up a payment from its reference alone, so transactions
whose redirection never reached Odoo stay in draft.
