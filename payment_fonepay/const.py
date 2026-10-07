# Copyright 2026 Amnil Technologies
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

# Fonepay does not publish its merchant integration specification: it is handed out by
# Fonepay or the acquiring bank at merchant onboarding (https://fonepay.com/faqs). The
# values below follow the "Fonepay Web Integration 2.0" specification and MUST be
# checked against the specification issued for the merchant before going live. The base
# URLs of the environments are not hard-coded: they are configured on the provider from
# that specification.

# The paths of the endpoints, relative to the environment's base URL.
PAYMENT_PATH = "/api/merchantRequest"
VERIFICATION_PATH = "/api/merchantRequest/verificationMerchant"

# The fields of the payment request, in the order in which they are hashed into DV.
REQUEST_SIGNED_FIELDS = ("PID", "MD", "PRN", "AMT", "CRN", "DT", "R1", "R2", "RU")

# The fields of the redirection response, in the order in which they are hashed into DV.
RESPONSE_SIGNED_FIELDS = (
    "PRN",
    "PID",
    "PS",
    "RC",
    "UID",
    "BC",
    "INI",
    "P_AMT",
    "R_AMT",
)

# The fields of the verification request, in the order in which they are hashed into DV.
VERIFICATION_SIGNED_FIELDS = ("PID", "AMT", "PRN", "BID", "UID")

# The payment mode of the request ("P" for payment).
PAYMENT_MODE = "P"

# The format of the request date (DT), expressed in Nepal's time zone.
REQUEST_DATE_FORMAT = "%m/%d/%Y"
REQUEST_DATE_TIMEZONE = "Asia/Kathmandu"

# The value of the second remark, which is mandatory but unused.
DEFAULT_REMARK = "N/A"

# The bounds of the product reference number (PRN) length.
PRN_MIN_LENGTH = 3
PRN_MAX_LENGTH = 25

# The PRN must be unique for the merchant: references are suffixed with this timestamp.
REFERENCE_DATE_FORMAT = "%y%m%d%H%M%S"

# Mapping of transaction states to the response codes (RC) of the redirection.
RESPONSE_CODE_MAPPING = {
    "done": ("successful",),
    "cancel": ("cancel",),
    "error": ("failed",),
}

# Fonepay only processes payments in Nepalese Rupees.
SUPPORTED_CURRENCIES = ("NPR",)

# The codes of the payment methods to activate when Fonepay is activated.
DEFAULT_PAYMENT_METHOD_CODES = {"fonepay"}

# Fonepay references only use alphanumeric characters and hyphens here, so that the
# comma-separated hashed messages cannot be ambiguous.
FORBIDDEN_CHARS_PATTERN = r"[^A-Za-z0-9-]+"

# The redirection values are short; anything bigger is rejected unprocessed.
MAX_RESPONSE_VALUE_LENGTH = 256

# The window in which the scheduled action verifies paid but unsettled transactions.
UNSETTLED_TX_MAX_AGE_DAYS = 2
UNSETTLED_TX_BATCH_SIZE = 50
