-- disable eSewa payment provider
UPDATE payment_provider
   SET esewa_secret_key = NULL;
