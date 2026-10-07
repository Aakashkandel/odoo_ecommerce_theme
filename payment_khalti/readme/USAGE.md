Customers select *Khalti* on the payment form, are redirected to Khalti to pay, and are
redirected back to Odoo's payment status page.

The transaction is confirmed only when Khalti's lookup API returns `Completed`.
`Pending` and `Initiated` payments are kept pending, `Expired` and `User canceled`
payments are cancelled, and refunded payments are never confirmed. Unconfirmed
transactions are checked again by the scheduled action every 15 minutes during two
days.

Refunds must be made from the Khalti merchant portal.
