Merchant credentials (issued by Fonepay or the acquiring bank):

- **Merchant Code**: the merchant code (`PID`).
- **Secret Key**: the secret key used to compute the `DV` hashes. It is only visible to
  administrators and is never sent to the browser.
- **Test Base URL** and **Production Base URL**: the base URLs of the Fonepay
  environments, without path, as given in the merchant integration specification.

Before going live, check with the merchant specification that:

- the payment request is `GET <base URL>/api/merchantRequest` and the verification
  request is `GET <base URL>/api/merchantRequest/verificationMerchant`;
- the hashed fields and their order match `const.py` (request:
  `PID,MD,PRN,AMT,CRN,DT,R1,R2,RU`; response: `PRN,PID,PS,RC,UID,BC,INI,P_AMT,R_AMT`;
  verification: `PID,AMT,PRN,BID,UID`);
- the verification response is XML with `success`, `response_code`, `txnAmount` and
  `uniqueId` elements.

If the specification differs, payments stay unconfirmed (they are never wrongly
confirmed) and `const.py` must be adapted.

To configure the provider:

1. Go to *Accounting / Website > Configuration > Payment Providers* and open *Fonepay*.
2. Fill in the credentials and the base URL of the environment to use.
3. Set the state to *Test Mode* (uses the Test Base URL) or *Enabled* (uses the
   Production Base URL). Odoo refuses to enable the provider without the base URL of
   that environment, and never falls back on the other one.
4. Publish the provider.

The website must be reachable over HTTPS on its public base URL, as Fonepay redirects
the customer to `/payment/fonepay/return`.
