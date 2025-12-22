import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import ERROR_TYPES
from services.error_code_service import generate_error_code
from services.error_service import create_error

class CreateErrorWindow(tk.Toplevel):
    def __init__(self, master, current_user):
        super().__init__(master)
        self.current_user = current_user
        self.title("Create Documentation")
        self.geometry("800x600")

        # -------------------
        # Error Type
        # -------------------
        tk.Label(self, text="Error Type").pack(anchor="w")
        self.error_type_var = tk.StringVar()
        self.error_type_cb = ttk.Combobox(
            self,
            textvariable=self.error_type_var,
            values=list(ERROR_TYPES.keys()),
            state="readonly"
        )
        self.error_type_cb.pack(fill="x")

        # -------------------
        # Error Code (Auto)
        # -------------------
        tk.Label(self, text="Error Code").pack(anchor="w", pady=(10, 0))
        self.error_code_entry = tk.Entry(self, state="readonly")
        self.error_code_entry.pack(fill="x")

        self.error_type_cb.bind("<<ComboboxSelected>>", self.generate_code)

        # -------------------
        # Error Name
        # -------------------
        tk.Label(self, text="Error Name").pack(anchor="w", pady=(10, 0))
        self.name_entry = tk.Entry(self)
        self.name_entry.pack(fill="x")

        # -------------------
        # Error Category
        # -------------------
        tk.Label(self, text="Error Category").pack(anchor="w", pady=(10, 0))
        self.category_entry = tk.Entry(self)
        self.category_entry.pack(fill="x")

        # -------------------
        # Toolbar
        # -------------------
        toolbar = tk.Frame(self)
        toolbar.pack(fill="x", pady=5)

        tk.Button(toolbar, text="B", command=self.make_bold).pack(side="left")
        tk.Button(toolbar, text="I", command=self.make_italic).pack(side="left")
        tk.Button(toolbar, text="U", command=self.make_underline).pack(side="left")

        # -------------------
        # Content Editor
        # -------------------
        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill="both", expand=True)

        self.text.tag_configure("bold", font=("Arial", 10, "bold"))
        self.text.tag_configure("italic", font=("Arial", 10, "italic"))
        self.text.tag_configure("underline", font=("Arial", 10, "underline"))

        # -------------------
        # Save Button
        # -------------------
        tk.Button(self, text="Save", command=self.save).pack(pady=10)

    # -----------------------
    # Formatting
    # -----------------------
    def apply_tag(self, tag):
        try:
            start, end = self.text.tag_ranges(tk.SEL)
            self.text.tag_add(tag, start, end)
        except:
            pass

    def make_bold(self):
        self.apply_tag("bold")

    def make_italic(self):
        self.apply_tag("italic")

    def make_underline(self):
        self.apply_tag("underline")

    # -----------------------
    # Error Code Generator
    # -----------------------
    def generate_code(self, event=None):
        prefix = ERROR_TYPES[self.error_type_var.get()]
        code = generate_error_code(prefix)
        self.error_code_entry.config(state="normal")
        self.error_code_entry.delete(0, tk.END)
        self.error_code_entry.insert(0, code)
        self.error_code_entry.config(state="readonly")

    # -----------------------
    # Save Logic
    # -----------------------
    def serialize_content(self):
        content = ""
        index = "1.0"
        while index != self.text.index("end"):
            tags = self.text.tag_names(index)
            char = self.text.get(index)
            if "bold" in tags:
                content += f"<b>{char}</b>"
            elif "italic" in tags:
                content += f"<i>{char}</i>"
            elif "underline" in tags:
                content += f"<u>{char}</u>"
            else:
                content += char
            index = self.text.index(f"{index}+1c")
        return content

    def save(self):
        if not self.error_code_entry.get():
            messagebox.showerror("Error", "Error Type required")
            return

        create_error(
            self.error_code_entry.get(),
            ERROR_TYPES[self.error_type_var.get()],
            self.name_entry.get(),
            self.category_entry.get(),
            self.serialize_content(),
            self.current_user["username"]
        )

        messagebox.showinfo("Success", "Documentation created")
        self.destroy()
