import csv
import json
import os
from datetime import datetime

DATA_DIR = "data"
ERROR_CSV = os.path.join(DATA_DIR, "errors.csv")
VERSION_CSV = os.path.join(DATA_DIR, "error_versions.csv")


# --------------------------------------------------
# UTIL
# --------------------------------------------------
def _ensure_file(path, headers):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


# --------------------------------------------------
# ERRORS
# --------------------------------------------------
def load_errors():
    _ensure_file(ERROR_CSV, [
        "error_code",
        "error_type",
        "error_name",
        "error_category",
        "created_at",
        "created_by",
        "is_active"
    ])

    with open(ERROR_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [r for r in reader if r["is_active"] == "True"]


# --------------------------------------------------
# VERSIONS
# --------------------------------------------------
def load_versions_by_error(error_code):
    _ensure_file(VERSION_CSV, [
        "error_code",
        "version",
        "content_json",
        "created_at",
        "created_by",
        "is_active"
    ])

    rows = []
    with open(VERSION_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["error_code"] == error_code and r["is_active"] == "True":
                rows.append(r)

    # latest first
    rows.sort(key=lambda x: int(x["version"]), reverse=True)
    return rows


def save_new_version(error_code, content_json, user):
    _ensure_file(VERSION_CSV, [
        "error_code",
        "version",
        "content_json",
        "created_at",
        "created_by",
        "is_active"
    ])

    versions = load_versions_by_error(error_code)
    next_version = 1
    if versions:
        next_version = int(versions[0]["version"]) + 1

    with open(VERSION_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            error_code,
            next_version,
            content_json,
            datetime.now().isoformat(timespec="seconds"),
            user,
            "True"
        ])
