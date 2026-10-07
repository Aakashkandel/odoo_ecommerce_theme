Merchant credentials:

- **Live Secret Key**: the `live_secret_key` of the merchant account. Use the key of
  the sandbox merchant account (from `test-admin.khalti.com`) in test mode, and the
  key of the production merchant account (from `admin.khalti.com`) when enabled. It is
  only visible to administrators and is never sent to the browser.

To configure the provider:

1. Go to *Accounting / Website > Configuration > Payment Providers* and open *Khalti*.
2. Fill in the Live Secret Key.
3. Set the state to *Test Mode* to use the sandbox API (`dev.khalti.com`), or
   *Enabled* to use the production API (`khalti.com`). The environment always follows
   the state.
4. Publish the provider.

The website must be reachable over HTTPS on its public base URL, as Khalti redirects the
customer to `/payment/khalti/return`.
