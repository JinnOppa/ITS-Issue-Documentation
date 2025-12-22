import tkinter as tk
from tkinter import ttk, messagebox

from core.content_parser import parse_text_widget, blocks_to_json
from core.content_renderer import render_blocks
from core.storage import (
    load_errors,
    load_versions_by_error,
    save_new_version
)
from ui.create_error_window import CreateErrorWindow


class DocumentationTab(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user

        self.selected_error = None
        self.selected_version = None

        self.build_ui()
        self.load_error_list()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def build_ui(self):
        # ROOT GRID
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ================= LEFT =================
        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        tk.Label(left, text="Search Error Code").pack(anchor="w")
        self.search = tk.Entry(left)
        self.search.pack(fill="x", pady=2)

        tk.Label(left, text="Error Code List").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=30)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_error)

        tk.Button(
            left,
            text="Create New Error",
            command=self.open_create_error
        ).pack(fill="x", pady=2)
        tk.Button(left, text="Refresh", command=self.refresh_all).pack(fill="x")

        # ================= RIGHT =================
        right = tk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # -------- TOP META --------
        top = tk.Frame(right)
        top.grid(row=0, column=0, sticky="ew")

        self.lbl_create = self._meta(top, "Create Date", 0)
        self.lbl_update = self._meta(top, "Update Date", 1)
        self.lbl_code = self._meta(top, "Error Code", 2)
        self.lbl_name = self._meta(top, "Error Name", 3)
        self.lbl_category = self._meta(top, "Category", 4)

        tk.Label(top, text="Version").grid(row=5, column=0, sticky="w")
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            top, textvariable=self.version_var, state="readonly", width=12
        )
        self.version_combo.grid(row=5, column=1, sticky="w")
        self.version_combo.bind("<<ComboboxSelected>>", self.on_select_version)

        tk.Button(top, text="Logout").grid(row=0, column=3, rowspan=2, padx=10)

        # -------- CONTENT --------
        self.text = tk.Text(right, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew", pady=5)

        self.text.tag_config("bold", font=("Arial", 10, "bold"))
        self.text.tag_config("italic", font=("Arial", 10, "italic"))
        self.text.tag_config("underline", underline=1)

        # -------- ACTION --------
        action = tk.Frame(right)
        action.grid(row=2, column=0, sticky="e")

        tk.Button(action, text="Save Version", command=self.save_version).pack(side="left", padx=5)
        tk.Button(action, text="Delete Document").pack(side="left", padx=5)
        tk.Button(action, text="Delete Version").pack(side="left", padx=5)


    # def build_ui(self):
    #     self.columnconfigure(1, weight=1)
    #     self.rowconfigure(0, weight=1)

    #     # LEFT
    #     left = tk.Frame(self)
    #     left.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

    #     tk.Label(left, text="Error Code").pack(anchor="w")
    #     self.listbox = tk.Listbox(left, width=30)
    #     self.listbox.pack(fill="y", expand=True)
    #     self.listbox.bind("<<ListboxSelect>>", self.on_select_error)

    #     tk.Button(left, text="Refresh", command=self.refresh_all).pack(fill="x", pady=5)

    #     # RIGHT
    #     right = tk.Frame(self)
    #     right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    #     right.rowconfigure(1, weight=1)

    #     meta = tk.Frame(right)
    #     meta.grid(row=0, column=0, sticky="w")

    #     self.lbl_code = self._meta(meta, "Error Code", 0)
    #     self.lbl_name = self._meta(meta, "Name", 1)
    #     self.lbl_category = self._meta(meta, "Category", 2)
    #     self.lbl_create = self._meta(meta, "Create Date", 3)
    #     self.lbl_update = self._meta(meta, "Update Date", 4)

    #     tk.Label(meta, text="Version").grid(row=5, column=0, sticky="w")
    #     self.version_var = tk.StringVar()
    #     self.version_combo = ttk.Combobox(
    #         meta, textvariable=self.version_var, state="readonly", width=10
    #     )
    #     self.version_combo.grid(row=5, column=1, sticky="w")
    #     self.version_combo.bind("<<ComboboxSelected>>", self.on_select_version)

    #     # CONTENT
    #     self.text = tk.Text(right, wrap="word")
    #     self.text.grid(row=1, column=0, sticky="nsew", pady=5)

    #     # tags
    #     self.text.tag_config("bold", font=("Arial", 10, "bold"))
    #     self.text.tag_config("italic", font=("Arial", 10, "italic"))
    #     self.text.tag_config("underline", underline=1)

    #     action = tk.Frame(right)
    #     action.grid(row=2, column=0, sticky="e")

    #     tk.Button(action, text="Save Version", command=self.save_version).pack(side="left", padx=5)

    def _meta(self, parent, label, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        lbl = tk.Label(parent, text="-")
        lbl.grid(row=row, column=1, sticky="w")
        return lbl

    # --------------------------------------------------
    # DATA LOAD
    # --------------------------------------------------
    def load_error_list(self):
        self.listbox.delete(0, "end")
        self.errors = load_errors()

        for err in self.errors:
            self.listbox.insert("end", err["error_code"])

    def on_select_error(self, _):
        idx = self.listbox.curselection()
        if not idx:
            return

        self.selected_error = self.errors[idx[0]]
        self.load_versions()

    def load_versions(self):
        versions = load_versions_by_error(self.selected_error["error_code"])
        if not versions:
            return

        self.versions = versions
        version_nums = [v["version"] for v in versions]

        self.version_combo["values"] = version_nums
        self.version_combo.current(0)  # latest
        self.load_version(versions[0])

    def on_select_version(self, _):
        v = self.version_var.get()
        for ver in self.versions:
            if ver["version"] == v:
                self.load_version(ver)
                break

    def load_version(self, version_row):
        self.selected_version = version_row

        self.lbl_code.config(text=self.selected_error["error_code"])
        self.lbl_name.config(text=self.selected_error["error_name"])
        self.lbl_category.config(text=self.selected_error["error_category"])
        self.lbl_create.config(text=self.selected_error["created_at"])
        self.lbl_update.config(text=version_row["created_at"])

        render_blocks(self.text, version_row["content_json"])

    # --------------------------------------------------
    # ACTIONS
    # --------------------------------------------------
    def save_version(self):
        if not self.selected_error:
            messagebox.showwarning("Warning", "No error selected")
            return

        blocks = parse_text_widget(self.text)
        json_content = blocks_to_json(blocks)

        save_new_version(
            error_code=self.selected_error["error_code"],
            content_json=json_content,
            user=self.user["username"]
        )

        messagebox.showinfo("Saved", "New version saved")
        self.load_versions()

    def refresh_all(self):
        self.selected_error = None
        self.selected_version = None

        self.listbox.selection_clear(0, "end")
        self.version_combo.set("")

        for lbl in (
            self.lbl_code,
            self.lbl_name,
            self.lbl_category,
            self.lbl_create,
            self.lbl_update
        ):
            lbl.config(text="-")

        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

        self.load_error_list()

    def open_create_error(self):
        CreateErrorWindow(
            master=self,
            user=self.user,
            on_success=self.refresh_all
        )


# import tkinter as tk
# from tkinter import ttk, messagebox
# import csv

# from config.settings import ERRORS_MASTER_CSV, ERROR_VERSIONS_CSV
# from utils.datetime_utils import now
# from ui.create_error_window import CreateErrorWindow
# from ui.view_error_window import ViewErrorWindow

# class DocumentationTab(tk.Frame):
#     def __init__(self, master, user, logout_callback=None):
#         super().__init__(master)
#         self.user = user
#         self.logout_callback = logout_callback

#         self.selected_error_code = None
#         self.selected_version = None

#         self.build_ui()
#         self.load_error_list()

#     def build_ui(self):
#         self.grid_columnconfigure(1, weight=1)
#         self.grid_rowconfigure(2, weight=1)

#         # -------------------------------
#         # [11] Logout
#         # -------------------------------
#         tk.Button(self, text="Logout", command=self.logout).grid(
#             row=0, column=1, sticky="e", padx=10, pady=5
#         )

#         # -------------------------------
#         # [1] Search Error Code
#         # -------------------------------
#         self.search_var = tk.StringVar()
#         tk.Entry(self, textvariable=self.search_var).grid(
#             row=1, column=0, sticky="ew", padx=5
#         )
#         self.search_var.trace_add("write", lambda *_: self.load_error_list())

#         # -------------------------------
#         # [2] Error Code List
#         # -------------------------------
#         self.tree = ttk.Treeview(
#             self,
#             columns=("code",),
#             show="headings",
#             height=15
#         )
#         self.tree.heading("code", text="Error Code")
#         self.tree.grid(row=2, column=0, sticky="ns", padx=5)
#         self.tree.bind("<<TreeviewSelect>>", self.on_select_error)

#         # -------------------------------
#         # [3] Create Error
#         # -------------------------------
#         if self.user["role"] in ("IT_ADMIN", "IT_USER"):
#             tk.Button(
#                 self, text="Create Error",
#                 command=lambda: CreateErrorWindow(self, self.user)
#             ).grid(row=3, column=0, sticky="w", padx=5)

#         # -------------------------------
#         # [4] Refresh
#         # -------------------------------
#         tk.Button(
#             self, text="Refresh",
#             command=self.refresh_all
#         ).grid(row=3, column=0, sticky="e", padx=5)

#         # ===============================
#         # RIGHT PANEL
#         # ===============================
#         right = tk.Frame(self)
#         right.grid(row=1, column=1, rowspan=3, sticky="nsew", padx=10)
#         right.grid_columnconfigure(0, weight=1)
#         right.grid_rowconfigure(2, weight=1)

#         # -------------------------------
#         # [5]–[10] Metadata
#         # -------------------------------
#         meta = tk.Frame(right)
#         meta.grid(row=0, column=0, sticky="ew")

#         self.lbl_create = self.meta_label(meta, "Create Date", 0)
#         self.lbl_update = self.meta_label(meta, "Update Date", 1)
#         self.lbl_code = self.meta_label(meta, "Error Code", 2)
#         self.lbl_name = self.meta_label(meta, "Error Name", 3)
#         self.lbl_category = self.meta_label(meta, "Category", 4)
#         self.lbl_version = self.meta_label(meta, "Version", 5)

#         # -------------------------------
#         # [12] Content
#         # -------------------------------
#         self.text = tk.Text(right, wrap="word")
#         self.text.grid(row=2, column=0, sticky="nsew")
#         self.text.tag_config("b", font=("Arial", 10, "bold"))
#         self.text.tag_config("i", font=("Arial", 10, "italic"))
#         self.text.tag_config("u", underline=1)

#         # -------------------------------
#         # [13][14][15] Action Buttons
#         # -------------------------------
#         action = tk.Frame(right)
#         action.grid(row=3, column=0, sticky="e", pady=5)

#         if self.user["role"] in ("IT_ADMIN", "IT_USER"):
#             tk.Button(action, text="Save Version", command=self.save_version).pack(side="left", padx=5)
#             tk.Button(action, text="Delete Version", command=self.delete_version).pack(side="left", padx=5)

#         if self.user["role"] == "IT_ADMIN":
#             tk.Button(action, text="Delete Document", command=self.delete_document).pack(side="left", padx=5)

#     def refresh_all(self):
#         # Reset selected state
#         self.selected_error_code = None
#         self.selected_version = None

#         # Reload error list
#         self.load_error_list()

#         # Clear metadata labels
#         for lbl in (
#             self.lbl_create,
#             self.lbl_update,
#             self.lbl_code,
#             self.lbl_name,
#             self.lbl_category,
#             self.lbl_version
#         ):
#             lbl.config(text="-")

#         # Clear content
#         self.text.config(state="normal")
#         self.text.delete("1.0", "end")
#         self.text.config(state="disabled")


#     def meta_label(self, parent, title, col):
#         frame = tk.Frame(parent)
#         frame.grid(row=0, column=col, padx=5)
#         tk.Label(frame, text=title, fg="gray").pack()
#         lbl = tk.Label(frame, text="-", font=("Arial", 10, "bold"))
#         lbl.pack()
#         return lbl
    
#     def load_error_list(self):
#         keyword = self.search_var.get().lower()
#         self.tree.delete(*self.tree.get_children())

#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["is_active"] != "True":
#                     continue
#                 if keyword and keyword not in r["error_code"].lower():
#                     continue
#                 self.tree.insert("", "end", values=(r["error_code"],))

#     def on_select_error(self, _):
#         item = self.tree.focus()
#         if not item:
#             return

#         self.selected_error_code = self.tree.item(item)["values"][0]
#         self.load_metadata()
#         self.load_latest_content()

#     def load_metadata(self):
#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code:
#                     self.lbl_create.config(text=r["create_date"])
#                     self.lbl_code.config(text=r["error_code"])
#                     self.lbl_name.config(text=r["error_name"])
#                     self.lbl_category.config(text=r["error_category"])
#                     self.lbl_version.config(text=r["latest_version"])

#     def load_latest_content(self):
#         self.text.config(state="normal")
#         self.text.delete("1.0", "end")

#         latest = None
#         with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code and r["is_active"] == "True":
#                     latest = r

#         if latest:
#             self.lbl_update.config(text=latest["created_at"])
#             self.render_content(latest["content"])

#         self.text.config(state="disabled")

#     def save_version(self):
#         if not self.selected_error_code:
#             messagebox.showwarning("Warning", "Select an error first")
#             return

#         content = self.text.get("1.0", "end").strip()
#         if not content:
#             messagebox.showwarning("Warning", "Content cannot be empty")
#             return

#         # Get latest version number
#         latest_version = 0
#         rows = []

#         with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             for r in reader:
#                 rows.append(r)
#                 if r["error_code"] == self.selected_error_code:
#                     latest_version = max(latest_version, int(r["version"]))

#         new_version = latest_version + 1

#         rows.append({
#             "error_code": self.selected_error_code,
#             "version": str(new_version),
#             "content": content,
#             "created_at": now(),
#             "created_by": self.user["username"],
#             "is_active": "True"
#         })

#         with open(ERROR_VERSIONS_CSV, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(
#                 f,
#                 fieldnames=rows[0].keys()
#             )
#             writer.writeheader()
#             writer.writerows(rows)

#         # Update latest_version in master
#         self.update_latest_version(new_version)

#         self.load_latest_content()
#         messagebox.showinfo("Success", f"Version {new_version} saved")

#     def delete_version(self):
#         if not self.selected_error_code:
#             messagebox.showwarning("Warning", "Select an error first")
#             return

#         versions = []
#         with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code and r["is_active"] == "True":
#                     versions.append(r["version"])

#         if not versions:
#             messagebox.showinfo("Info", "No versions to delete")
#             return

#         win = tk.Toplevel(self)
#         win.title("Delete Version")

#         tk.Label(win, text="Select Version").pack(padx=10, pady=5)
#         cb = ttk.Combobox(win, values=versions, state="readonly")
#         cb.pack(padx=10)

#         def confirm():
#             selected = cb.get()
#             rows = []

#             with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#                 for r in csv.DictReader(f):
#                     if (
#                         r["error_code"] == self.selected_error_code
#                         and r["version"] == selected
#                     ):
#                         r["is_active"] = "False"
#                     rows.append(r)

#             with open(ERROR_VERSIONS_CSV, "w", newline="", encoding="utf-8") as f:
#                 writer = csv.DictWriter(f, fieldnames=rows[0].keys())
#                 writer.writeheader()
#                 writer.writerows(rows)

#             win.destroy()
#             self.load_latest_content()

#         tk.Button(win, text="Delete", command=confirm).pack(pady=5)


#     def delete_document(self):
#         if not self.selected_error_code:
#             return

#         if not messagebox.askyesno(
#             "Confirm",
#             f"Delete entire document {self.selected_error_code}?"
#         ):
#             return

#         # Disable master
#         master_rows = []
#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code:
#                     r["is_active"] = "False"
#                 master_rows.append(r)

#         with open(ERRORS_MASTER_CSV, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=master_rows[0].keys())
#             writer.writeheader()
#             writer.writerows(master_rows)

#         # Disable all versions
#         version_rows = []
#         with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code:
#                     r["is_active"] = "False"
#                 version_rows.append(r)

#         with open(ERROR_VERSIONS_CSV, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=version_rows[0].keys())
#             writer.writeheader()
#             writer.writerows(version_rows)

#         self.refresh_all()


#     def update_latest_version(self, version):
#         rows = []
#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == self.selected_error_code:
#                     r["latest_version"] = str(version)
#                 rows.append(r)

#         with open(ERRORS_MASTER_CSV, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=rows[0].keys())
#             writer.writeheader()
#             writer.writerows(rows)

#         self.lbl_version.config(text=str(version))
#         self.lbl_update.config(text=now())


#     def logout(self):
#         if self.logout_callback:
#             self.logout_callback()


# import tkinter as tk
# from tkinter import ttk, messagebox
# import csv
# from config.settings import ERRORS_MASTER_CSV, ERROR_VERSIONS_CSV
# from ui.create_error_window import CreateErrorWindow
# from ui.view_error_window import ViewErrorWindow

# class DocumentationTab(tk.Frame):
#     def __init__(self, master, user):
#         super().__init__(master)
#         self.user = user

#         # -------------------
#         # Toolbar
#         # -------------------
#         toolbar = tk.Frame(self)
#         toolbar.pack(fill="x", pady=5)

#         if user["role"] in ("IT_ADMIN", "IT_USER"):
#             tk.Button(
#                 toolbar,
#                 text="Create Documentation",
#                 command=lambda: CreateErrorWindow(self, user)
#             ).pack(side="left")

#         tk.Button(toolbar, text="Refresh", command=self.load_data).pack(side="left")

#         if user["role"] in ("IT_ADMIN", "IT_USER"):
#             tk.Button(toolbar, text="Delete Version", command=self.delete_version).pack(side="right")
#         tk.Button(toolbar, text="View", command=self.view_error).pack(side="left")

#         if user["role"] == "IT_ADMIN":
#             tk.Button(toolbar, text="Delete Error", command=self.delete_error).pack(side="right")

#         # -------------------
#         # Table
#         # -------------------
#         self.tree = ttk.Treeview(
#             self,
#             columns=("code", "type", "created"),
#             show="headings"
#         )
#         self.tree.heading("code", text="Error Code")
#         self.tree.heading("type", text="Error Type")
#         self.tree.heading("created", text="Created Date")
#         self.tree.pack(fill="both", expand=True)

#         self.load_data()

#     def load_data(self):
#         self.tree.delete(*self.tree.get_children())

#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 if row["is_active"] == "True":
#                     self.tree.insert("", "end", values=(
#                         row["error_code"],
#                         row["error_type"],
#                         row["create_date"]
#                     ))

#     def delete_error(self):
#         selected = self.tree.focus()
#         if not selected:
#             return

#         error_code = self.tree.item(selected)["values"][0]

#         if not messagebox.askyesno(
#             "Confirm Delete",
#             f"Delete ALL versions of {error_code}?"
#         ):
#             return

#         rows = []
#         with open(ERRORS_MASTER_CSV, newline="", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             for r in reader:
#                 if r["error_code"] == error_code:
#                     r["is_active"] = "False"
#                 rows.append(r)

#         with open(ERRORS_MASTER_CSV, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=rows[0].keys())
#             writer.writeheader()
#             writer.writerows(rows)

#         self.load_data()

#     def view_error(self):
#         selected = self.tree.focus()
#         if not selected:
#             return
#         error_code = self.tree.item(selected)["values"][0]
#         ViewErrorWindow(self, error_code)

#     def delete_version(self):
#         selected = self.tree.focus()
#         if not selected:
#             return

#         error_code = self.tree.item(selected)["values"][0]

#         win = tk.Toplevel(self)
#         win.title("Delete Version")

#         tk.Label(win, text="Select Version").pack()

#         versions = []
#         with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#             for r in csv.DictReader(f):
#                 if r["error_code"] == error_code and r["is_active"] == "True":
#                     versions.append(r["version"])

#         cb = ttk.Combobox(win, values=versions, state="readonly")
#         cb.pack()

#         def confirm():
#             rows = []
#             with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
#                 for r in csv.DictReader(f):
#                     if r["error_code"] == error_code and r["version"] == cb.get():
#                         r["is_active"] = "False"
#                     rows.append(r)

#             with open(ERROR_VERSIONS_CSV, "w", newline="", encoding="utf-8") as f:
#                 writer = csv.DictWriter(f, fieldnames=rows[0].keys())
#                 writer.writeheader()
#                 writer.writerows(rows)

#             win.destroy()

#         tk.Button(win, text="Delete", command=confirm).pack()

        
