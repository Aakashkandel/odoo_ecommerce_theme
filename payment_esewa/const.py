# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# All values below come from the official eSewa ePay v2 documentation:
# https://developer.esewa.com.np/pages/Epay

# The URLs of the hosted payment form, per provider state.
PAYMENT_FORM_URLS = {
    "test": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
    "enabled": "https://epay.esewa.com.np/api/epay/main/v2/form",
}

# The URLs of the server-side status check API, per provider state.
STATUS_CHECK_URLS = {
    "test": "https://rc.esewa.com.np/api/epay/transaction/status/",
    "enabled": "https://esewa.com.np/api/epay/transaction/status/",
}

# The fields signed in the payment request, in the documented order.
REQUEST_SIGNED_FIELDS = ("total_amount", "transaction_uuid", "product_code")

# The fields signed in the redirection response, in the documented order.
RESPONSE_SIGNED_FIELDS = (
    "transaction_code",
    "status",
    "total_amount",
    "transaction_uuid",
    "product_code",
    "signed_field_names",
)

# Mapping of transaction states to the statuses returned by the status check API.
PAYMENT_STATUS_MAPPING = {
    "done": ("COMPLETE",),
    "pending": ("PENDING", "AMBIGUOUS"),
    "cancel": ("CANCELED",),
    "refunded": ("FULL_REFUND", "PARTIAL_REFUND"),
    "not_found": ("NOT_FOUND",),
}

# eSewa only settles payments in Nepalese Rupees.
SUPPORTED_CURRENCIES = ("NPR",)

# The codes of the payment methods to activate when eSewa is activated.
DEFAULT_PAYMENT_METHOD_CODES = {"esewa"}

# eSewa only accepts alphanumeric characters and hyphens in the transaction UUID.
REFERENCE_FORBIDDEN_CHARS_PATTERN = r"[^A-Za-z0-9-]+"

# eSewa rejects reused transaction UUIDs: references are suffixed with this timestamp.
REFERENCE_DATE_FORMAT = "%y%m%d%H%M%S"

# The redirection payload is a small base64-encoded JSON; anything bigger is rejected
# unparsed.
MAX_RESPONSE_PAYLOAD_LENGTH = 4096

# A transaction unknown to eSewa ("NOT_FOUND": session expired) is only canceled after
# this delay, so that a payment still being completed by the customer is never canceled
# prematurely.
NOT_FOUND_CANCEL_DELAY_MINUTES = 60

# The window in which the scheduled action reconciles unsettled transactions with eSewa.
UNSETTLED_TX_MIN_AGE_MINUTES = 5
UNSETTLED_TX_MAX_AGE_DAYS = 2
UNSETTLED_TX_BATCH_SIZE = 50
