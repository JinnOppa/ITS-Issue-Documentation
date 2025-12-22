import tkinter as tk
from tkinter import ttk, messagebox
import csv
from config.settings import USERS_CSV, ROLES
from utils.security import hash_password
from utils.datetime_utils import now

class UserManagementTab(tk.Frame):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.current_user = current_user

        # -------------------
        # Toolbar
        # -------------------
        toolbar = tk.Frame(self)
        toolbar.pack(fill="x", pady=5)

        tk.Button(toolbar, text="Create User", command=self.create_user).pack(side="left")
        tk.Button(toolbar, text="Disable User", command=self.disable_user).pack(side="right")

        # -------------------
        # Table
        # -------------------
        self.tree = ttk.Treeview(
            self,
            columns=("username", "role", "active"),
            show="headings"
        )
        self.tree.heading("username", text="Username")
        self.tree.heading("role", text="Role")
        self.tree.heading("active", text="Active")
        self.tree.pack(fill="both", expand=True)

        self.load_users()

    def load_users(self):
        self.tree.delete(*self.tree.get_children())
        with open(USERS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.tree.insert("", "end", values=(
                    row["username"],
                    row["role"],
                    row["is_active"]
                ))

    def create_user(self):
        win = tk.Toplevel(self)
        win.title("Create User")

        tk.Label(win, text="Username").grid(row=0, column=0)
        tk.Label(win, text="Password").grid(row=1, column=0)
        tk.Label(win, text="Role").grid(row=2, column=0)

        u = tk.Entry(win)
        p = tk.Entry(win, show="*")
        r = ttk.Combobox(win, values=ROLES, state="readonly")

        u.grid(row=0, column=1)
        p.grid(row=1, column=1)
        r.grid(row=2, column=1)

        def save():
            with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    u.get(),
                    hash_password(p.get()),
                    r.get(),
                    now(),
                    self.current_user["username"],
                    "True"
                ])
            win.destroy()
            self.load_users()

        tk.Button(win, text="Save", command=save).grid(row=3, columnspan=2)

    def disable_user(self):
        selected = self.tree.focus()
        if not selected:
            return

        username = self.tree.item(selected)["values"][0]

        rows = []
        with open(USERS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r["username"] == username:
                    r["is_active"] = "False"
                rows.append(r)

        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        self.load_users()
