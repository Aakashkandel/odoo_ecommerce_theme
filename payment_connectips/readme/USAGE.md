Customers select *connectIPS* on the payment form, are redirected to connectIPS to pay,
and are redirected back to Odoo's payment status page.

The transaction is confirmed only when connectIPS's validation API returns `SUCCESS`; a
`FAILED` payment is marked as failed. Payments that connectIPS does not know yet
(`ERROR`: not found or incomplete) are checked again by the scheduled action every 15
minutes and cancelled after one hour.
