# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# All values below come from the official Khalti ePayment (Web Checkout) documentation:
# https://docs.khalti.com/khalti-epayment/

# The base URLs of the API, per provider state.
API_URLS = {
    "test": "https://dev.khalti.com/api/v2/",
    "enabled": "https://khalti.com/api/v2/",
}

INITIATE_ENDPOINT = "epayment/initiate/"
LOOKUP_ENDPOINT = "epayment/lookup/"

# The payment URL returned by the initiate API must be served over HTTPS by this domain.
PAYMENT_URL_DOMAIN = "khalti.com"

# Mapping of transaction states to the statuses returned by the lookup API. Khalti
# states that "only the status with Completed must be treated as success".
PAYMENT_STATUS_MAPPING = {
    "done": ("Completed",),
    "pending": ("Pending", "Initiated"),
    "cancel": ("Expired", "User canceled"),
    "refunded": ("Refunded", "Partially Refunded"),
}

# Khalti only processes payments in Nepalese Rupees, with amounts expressed in paisa.
SUPPORTED_CURRENCIES = ("NPR",)

# The minimum amount accepted by Khalti, in paisa (Rs. 10).
MINIMUM_AMOUNT_PAISA = 1000

# Khalti requires unique purchase order identifiers: references are suffixed with this
# timestamp.
REFERENCE_DATE_FORMAT = "%y%m%d%H%M%S"

# The codes of the payment methods to activate when Khalti is activated.
DEFAULT_PAYMENT_METHOD_CODES = {"khalti"}

# Khalti's payment identifiers are short opaque strings; anything else is rejected
# unprocessed.
PIDX_PATTERN = r"^[A-Za-z0-9]{1,64}$"

# The window in which the scheduled action reconciles unsettled transactions with
# Khalti.
UNSETTLED_TX_MIN_AGE_MINUTES = 5
UNSETTLED_TX_MAX_AGE_DAYS = 2
UNSETTLED_TX_BATCH_SIZE = 50
