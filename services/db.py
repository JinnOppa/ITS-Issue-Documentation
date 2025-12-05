
# PART 1.2
import sqlite3
import os
from pathlib import Path
import bcrypt
from datetime import datetime

DB_PATH = Path("db")
DB_FILE = DB_PATH / "docs.db"

def get_connection():
    if not DB_PATH.exists():
        DB_PATH.mkdir(parents=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def initialize_db():
    conn = get_connection()
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password BLOB NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin_lead','admin_regular','regular_user')),
        date_created TEXT NOT NULL
    );
    """)

    # DOCUMENTATION TABLE (no content yet for Part 1)
    c.execute("""
    CREATE TABLE IF NOT EXISTS docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        error_code TEXT NOT NULL,
        category TEXT,
        version INTEGER,
        created_at TEXT,
        updated_at TEXT,
        created_by INTEGER,
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    """)

    conn.commit()
    conn.close()

def create_default_admin_if_missing():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = 'admin_lead'")
    row = c.fetchone()

    if not row:
        hashed = hash_password("adminlead123")
        now = datetime.utcnow().isoformat()
        c.execute("""
        INSERT INTO users (username, password, role, date_created)
        VALUES (?, ?, ?, ?)
        """, ("admin_lead", hashed, "admin_lead", now))
        conn.commit()

    conn.close()

# ============================
# PATCH 2.1 - USER UPDATE/DELETE
# ============================

def update_user(user_id, new_username=None, new_password_hash=None, new_role=None):
    """
    Update user fields selectively.
    Only updates fields that are not None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build dynamic SQL
    fields = []
    params = []

    if new_username is not None:
        fields.append("username = ?")
        params.append(new_username)

    if new_password_hash is not None:
        fields.append("password_hash = ?")
        params.append(new_password_hash)

    if new_role is not None:
        fields.append("role = ?")
        params.append(new_role)

    # Nothing to update
    if not fields:
        return False, "No fields provided to update."

    params.append(user_id)

    sql = f"""
        UPDATE users
        SET {", ".join(fields)}
        WHERE id = ?
    """

    try:
        cursor.execute(sql, params)
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_user(user_id):
    """
    Deletes a user by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()



# Run initialization at import
initialize_db()
create_default_admin_if_missing()



# PART 1.1

# # services/db.py
# import sqlite3
# import os
# from datetime import datetime
# # from passlib.hash import bcrypt
# import bcrypt

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # project root/services/..
# DB_FOLDER = os.path.join(BASE_DIR, "db")
# DB_PATH = os.path.join(DB_FOLDER, "docs.db")
# IMAGES_DIR = os.path.join(BASE_DIR, "images")

# def ensure_folders():
#     os.makedirs(DB_FOLDER, exist_ok=True)
#     os.makedirs(IMAGES_DIR, exist_ok=True)

# def get_connection():
#     ensure_folders()
#     conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#     conn.row_factory = sqlite3.Row
#     return conn

# def create_tables():
#     conn = get_connection()
#     c = conn.cursor()

#     # users
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL,
#         role TEXT NOT NULL CHECK(role IN ('admin','user')),
#         date_created TEXT NOT NULL
#     )
#     """)

#     # documentation (parent)
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS documentation (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         error_code TEXT UNIQUE NOT NULL,
#         date_created TEXT NOT NULL,
#         created_by INTEGER,
#         latest_version INTEGER DEFAULT 1,
#         FOREIGN KEY (created_by) REFERENCES users(id)
#     )
#     """)

#     # documentation_version
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS documentation_version (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         documentation_id INTEGER NOT NULL,
#         version INTEGER NOT NULL,
#         date_updated TEXT NOT NULL,
#         category TEXT,
#         created_by INTEGER,
#         version_label TEXT,
#         FOREIGN KEY(documentation_id) REFERENCES documentation(id),
#         FOREIGN KEY(created_by) REFERENCES users(id),
#         UNIQUE(documentation_id, version)
#     )
#     """)

#     # documentation_content
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS documentation_content (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         doc_version_id INTEGER NOT NULL,
#         order_index INTEGER NOT NULL,
#         content_type TEXT NOT NULL CHECK(content_type IN ('text','image')),
#         text TEXT,
#         image_path TEXT,
#         FOREIGN KEY(doc_version_id) REFERENCES documentation_version(id)
#     )
#     """)

#     conn.commit()
#     conn.close()

# def hash_password(pw: str) -> bytes:
#     return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

# def create_default_admin_if_missing():
#     conn = get_connection()
#     c = conn.cursor()

#     c.execute("SELECT id FROM users WHERE username = ?", ("admin_lead",))
#     if c.fetchone() is None:
#         # default password for testing only — change after testing!
#         # hashed = bcrypt.hash("admin123")
#         hashed = hash_password("admin123")
#         now = datetime.utcnow().isoformat()
#         c.execute(
#             "INSERT INTO users (username, password, role, date_created) VALUES (?,?,?,?)",
#             ("admin_lead", hashed, "admin_lead", now)
#         )
#         conn.commit()
#         print("[db] Default admin created -> username: admin password: admin123")
#     conn.close()

# # Initialize DB on import
# create_tables()
# create_default_admin_if_missing()
