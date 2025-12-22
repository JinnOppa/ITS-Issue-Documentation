import csv
from config.settings import ERRORS_MASTER_CSV

def generate_error_code(prefix):
    max_num = 0
    with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["error_code"].startswith(prefix):
                num = int(row["error_code"][2:])
                max_num = max(max_num, num)
    return f"{prefix}{str(max_num + 1).zfill(4)}"
