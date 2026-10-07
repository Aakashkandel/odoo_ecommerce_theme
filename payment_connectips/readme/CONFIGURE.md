Merchant credentials (issued by NCHL at merchant registration):

- **Merchant ID**: the numeric merchant identifier.
- **App ID** and **App Name**: the identifiers of the merchant application. The App ID
  is also the user name of the validation API.
- **API Password**: the password of the validation API.
- **Certificate (PFX)** and **Certificate Password**: the PKCS#12 file holding the
  private key used to sign requests (`CREDITOR.pfx` in the test environment).
- **Test Base URL** and **Production Base URL**: the base URLs of the connectIPS
  environments (for instance `https://<host>`, without path). They are not published in
  the public documentation and must be taken from NCHL's onboarding material.

The password, PFX file and its password are only visible to administrators and are never
sent to the browser.

To configure the provider:

1. Register these URLs with NCHL as the merchant's success and failure URLs:
   `https://<your-domain>/payment/connectips/return` and
   `https://<your-domain>/payment/connectips/failure`.
2. Go to *Accounting / Website > Configuration > Payment Providers* and open
   *connectIPS*.
3. Fill in the credentials and the base URL of the environment to use.
4. Set the state to *Test Mode* (uses the Test Base URL) or *Enabled* (uses the
   Production Base URL). Odoo refuses to enable the provider without the base URL of
   that environment, and never falls back on the other one.
5. Publish the provider.
