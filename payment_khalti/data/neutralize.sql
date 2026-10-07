-- disable Khalti payment provider
UPDATE payment_provider
   SET khalti_secret_key = NULL;
