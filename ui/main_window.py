import tkinter as tk
from tkinter import ttk
from ui.documentation_tab import DocumentationTab
from ui.user_management_tab import UserManagementTab

class MainWindow(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.pack(fill="both", expand=True)

        tk.Label(
            self,
            text=f"Logged in as {user['username']} ({user['role']})",
            font=("Arial", 14)
        ).pack(pady=10)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # -----------------------
        # Documentation Tab
        # -----------------------
        doc_tab = DocumentationTab(notebook, user)
        notebook.add(doc_tab, text="Documentation")

        # -----------------------
        # User Management Tab
        # -----------------------
        if user["role"] == "IT_ADMIN":
            user_tab = UserManagementTab(notebook, user)
            notebook.add(user_tab, text="User Management")


# import tkinter as tk
# from ui.create_error_window import CreateErrorWindow

# class MainWindow(tk.Frame):
#     def __init__(self, master, user):
#         super().__init__(master)
#         self.user = user
#         self.pack(fill="both", expand=True)

#         tk.Label(
#             self,
#             text=f"Logged in as {user['username']} ({user['role']})",
#             font=("Arial", 14)
#         ).pack(pady=20)

#         tk.Label(
#             self,
#             text="(Next step: documentation UI & rich editor)",
#             fg="gray"
#         ).pack()

#         if self.user["role"] in ("IT_ADMIN", "IT_USER"):
#             tk.Button(
#                 self,
#                 text="Create Documentation",
#                 command=lambda: CreateErrorWindow(self, self.user)
#             ).pack()

