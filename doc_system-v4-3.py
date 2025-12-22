"""
doc_system_v6_clickable.py
NEXT STEP:
- Full Documentation actions (clickable)
- Version control UI
"""

import os, csv, json
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
        "doc": ["create","view","update","delete","delete_version"]
    },
    "it_user": {
        "doc": ["create","view","update","delete_version"]
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
        with open(DOCS_CSV,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([
                "error_code","error_type","error_name",
                "error_category","latest_version",
                "created_at","created_by"
            ])

    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV,"w",newline="",encoding="utf-8") as f:
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

def load_docs():
    with open(DOCS_CSV,newline="",encoding="utf-8") as f:
        return {r["error_code"]:r for r in csv.DictReader(f)}

def save_docs(docs):
    with open(DOCS_CSV,"w",newline="",encoding="utf-8") as f:
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
    for c in load_docs():
        if c.startswith(prefix):
            try: nums.append(int(c[len(prefix):]))
            except: pass
    return f"{prefix}{max(nums,default=0)+1:04d}"

def version_path(code, v):
    return os.path.join(VERSIONS_DIR, code, f"v{v}", "data.json")

def load_users():
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        return {r["username"]: r for r in csv.DictReader(f)}
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
        self.u.pack(fill="x",padx=20)

        ttk.Label(self.root,text="Password").pack()
        self.p = ttk.Entry(self.root,show="*")
        self.p.pack(fill="x",padx=20)

        ttk.Button(self.root,text="Login",command=self.login).pack(pady=10)
        self.root.mainloop()

    def login(self):
        users = load_users()
        username = self.u.get()
        password = self.p.get()

        if username in users and users[username]["password"] == password:
            role = users[username]["role"]

            self.root.destroy()   # destroy SETELAH data diambil
            AppMain(role, username)
        else:
            messagebox.showerror("Error", "Invalid login")

    # def login(self):
    #     with open(USERS_CSV,newline="",encoding="utf-8") as f:
    #         users = {r["username"]:r for r in csv.DictReader(f)}
    #     if self.u.get() in users and users[self.u.get()]["password"] == self.p.get():
    #         self.root.destroy()
    #         AppMain(users[self.u.get()]["role"], self.u.get())
    #     else:
    #         messagebox.showerror("Error","Invalid login")

# ======================================================
# MAIN APP
# ======================================================
class AppMain:
    def __init__(self, role, username):
        self.role = role
        self.username = username
        self.current_code = None
        self.current_version = None

        self.root = tk.Tk()
        self.root.title(f"Documentation System ({role})")
        self.root.geometry("1200x750")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both",expand=True)

        self.build_doc_tab()
        self.root.mainloop()

    # --------------------------------------------------
    # DOCUMENTATION TAB
    # --------------------------------------------------
    def build_doc_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab,text="Documentation")

        left = ttk.Frame(tab,width=320)
        left.pack(side="left",fill="y")

        right = ttk.Frame(tab)
        right.pack(side="left",fill="both",expand=True)

        ttk.Label(left,text="Documentation",font=("Arial",12,"bold")).pack()
        self.lst = tk.Listbox(left,width=40)
        self.lst.pack(fill="y",expand=True)
        self.lst.bind("<<ListboxSelect>>", self.select_doc)

        ttk.Button(left,text="Refresh",command=self.refresh_docs).pack(pady=3)

        if has_perm(self.role,"doc","create"):
            ttk.Button(left,text="➕ Create Documentation",command=self.create_doc).pack(pady=3)

        # -------- RIGHT TOP (META) --------
        meta = ttk.Frame(right)
        meta.pack(fill="x")

        self.lbl_meta = ttk.Label(meta,text="No document selected")
        self.lbl_meta.pack(side="left",padx=5)

        self.cb_version = ttk.Combobox(meta,state="readonly",width=10)
        self.cb_version.pack(side="right",padx=5)
        self.cb_version.bind("<<ComboboxSelected>>", self.load_version)

        # -------- CONTENT --------
        self.txt = ScrolledText(right)
        self.txt.pack(fill="both",expand=True)

        # -------- BUTTON BAR --------
        bar = ttk.Frame(right)
        bar.pack(fill="x",pady=4)

        if has_perm(self.role,"doc","update"):
            ttk.Button(bar,text="💾 Save New Version",command=self.save_version).pack(side="left",padx=4)
            ttk.Button(bar,text="✏️ Edit Metadata",command=self.edit_metadata).pack(side="left",padx=4)

        if has_perm(self.role,"doc","delete_version"):
            ttk.Button(bar,text="🗑️ Delete Version",command=self.delete_version).pack(side="left",padx=4)

        if has_perm(self.role,"doc","delete"):
            ttk.Button(bar,text="❌ Delete Documentation",command=self.delete_doc).pack(side="right",padx=4)

        self.refresh_docs()

    # --------------------------------------------------
    # DOC ACTIONS
    # --------------------------------------------------
    def refresh_docs(self):
        self.docs = load_docs()
        self.lst.delete(0,"end")
        for d in self.docs.values():
            self.lst.insert("end", f'{d["error_code"]} - {d["error_name"]}')

    def select_doc(self, e):
        sel = self.lst.curselection()
        if not sel: return
        self.current_code = self.lst.get(sel[0]).split(" - ")[0]
        doc = self.docs[self.current_code]

        self.lbl_meta.config(
            text=f'{doc["error_code"]} | {doc["error_type"]} | {doc["error_name"]}'
        )

        versions = []
        base = os.path.join(VERSIONS_DIR, self.current_code)
        if os.path.exists(base):
            for d in os.listdir(base):
                if d.startswith("v"):
                    versions.append(d)
        versions.sort()

        self.cb_version["values"] = versions
        if versions:
            self.cb_version.set(versions[-1])
            self.load_version()

    def load_version(self, e=None):
        v = self.cb_version.get().lstrip("v")
        self.current_version = int(v)
        path = version_path(self.current_code, self.current_version)
        self.txt.delete("1.0","end")
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f:
                data = json.load(f)
            self.txt.insert("end", data.get("content",""))
        else:
            self.txt.insert("end","(empty version)")

    def save_version(self):
        if not self.current_code:
            messagebox.showerror("Error","Select document")
            return

        docs = load_docs()
        doc = docs[self.current_code]

        new_v = int(doc["latest_version"]) + 1
        doc["latest_version"] = str(new_v)
        save_docs(docs)

        folder = os.path.join(VERSIONS_DIR,self.current_code,f"v{new_v}")
        os.makedirs(folder,exist_ok=True)

        with open(version_path(self.current_code,new_v),"w",encoding="utf-8") as f:
            json.dump({
                "version": new_v,
                "content": self.txt.get("1.0","end").strip(),
                "updated_at": datetime.now().isoformat(),
                "updated_by": self.username
            }, f, indent=2)

        messagebox.showinfo("Saved",f"Version v{new_v} saved")
        self.refresh_docs()
        self.select_doc(None)

    def delete_version(self):
        if not self.current_code or not self.current_version:
            return

        docs = load_docs()
        latest = int(docs[self.current_code]["latest_version"])
        if self.current_version == latest:
            messagebox.showerror("Blocked","Cannot delete latest version")
            return

        path = os.path.join(VERSIONS_DIR,self.current_code,f"v{self.current_version}")
        if messagebox.askyesno("Confirm",f"Delete version v{self.current_version}?"):
            import shutil
            shutil.rmtree(path)
            messagebox.showinfo("Deleted","Version deleted")
            self.select_doc(None)

    def delete_doc(self):
        if not self.current_code:
            return
        if not messagebox.askyesno("Confirm","Delete entire documentation?"):
            return

        docs = load_docs()
        docs.pop(self.current_code,None)
        save_docs(docs)

        shutil.rmtree(os.path.join(VERSIONS_DIR,self.current_code),ignore_errors=True)
        self.current_code = None
        self.txt.delete("1.0","end")
        self.refresh_docs()

    def edit_metadata(self):
        if not self.current_code:
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Edit Metadata")
        dlg.geometry("400x250")

        doc = self.docs[self.current_code]

        ttk.Label(dlg,text="Error Name").pack()
        ent_name = ttk.Entry(dlg)
        ent_name.insert(0,doc["error_name"])
        ent_name.pack(fill="x",padx=10)

        ttk.Label(dlg,text="Category").pack()
        ent_cat = ttk.Entry(dlg)
        ent_cat.insert(0,doc["error_category"])
        ent_cat.pack(fill="x",padx=10)

        def save():
            docs = load_docs()
            docs[self.current_code]["error_name"] = ent_name.get()
            docs[self.current_code]["error_category"] = ent_cat.get()
            save_docs(docs)
            dlg.destroy()
            self.refresh_docs()

        ttk.Button(dlg,text="Save",command=save).pack(pady=10)

    def create_doc(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Documentation")
        dlg.geometry("520x500")

        ttk.Label(dlg,text="Error Type").pack(anchor="w",padx=10)
        cb = ttk.Combobox(dlg,values=list(ERROR_TYPES.keys()),state="readonly")
        cb.pack(fill="x",padx=10)

        ttk.Label(dlg,text="Error Name").pack(anchor="w",padx=10)
        en = ttk.Entry(dlg)
        en.pack(fill="x",padx=10)

        ttk.Label(dlg,text="Category").pack(anchor="w",padx=10)
        ec = ttk.Entry(dlg)
        ec.pack(fill="x",padx=10)

        lbl_code = ttk.Label(dlg,text="Error Code: -")
        lbl_code.pack(pady=5)

        cb.bind("<<ComboboxSelected>>",
            lambda e: lbl_code.config(
                text=f"Error Code: {generate_error_code(cb.get())}"
            )
        )

        ttk.Label(dlg,text="Content (Version 1)").pack(anchor="w",padx=10,pady=(10,0))
        txt = ScrolledText(dlg,height=10)
        txt.pack(fill="both",expand=True,padx=10)

        def save():
            if not cb.get():
                messagebox.showerror("Error","Select Error Type")
                return

            code = lbl_code.cget("text").split(": ")[1]
            docs = load_docs()

            docs[code] = {
                "error_code": code,
                "error_type": cb.get(),
                "error_name": en.get(),
                "error_category": ec.get(),
                "latest_version": "1",
                "created_at": datetime.now().isoformat(),
                "created_by": self.username
            }
            save_docs(docs)

            # create version 1
            folder = os.path.join(VERSIONS_DIR,code,"v1")
            os.makedirs(folder,exist_ok=True)

            with open(version_path(code,1),"w",encoding="utf-8") as f:
                json.dump({
                    "version": 1,
                    "content": txt.get("1.0","end").strip(),
                    "updated_at": datetime.now().isoformat(),
                    "updated_by": self.username
                }, f, indent=2)

            dlg.destroy()
            self.refresh_docs()
            messagebox.showinfo("Created","Documentation created with Version 1")

        ttk.Button(dlg,text="Create Documentation",command=save).pack(pady=10)


    # def create_doc(self):
    #     dlg = tk.Toplevel(self.root)
    #     dlg.title("Create Documentation")
    #     dlg.geometry("420x300")

    #     ttk.Label(dlg,text="Error Type").pack(anchor="w",padx=8)
    #     cb = ttk.Combobox(dlg,values=list(ERROR_TYPES.keys()),state="readonly")
    #     cb.pack(fill="x",padx=8)

    #     ttk.Label(dlg,text="Error Name").pack(anchor="w",padx=8)
    #     en = ttk.Entry(dlg)
    #     en.pack(fill="x",padx=8)

    #     ttk.Label(dlg,text="Category").pack(anchor="w",padx=8)
    #     ec = ttk.Entry(dlg)
    #     ec.pack(fill="x",padx=8)

    #     lbl = ttk.Label(dlg,text="Error Code: -")
    #     lbl.pack(pady=8)

    #     cb.bind("<<ComboboxSelected>>",
    #         lambda e: lbl.config(text=f"Error Code: {generate_error_code(cb.get())}")
    #     )

    #     def save():
    #         code = lbl.cget("text").split(": ")[1]
    #         docs = load_docs()
    #         docs[code] = {
    #             "error_code": code,
    #             "error_type": cb.get(),
    #             "error_name": en.get(),
    #             "error_category": ec.get(),
    #             "latest_version": "0",
    #             "created_at": datetime.now().isoformat(),
    #             "created_by": self.username
    #         }
    #         save_docs(docs)
    #         os.makedirs(os.path.join(VERSIONS_DIR,code),exist_ok=True)
    #         dlg.destroy()
    #         self.refresh_docs()

    #     ttk.Button(dlg,text="Create",command=save).pack(pady=10)

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    LoginWindow()
