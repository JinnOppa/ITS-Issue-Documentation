"""
doc_system_v5.py
- 2 Tabs: Documentation & User Management
- Roles: it_admin, it_user, user
"""

import os, csv, json, shutil
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
DATA_DIR = "data"
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
DOCS_CSV = os.path.join(DATA_DIR, "documentation.csv")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")

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
        "user": ["create","update","delete","assign_any"]
    },
    "it_user": {
        "doc": ["create","view","update","delete_version"],
        "user": ["create","update","delete","assign_user_only"]
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
            csv.writer(f).writerow([
                "error_code","error_type","error_name",
                "error_category","latest_version",
                "created_at","created_by"
            ])

    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["username","password","role"])
            w.writerow(["admin","admin","it_admin"])
            w.writerow(["ituser","ituser","it_user"])
            w.writerow(["viewer","viewer","user"])

ensure_files()

# ======================================================
# HELPERS
# ======================================================
def has_perm(role, domain, action):
    return action in PERMISSIONS.get(role, {}).get(domain, [])

def load_users():
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        return {r["username"]: r for r in csv.DictReader(f)}

def save_users(users):
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["username","password","role"])
        for u in users.values():
            w.writerow([u["username"],u["password"],u["role"]])

def load_docs():
    with open(DOCS_CSV, newline="", encoding="utf-8") as f:
        return {r["error_code"]: r for r in csv.DictReader(f)}

def save_docs(docs):
    with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "error_code","error_type","error_name",
            "error_category","latest_version",
            "created_at","created_by"
        ])
        for d in docs.values():
            w.writerow([
                d["error_code"], d["error_type"], d["error_name"],
                d["error_category"], d["latest_version"],
                d["created_at"], d["created_by"]
            ])

def generate_error_code(error_type):
    prefix = ERROR_TYPES[error_type]
    nums = []
    for code in load_docs().keys():
        if code.startswith(prefix):
            try: nums.append(int(code[len(prefix):]))
            except: pass
    return f"{prefix}{max(nums, default=0)+1:04d}"

# ======================================================
# LOGIN
# ======================================================
class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("300x200")

        ttk.Label(self.root,text="Username").pack()
        self.u = ttk.Entry(self.root)
        self.u.pack(fill="x", padx=20)

        ttk.Label(self.root,text="Password").pack()
        self.p = ttk.Entry(self.root, show="*")
        self.p.pack(fill="x", padx=20)

        ttk.Button(self.root,text="Login",command=self.login).pack(pady=10)
        self.root.mainloop()

    def login(self):
        users = load_users()
        u,p = self.u.get(), self.p.get()
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

        self.root = tk.Tk()
        self.root.title(f"Documentation System ({role})")
        self.root.geometry("1100x700")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True)

        self.build_doc_tab()

        if has_perm(role,"user","create"):
            self.build_user_tab()

        self.root.mainloop()

    # --------------------------------------------------
    # DOCUMENTATION TAB
    # --------------------------------------------------
    def build_doc_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Documentation")

        left = ttk.Frame(tab, width=300)
        left.pack(side="left", fill="y")

        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left,text="Documentation",font=("Arial",12,"bold")).pack()
        self.lst_docs = tk.Listbox(left,width=40)
        self.lst_docs.pack(fill="y", expand=True)

        ttk.Button(left,text="Refresh",command=self.refresh_docs).pack(pady=4)

        if has_perm(self.role,"doc","create"):
            ttk.Button(left,text="Create Documentation",
                       command=self.create_doc).pack(pady=4)

        self.viewer = ScrolledText(right)
        self.viewer.pack(fill="both", expand=True)

        self.refresh_docs()

    def refresh_docs(self):
        self.lst_docs.delete(0,"end")
        self.docs = load_docs()
        for d in self.docs.values():
            self.lst_docs.insert(
                "end",
                f'{d["error_code"]} - {d["error_name"]}'
            )

    def create_doc(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Documentation")
        dlg.geometry("420x300")

        ttk.Label(dlg,text="Error Type").pack(anchor="w",padx=8)
        cb_type = ttk.Combobox(
            dlg,values=list(ERROR_TYPES.keys()),state="readonly"
        )
        cb_type.pack(fill="x",padx=8)

        ttk.Label(dlg,text="Error Name").pack(anchor="w",padx=8)
        ent_name = ttk.Entry(dlg)
        ent_name.pack(fill="x",padx=8)

        ttk.Label(dlg,text="Category").pack(anchor="w",padx=8)
        ent_cat = ttk.Entry(dlg)
        ent_cat.pack(fill="x",padx=8)

        lbl_code = ttk.Label(dlg,text="Error Code: -")
        lbl_code.pack(pady=8)

        def on_select(e):
            lbl_code.config(
                text=f"Error Code: {generate_error_code(cb_type.get())}"
            )
        cb_type.bind("<<ComboboxSelected>>", on_select)

        def save():
            if not cb_type.get():
                messagebox.showerror("Error","Select Error Type")
                return
            code = lbl_code.cget("text").split(": ")[1]
            docs = load_docs()
            docs[code] = {
                "error_code": code,
                "error_type": cb_type.get(),
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

        ttk.Button(dlg,text="Create",command=save).pack(pady=12)

    # --------------------------------------------------
    # USER MANAGEMENT TAB
    # --------------------------------------------------
    def build_user_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="User Management")

        left = ttk.Frame(tab, width=300)
        left.pack(side="left", fill="y")

        right = ttk.Frame(tab)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left,text="Users",font=("Arial",12,"bold")).pack()
        self.lst_users = tk.Listbox(left)
        self.lst_users.pack(fill="y", expand=True)

        ttk.Button(left,text="Refresh",command=self.refresh_users).pack(pady=4)
        ttk.Button(left,text="Create User",command=self.create_user).pack(pady=4)
        ttk.Button(left,text="Delete User",command=self.delete_user).pack(pady=4)

        self.user_info = ScrolledText(right, state="disabled")
        self.user_info.pack(fill="both", expand=True)

        self.refresh_users()

    def refresh_users(self):
        self.lst_users.delete(0,"end")
        self.users = load_users()
        for u in self.users.values():
            self.lst_users.insert("end", f'{u["username"]} ({u["role"]})')

    def create_user(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create User")
        dlg.geometry("350x250")

        ttk.Label(dlg,text="Username").pack()
        ent_u = ttk.Entry(dlg)
        ent_u.pack(fill="x", padx=10)

        ttk.Label(dlg,text="Password").pack()
        ent_p = ttk.Entry(dlg)
        ent_p.pack(fill="x", padx=10)

        ttk.Label(dlg,text="Role").pack()
        roles = ["user"]
        if self.role == "it_admin":
            roles = ["user","it_user","it_admin"]
        cb_role = ttk.Combobox(dlg,values=roles,state="readonly")
        cb_role.pack(fill="x", padx=10)

        def save():
            users = load_users()
            u = ent_u.get()
            if u in users:
                messagebox.showerror("Error","User exists")
                return
            users[u] = {
                "username": u,
                "password": ent_p.get(),
                "role": cb_role.get()
            }
            save_users(users)
            dlg.destroy()
            self.refresh_users()

        ttk.Button(dlg,text="Create",command=save).pack(pady=10)

    def delete_user(self):
        sel = self.lst_users.curselection()
        if not sel:
            return
        uname = self.lst_users.get(sel[0]).split(" ")[0]
        if uname == self.username:
            messagebox.showerror("Error","Cannot delete yourself")
            return
        users = load_users()
        users.pop(uname,None)
        save_users(users)
        self.refresh_users()

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    LoginWindow()
