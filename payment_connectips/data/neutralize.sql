-- disable connectIPS payment provider
UPDATE payment_provider
   SET connectips_app_password = NULL,
       connectips_certificate_password = NULL;
DELETE FROM ir_attachment
 WHERE res_model = 'payment.provider'
   AND res_field = 'connectips_certificate';
