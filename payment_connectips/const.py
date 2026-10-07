# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# All values below come from the official connectIPS gateway documentation published by
# NCHL: https://doc.connectips.com/docs/category/2-connectips-gateway The documentation
# does not publish the base URLs of the test and live environments; they are provided by
# NCHL at merchant onboarding and configured on the provider.

# The paths of the gateway endpoints, relative to the environment's base URL.
LOGIN_PAGE_PATH = "/connectipswebgw/loginpage"
VALIDATE_TXN_PATH = "/connectipswebws/api/creditor/validatetxn"

# The fields of the payment request, in the order in which they are signed.
LOGIN_PAGE_SIGNED_FIELDS = (
    "MERCHANTID",
    "APPID",
    "APPNAME",
    "TXNID",
    "TXNDATE",
    "TXNCRNCY",
    "TXNAMT",
    "REFERENCEID",
    "REMARKS",
    "PARTICULARS",
)

# The fields of the validation request, in the order in which they are signed.
VALIDATE_TXN_SIGNED_FIELDS = ("MERCHANTID", "APPID", "REFERENCEID", "TXNAMT")

# The maximum lengths of the payment request fields.
FIELD_MAX_LENGTHS = {
    "APPID": 15,
    "APPNAME": 30,
    "TXNID": 20,
    "REFERENCEID": 20,
    "REMARKS": 50,
    "PARTICULARS": 100,
}

# The format of TXNDATE (DD-MM-YYYY), expressed in Nepal's time zone.
TXN_DATE_FORMAT = "%d-%m-%Y"
TXN_DATE_TIMEZONE = "Asia/Kathmandu"

# Mapping of transaction states to the statuses returned by the validation API.
PAYMENT_STATUS_MAPPING = {
    "done": ("SUCCESS",),
    "error": ("FAILED",),
    # "TRANSACTION NOT FOUND" or "TRANSACTION INCOMPLETE": the customer did not complete
    # it (yet).
    "not_found": ("ERROR",),
}

# connectIPS only processes payments in Nepalese Rupees, with amounts expressed in
# paisa.
SUPPORTED_CURRENCIES = ("NPR",)

# The codes of the payment methods to activate when connectIPS is activated.
DEFAULT_PAYMENT_METHOD_CODES = {"connectips"}

# connectIPS identifiers only use alphanumeric characters and hyphens here, so that the
# comma-separated signed messages cannot be ambiguous.
FORBIDDEN_CHARS_PATTERN = r"[^A-Za-z0-9-]+"

# The TXNID sent back to the return URLs is short; anything else is rejected
# unprocessed.
TXNID_PATTERN = r"^[A-Za-z0-9-]{1,20}$"

# A transaction unknown to connectIPS is only canceled after this delay, so that a
# payment still being completed by the customer is never canceled prematurely.
NOT_FOUND_CANCEL_DELAY_MINUTES = 60

# The window in which the scheduled action reconciles unsettled transactions with
# connectIPS.
UNSETTLED_TX_MIN_AGE_MINUTES = 5
UNSETTLED_TX_MAX_AGE_DAYS = 2
UNSETTLED_TX_BATCH_SIZE = 50
