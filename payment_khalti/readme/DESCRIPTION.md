This module adds [Khalti](https://khalti.com) as a payment provider, using the official
[Khalti ePayment (Web Checkout)](https://docs.khalti.com/khalti-epayment/) API.

- The payment is initiated server-side; the customer is then redirected to Khalti's
  payment page.
- When Khalti redirects back, the payment is confirmed only after the **lookup API**
  reports it as `Completed`, for the payment identifier (`pidx`) stored at initiation
  and the transaction's amount. As required by Khalti, the redirection data are never
  trusted.
- A scheduled action ("Khalti: Check unsettled transactions") settles transactions
  whose redirection never reached Odoo, and pending ones.
- Only Nepalese Rupees (NPR) are supported, with a minimum of Rs. 10. Refunds,
  tokenization and manual capture are not declared.

Payments are recorded through Odoo's standard payment transaction flow, so invoices and
sales orders are reconciled by Odoo itself.
