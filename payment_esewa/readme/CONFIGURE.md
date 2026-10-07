Merchant credentials (issued by eSewa when the merchant account is opened):

- **Merchant Code**: the `product_code` of the merchant account.
- **Secret Key**: the HMAC secret key. It is only visible to administrators and is
  never sent to the browser.

To configure the provider:

1. Go to *Accounting / Website > Configuration > Payment Providers* and open *eSewa*.
2. Fill in the Merchant Code and Secret Key.
3. Set the state to *Test Mode* to use eSewa's UAT environment
   (`rc-epay.esewa.com.np` / `rc.esewa.com.np`), or *Enabled* to use the production
   environment (`epay.esewa.com.np` / `esewa.com.np`). The environment always follows the
   state: test credentials only work in test mode and live credentials in enabled mode.
4. Publish the provider.

The public UAT credentials (merchant code `EPAYTEST` and its secret key) are listed in
eSewa's developer documentation; never use them with the *Enabled* state.

The website must be reachable over HTTPS on its public base URL, as eSewa redirects the
customer to `/payment/esewa/return` and `/payment/esewa/failure`.
