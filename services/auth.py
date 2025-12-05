# PART 1.3
# services/auth.py
from services.db import get_connection, hash_password
import bcrypt
from datetime import datetime

# low-level create_user (adds a user to DB)
# creator_role: optional string used for server-side authorization checks
def create_user(username: str, password: str, role: str, creator_role: str = None):
    # server-side authorization: enforce who may create which role
    if creator_role is not None:
        allowed = {
            "admin_lead": ("admin_lead","admin_regular", "regular_user"),
            "admin_regular": ("regular_user",),
            "regular_user": tuple()
        }
        if role not in allowed.get(creator_role, ()):
            return False, f"Role '{creator_role}' cannot create users with role '{role}'"

    conn = get_connection()
    c = conn.cursor()
    try:
        hashed = hash_password(password)
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO users (username, password, role, date_created)
            VALUES (?, ?, ?, ?)
        """, (username, hashed, role, now))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def authenticate_user(username: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False, "User not found"

    stored = row["password"]
    # stored is bytes (BLOB), bcrypt.checkpw expects bytes
    if bcrypt.checkpw(password.encode("utf-8"), stored):
        return True, {"id": row["id"], "username": row["username"], "role": row["role"]}
    else:
        return False, "Invalid password"

def list_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, date_created FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Role helper utilities
def is_admin_lead(user):
    return user and user.get("role") == "admin_lead"

def is_admin_regular(user):
    return user and user.get("role") == "admin_regular"

def is_regular_user(user):
    return user and user.get("role") == "regular_user"

def can_manage_users(user):
    return is_admin_lead(user) or is_admin_regular(user)

def can_view_users(user):
    return is_admin_lead(user) or is_admin_regular(user)

def can_edit_docs(user):
    return is_admin_lead(user) or is_admin_regular(user)

def can_delete_docs(user):
    return is_admin_lead(user)

def can_view_docs(user):
    return True

def can_create_users(user):
    return user["role"] in ("admin_lead", "admin_regular")

def allowed_roles_for_creator(creator_role):
    if creator_role == "admin_lead":
        return ["admin_lead", "admin_regular", "regular_user"]
    if creator_role == "admin_regular":
        return ["regular_user"]
    return []



# PART 1.2
# from services.db import get_connection, hash_password
# import bcrypt
# from datetime import datetime

# def authenticate_user(username: str, password: str):
#     conn = get_connection()
#     c = conn.cursor()

#     c.execute("SELECT * FROM users WHERE username = ?", (username,))
#     row = c.fetchone()
#     conn.close()

#     if not row:
#         return False, "User not found"

#     stored = row["password"]

#     if bcrypt.checkpw(password.encode("utf-8"), stored):
#         return True, {
#             "id": row["id"],
#             "username": row["username"],
#             "role": row["role"]
#         }
#     else:
#         return False, "Invalid password"


# def create_user(username: str, password: str, role: str):
#     conn = get_connection()
#     c = conn.cursor()

#     hashed = hash_password(password)
#     now = datetime.utcnow().isoformat()

#     try:
#         c.execute("""
#         INSERT INTO users (username, password, role, date_created)
#         VALUES (?, ?, ?, ?)
#         """, (username, hashed, role, now))
#         conn.commit()
#         return True, None
#     except Exception as e:
#         return False, str(e)
#     finally:
#         conn.close()


# # ---------- ROLE CHECK HELPERS ----------
# def is_admin_lead(user):
#     return user["role"] == "admin_lead"

# def is_admin_regular(user):
#     return user["role"] == "admin_regular"

# def is_regular_user(user):
#     return user["role"] == "regular_user"

# def can_manage_users(user):
#     return user["role"] == "admin_lead"

# def can_edit_docs(user):
#     return user["role"] in ("admin_lead", "admin_regular")

# def can_delete_docs(user):
#     return user["role"] == "admin_lead"

# def can_view_users(user):
#     return user["role"] in ("admin_lead", "admin_regular")

# def can_view_docs(user):
#     return True



# PART 1.1

# # services/auth.py
# from services.db import get_connection
# import bcrypt
# from datetime import datetime

# def hash_password(password: str) -> bytes:
#     # bcrypt requires bytes
#     pw_bytes = password.encode("utf-8")
#     salt = bcrypt.gensalt()
#     return bcrypt.hashpw(pw_bytes, salt)

# def check_password(password: str, hashed: bytes) -> bool:
#     return bcrypt.checkpw(password.encode("utf-8"), hashed)

# def create_user(username: str, password: str, role: str = "user"):
#     conn = get_connection()
#     c = conn.cursor()
#     hashed = hash_password(password)
#     now = datetime.utcnow().isoformat()
#     try:
#         c.execute(
#             "INSERT INTO users (username, password, role, date_created) VALUES (?,?,?,?)",
#             (username, hashed, role, now)
#         )
#         conn.commit()
#         return True, None
#     except Exception as e:
#         return False, str(e)
#     finally:
#         conn.close()

# def authenticate_user(username: str, password: str):
#     conn = get_connection()
#     c = conn.cursor()
#     c.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
#     row = c.fetchone()
#     conn.close()
#     if not row:
#         return False, "User not found"

#     stored = row["password"]

#     if check_password(password, stored):
#         return True, {"id": row["id"], "username": row["username"], "role": row["role"]}
#     else:
#         return False, "Invalid password"

# def is_admin_lead(user):
#     return user["role"] == "admin_lead"

# def is_admin_regular(user):
#     return user["role"] == "admin_regular"

# def is_regular_user(user):
#     return user["role"] == "regular_user"

# def can_manage_users(user):
#     return user["role"] == "admin_lead"

# def can_edit_docs(user):
#     return user["role"] in ("admin_lead", "admin_regular")

# def can_delete_docs(user):
#     return user["role"] == "admin_lead"

# def can_view_users(user):
#     return user["role"] in ("admin_lead", "admin_regular")

# def can_view_docs(user):
#     return True  # all roles can view
