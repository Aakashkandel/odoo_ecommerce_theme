This module adds [connectIPS](https://connectips.com) (Nepal Clearing House Ltd.) as a
payment provider, following the official
[connectIPS gateway documentation](https://doc.connectips.com/docs/category/2-connectips-gateway).

- The customer is redirected to the connectIPS login page with a request signed with
  SHA256withRSA, using the private key of the merchant's certificate (PFX).
- When connectIPS redirects back to the success or failure URL, only the `TXNID` is
  used: the payment is confirmed only after the **validatetxn API** reports it as
  `SUCCESS`, for the transaction's own merchant, application, reference and amount.
- A scheduled action ("connectIPS: Check unsettled transactions") settles transactions
  whose redirection never reached Odoo.
- Only Nepalese Rupees (NPR) are supported. Refunds, tokenization and manual capture
  are not declared.

Payments are recorded through Odoo's standard payment transaction flow, so invoices and
sales orders are reconciled by Odoo itself.
