This module adds [eSewa](https://esewa.com.np) as a payment provider, using the official
[eSewa ePay v2](https://developer.esewa.com.np/pages/Epay) redirection flow.

- The customer is redirected to the eSewa hosted payment form with an HMAC-SHA256 signed
  request.
- When eSewa redirects back, the signature of the returned data is checked. The payment
  is then confirmed only after the server-side **status check API** reports it as
  `COMPLETE`, for the transaction's own reference, merchant code and amount.
- A scheduled action ("eSewa: Check unsettled transactions") settles transactions
  whose redirection never reached Odoo, and pending ones.
- Only Nepalese Rupees (NPR) are supported. Refunds, tokenization and manual capture
  are not supported by eSewa ePay and are not declared.

Payments are recorded through Odoo's standard payment transaction flow, so invoices and
sales orders are reconciled by Odoo itself.
