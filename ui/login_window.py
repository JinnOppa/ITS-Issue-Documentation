import tkinter as tk
from tkinter import messagebox
from services.auth_service import authenticate

class LoginWindow(tk.Frame):
    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.pack(padx=30, pady=30)

        tk.Label(self, text="Username").grid(row=0, column=0)
        tk.Label(self, text="Password").grid(row=1, column=0)

        self.u = tk.Entry(self)
        self.p = tk.Entry(self, show="*")
        self.u.grid(row=0, column=1)
        self.p.grid(row=1, column=1)

        tk.Button(self, text="Login", command=self.login).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def login(self):
        user = authenticate(self.u.get(), self.p.get())
        if not user:
            messagebox.showerror("Error", "Login failed")
            return
        self.callback(user)
