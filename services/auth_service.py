import csv
from config.settings import USERS_CSV
from utils.security import hash_password, verify_password
from utils.datetime_utils import now

def ensure_default_admin():
    has_user = False

    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for _ in reader:
            has_user = True
            break

    if has_user:
        return

    # CREATE DEFAULT IT ADMIN
    with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "master",
            hash_password("123"),
            "IT_ADMIN",
            now(),
            "SYSTEM",
            "True"
        ])

    print("[INIT] Default IT_ADMIN created (admin / admin123)")


def authenticate(username, password):
    found_user = None

    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username:
                found_user = row
                break

    # -------------------------
    # USER FOUND
    # -------------------------
    if found_user:
        if found_user["is_active"] != "True":
            return None

        if verify_password(password, found_user["password_hash"]):
            return {
                "username": found_user["username"],
                "role": found_user["role"]
            }
        else:
            # PASSWORD SALAH → JANGAN AUTO CREATE
            return None

    # -------------------------
    # USER NOT FOUND → AUTO CREATE
    # -------------------------
    with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            username,
            hash_password(password),
            "USER",
            now(),
            "SYSTEM",
            "True"
        ])

    return {
        "username": username,
        "role": "USER"
    }

