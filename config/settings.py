BASE_PATH = "data/"

USERS_CSV = BASE_PATH + "users.csv"
ERRORS_MASTER_CSV = BASE_PATH + "errors_master.csv"
ERROR_VERSIONS_CSV = BASE_PATH + "error_versions.csv"
ACTIVITY_LOGS_CSV = BASE_PATH + "activity_logs.csv"

ROLES = ["IT_ADMIN", "IT_USER", "USER"]

ERROR_TYPES = {
    "Account Payables": "AP",
    "Account Receivables": "AR",
    "Tax Indomaret": "AT",
    "General Ledgers": "GL",
    "Fixed Asset": "FA"
}
