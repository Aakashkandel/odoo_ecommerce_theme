This module adds [Fonepay](https://fonepay.com) as a payment provider, using the Fonepay
web payment redirection flow ("Fonepay Web Integration 2.0").

- The customer is redirected to Fonepay with a request hashed with HMAC-SHA512 (`DV`).
- When Fonepay redirects back, the `DV` of the returned data is checked. A successful
  payment is then confirmed only after Fonepay's **verification API** explicitly
  reports it as successful for the transaction's own reference and amount.
- A scheduled action ("Fonepay: Verify paid transactions") verifies paid transactions
  whose verification failed (e.g. Fonepay outage).
- Only Nepalese Rupees (NPR) are supported. Refunds, tokenization and manual capture
  are not declared.

**Important:** Fonepay does not publish its integration specification; it is handed
out by Fonepay or the acquiring bank to each merchant. This module must be checked
against the specification issued for the merchant, and tested in Fonepay's test
environment, before being enabled in production. See the configuration section.
