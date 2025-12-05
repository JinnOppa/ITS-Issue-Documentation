import sqlite3
conn = sqlite3.connect("db/docs.db")
c = conn.cursor()
c.execute("ALTER TABLE users RENAME TO tmp_users;")
c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password BLOB NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin_lead','admin_regular','regular_user')),
    date_created TEXT NOT NULL
);
""")
c.execute("""
INSERT INTO users (id, username, password, role, date_created)
SELECT id, username, password, 
CASE 
    WHEN role = 'admin' THEN 'admin_lead'
    ELSE role 
END,
date_created
FROM tmp_users;
""")
c.execute("DROP TABLE tmp_users;")
conn.commit()
conn.close()
