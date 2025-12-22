import csv
from config.settings import ERRORS_MASTER_CSV, ERROR_VERSIONS_CSV
from utils.datetime_utils import now

def create_error(error_code, error_type, name, category, content, user):
    with open(ERRORS_MASTER_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            error_code, error_type, now(), user, "True"
        ])

    with open(ERROR_VERSIONS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            error_code, 1, name, category, content,
            now(), user, "True"
        ])

def add_version(error_code, name, category, content, user):
    versions = []
    with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["error_code"] == error_code:
                versions.append(int(row["version"]))

    new_version = max(versions) + 1

    rows = []
    with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["error_code"] == error_code:
                r["is_latest"] = "False"
            rows.append(r)

    with open(ERROR_VERSIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow({
            "error_code": error_code,
            "version": new_version,
            "error_name": name,
            "error_category": category,
            "content": content,
            "update_date": now(),
            "updated_by": user,
            "is_latest": "True"
        })
