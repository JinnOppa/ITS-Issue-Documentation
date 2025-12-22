"""
doc_system_v4.py
"""

import os
import csv
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab

# ======================================================
# CONFIG
# ======================================================
DATA_DIR = "data"
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
DOCS_CSV = os.path.join(DATA_DIR, "documentation.csv")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "comments.csv")

ERROR_TYPES = {
    "Account Payables": "AP",
    "Account Receivables": "AR",
    "Tax Indomaret": "AT",
    "General Ledgers": "GL",
    "Fixed Asset": "FA"
}

PERMISSIONS = {
    "it_admin": {
        "doc": ["create","view","update","delete","delete_version"],
        "user": ["create","update","delete"]
    },
    "it_user": {
        "doc": ["create","view","update","delete_version"],
        "user": ["create","update","delete"]
    },
    "user": {
        "doc": ["view"]
    }
}

# ======================================================
# INIT
# ======================================================
def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)

    if not os.path.exists(DOCS_CSV):
        with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "error_code",
                "error_type",
                "error_name",
                "error_category",
                "latest_version",
                "created_at",
                "created_by"
            ])

    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username","password","role"])
            writer.writerow(["admin","admin","it_admin"])
            writer.writerow(["ituser","ituser","it_user"])
            writer.writerow(["viewer","viewer","user"])

    if not os.path.exists(COMMENTS_CSV):
        with open(COMMENTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["error_code","version","user","comment","timestamp"])

ensure_files()

# ======================================================
# HELPERS
# ======================================================
def has_permission(role, domain, action):
    return action in PERMISSIONS.get(role, {}).get(domain, [])

def load_users():
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        return {r["username"]: r for r in csv.DictReader(f)}

def load_docs():
    with open(DOCS_CSV, newline="", encoding="utf-8") as f:
        return {r["error_code"]: r for r in csv.DictReader(f)}

def save_docs(docs):
    with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "error_code","error_type","error_name",
            "error_category","latest_version",
            "created_at","created_by"
        ])
        for d in docs.values():
            writer.writerow([
                d["error_code"], d["error_type"], d["error_name"],
                d["error_category"], d["latest_version"],
                d["created_at"], d["created_by"]
            ])

def generate_error_code(error_type):
    prefix = ERROR_TYPES[error_type]
    docs = load_docs()
    nums = []
    for code in docs:
        if code.startswith(prefix):
            try:
                nums.append(int(code[len(prefix):]))
            except:
                pass
    next_num = max(nums, default=0) + 1
    return f"{prefix}{next_num:04d}"

# ======================================================
# LOGIN
# ======================================================
class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("300x200")

        ttk.Label(self.root, text="Username").pack()
        self.u = ttk.Entry(self.root)
        self.u.pack(fill="x", padx=20)

        ttk.Label(self.root, text="Password").pack()
        self.p = ttk.Entry(self.root, show="*")
        self.p.pack(fill="x", padx=20)

        ttk.Button(self.root, text="Login", command=self.login).pack(pady=10)
        self.root.mainloop()

    def login(self):
        users = load_users()
        u = self.u.get()
        p = self.p.get()
        if u in users and users[u]["password"] == p:
            self.root.destroy()
            AppMain(users[u]["role"], u)
        else:
            messagebox.showerror("Error","Invalid login")

# ======================================================
# MAIN APP
# ======================================================
class AppMain:
    def __init__(self, role, username):
        self.role = role
        self.username = username
        self.current_error = None
        self.root = tk.Tk()
        self.root.title(f"Doc System ({role})")
        self.root.geometry("1100x700")

        left = ttk.Frame(self.root)
        left.pack(side="left", fill="y")

        right = ttk.Frame(self.root)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Documentation", font=("Arial",12,"bold")).pack()
        self.lst = tk.Listbox(left, width=40)
        self.lst.pack(fill="y", expand=True)
        self.lst.bind("<<ListboxSelect>>", self.select_doc)

        if has_permission(role,"doc","create"):
            ttk.Button(left, text="Create Documentation", command=self.create_doc).pack(pady=5)

        self.txt = ScrolledText(right)
        self.txt.pack(fill="both", expand=True)

        self.refresh_docs()
        self.root.mainloop()

    def refresh_docs(self):
        self.lst.delete(0,"end")
        self.docs = load_docs()
        for d in self.docs.values():
            self.lst.insert("end", f'{d["error_code"]} - {d["error_name"]}')

    def select_doc(self, e):
        sel = self.lst.curselection()
        if not sel: return
        code = self.lst.get(sel[0]).split(" - ")[0]
        self.current_error = code
        self.txt.delete("1.0","end")
        self.txt.insert("end", json.dumps(self.docs[code], indent=2))

    def create_doc(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Documentation")
        dlg.geometry("400x300")

        ttk.Label(dlg, text="Error Type").pack()
        cb_type = ttk.Combobox(dlg, values=list(ERROR_TYPES.keys()), state="readonly")
        cb_type.pack(fill="x")

        ttk.Label(dlg, text="Error Name").pack()
        ent_name = ttk.Entry(dlg)
        ent_name.pack(fill="x")

        ttk.Label(dlg, text="Category").pack()
        ent_cat = ttk.Entry(dlg)
        ent_cat.pack(fill="x")

        lbl_code = ttk.Label(dlg, text="Error Code: -")
        lbl_code.pack(pady=5)

        def on_type_change(e):
            code = generate_error_code(cb_type.get())
            lbl_code.config(text=f"Error Code: {code}")

        cb_type.bind("<<ComboboxSelected>>", on_type_change)

        def save():
            etype = cb_type.get()
            if not etype:
                messagebox.showerror("Error","Select Error Type")
                return
            code = lbl_code.cget("text").split(": ")[1]
            docs = load_docs()
            docs[code] = {
                "error_code": code,
                "error_type": etype,
                "error_name": ent_name.get(),
                "error_category": ent_cat.get(),
                "latest_version": "0",
                "created_at": datetime.now().isoformat(),
                "created_by": self.username
            }
            save_docs(docs)
            os.makedirs(os.path.join(VERSIONS_DIR, code), exist_ok=True)
            dlg.destroy()
            self.refresh_docs()
            messagebox.showinfo("OK","Documentation created")

        ttk.Button(dlg, text="Create", command=save).pack(pady=10)

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    LoginWindow()
