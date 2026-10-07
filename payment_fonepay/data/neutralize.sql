-- disable Fonepay payment provider
UPDATE payment_provider
   SET fonepay_secret_key = NULL;
