import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import os, csv, json
from PIL import ImageGrab, Image


# -------------------------------------------------
#              FILE & FOLDER SETUP
# -------------------------------------------------
DATA_DIR = "data"
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
DOC_CSV = os.path.join(DATA_DIR, "documentation.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "comments.csv")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")


def init_system():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Documentation CSV
    if not os.path.exists(DOC_CSV):
        with open(DOC_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["error_code", "title", "latest_version", "created_by", "created_at"])

    # Comments CSV
    if not os.path.exists(COMMENTS_CSV):
        with open(COMMENTS_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["error_code", "version", "user", "comment", "date"])

    # Users CSV
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password", "role"])
            writer.writerow(["admin", "123", "admin"])
            writer.writerow(["user", "123", "user"])


init_system()


# -------------------------------------------------
#              DATA HELPERS
# -------------------------------------------------
def load_docs():
    docs = {}
    with open(DOC_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            docs[row["error_code"]] = row
    return docs


def save_doc_row(row):
    docs = load_docs()
    docs[row["error_code"]] = row

    with open(DOC_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["error_code", "title", "latest_version", "created_by", "created_at"])
        for d in docs.values():
            writer.writerow([d["error_code"], d["title"], d["latest_version"], d["created_by"], d["created_at"]])


def load_version(error_code, version):
    path = os.path.join(VERSIONS_DIR, error_code, f"v{version}.json")
    if not os.path.exists(path):
        return {"content": []}
    with open(path) as f:
        return json.load(f)


def save_version(error_code, version, content, updated_by):
    folder = os.path.join(VERSIONS_DIR, error_code)
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"v{version}.json")
    data = {
        "version": version,
        "content": content,
        "updated_by": updated_by
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------------------------------
#                    LOGIN WINDOW
# -------------------------------------------------
class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("350x200")

        tk.Label(self.root, text="Username").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()

        tk.Label(self.root, text="Password").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Login", command=self.do_login).pack(pady=15)

        self.root.mainloop()

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        with open(USERS_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username and row["password"] == password:
                    self.root.destroy()
                    DocumentationApp(role=row["role"], username=username)
                    return

        messagebox.showerror("Error", "Invalid username or password")


# -------------------------------------------------
#                   MAIN APP UI
# -------------------------------------------------
class DocumentationApp:
    def __init__(self, role, username):
        self.role = role
        self.username = username

        self.root = tk.Tk()
        self.root.title(f"Documentation System - Logged in as {username} ({role})")
        self.root.geometry("1000x650")

        self.error_code_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.version_var = tk.StringVar()

        self.docs = load_docs()

        self.create_ui()
        self.root.mainloop()

    # -------------------------------------------------
    # UI Layout
    # -------------------------------------------------
    def create_ui(self):
        left = tk.Frame(self.root, width=250)
        left.pack(side="left", fill="y")

        right = tk.Frame(self.root)
        right.pack(side="right", expand=True, fill="both")

        # List of docs
        tk.Label(left, text="Documentation List", font=("Arial", 14)).pack(pady=10)
        self.doc_list = tk.Listbox(left)
        self.doc_list.pack(expand=True, fill="y", padx=10)
        self.doc_list.bind("<<ListboxSelect>>", self.load_selected_doc)

        for c in self.docs.values():
            self.doc_list.insert("end", f"{c['error_code']} - {c['title']}")

        if self.role == "admin":
            tk.Button(left, text="Create New", command=self.new_doc).pack(pady=10)

        # Right side
        top = tk.Frame(right)
        top.pack(fill="x")

        tk.Label(top, text="Error Code:").pack(side="left")
        self.ec_entry = tk.Entry(top, textvariable=self.error_code_var)
        self.ec_entry.pack(side="left")

        tk.Label(top, text="Title:").pack(side="left")
        tk.Entry(top, textvariable=self.title_var, width=40).pack(side="left")

        self.version_menu = ttk.Combobox(top, textvariable=self.version_var)
        self.version_menu.pack(side="left")
        self.version_menu.bind("<<ComboboxSelected>>", self.load_version_dropdown)

        # Text editor
        self.text = ScrolledText(right)
        self.text.pack(expand=True, fill="both")

        # Buttons
        bottom = tk.Frame(right)
        bottom.pack(fill="x")

        tk.Button(bottom, text="Paste Image", command=self.paste_image).pack(side="left")

        if self.role == "admin":
            tk.Button(bottom, text="Save Version", command=self.save_version_handler).pack(side="left")

            # Disable edit for users
        if self.role == "user":
            self.text.config(state="disabled")

        tk.Button(bottom, text="Add Comment", command=self.add_comment).pack(side="right")

    # -------------------------------------------------
    # Load selected documentation
    # -------------------------------------------------
    def load_selected_doc(self, event):
        index = self.doc_list.curselection()
        if not index:
            return

        item = self.doc_list.get(index)
        error = item.split(" - ")[0]

        doc = self.docs[error]
        self.error_code_var.set(error)
        self.title_var.set(doc["title"])

        versions = self.get_versions(error)
        self.version_menu["values"] = versions

        latest = int(doc["latest_version"])
        self.version_var.set(f"v{latest}")

        self.load_version_dropdown()

    def get_versions(self, error_code):
        folder = os.path.join(VERSIONS_DIR, error_code)
        if not os.path.exists(folder):
            return []
        return [f"v{x}" for x in range(1, len(os.listdir(folder)) + 1)]

    # -------------------------------------------------
    # Load version
    # -------------------------------------------------
    def load_version_dropdown(self, event=None):
        version_str = self.version_var.get()
        if not version_str:
            return

        version = int(version_str.replace("v", ""))
        error_code = self.error_code_var.get()

        data = load_version(error_code, version)

        self.text.config(state="normal")
        self.text.delete("1.0", "end")

        for item in data["content"]:
            if item["type"] == "text":
                self.text.insert("end", item["value"] + "\n")
            else:
                self.text.insert("end", f"[IMAGE: {item['value']}]\n")

        if self.role == "user":
            self.text.config(state="disabled")

    # -------------------------------------------------
    # New doc
    # -------------------------------------------------
    def new_doc(self):
        self.error_code_var.set("")
        self.title_var.set("")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")

    # -------------------------------------------------
    # Save new version
    # -------------------------------------------------
    def save_version_handler(self):
        error = self.error_code_var.get().strip()
        title = self.title_var.get().strip()

        if not error:
            messagebox.showerror("Error", "Error Code cannot be empty")
            return

        if error in self.docs:
            doc = self.docs[error]
            latest = int(doc["latest_version"])
            new_version = latest + 1
            doc["latest_version"] = str(new_version)
        else:
            new_version = 1
            self.docs[error] = {
                "error_code": error,
                "title": title,
                "latest_version": "1",
                "created_by": self.username,
                "created_at": "now"
            }

        content = self.extract_content()
        save_version(error, new_version, content, self.username)
        save_doc_row(self.docs[error])

        messagebox.showinfo("Saved", f"Version v{new_version} saved.")
        self.refresh_list()

    # Extract editor lines
    def extract_content(self):
        lines = self.text.get("1.0", "end").split("\n")
        content = []

        for l in lines:
            if l.startswith("[IMAGE:"):
                img = l.replace("[IMAGE:", "").replace("]", "").strip()
                content.append({"type": "image", "value": img})
            else:
                if l.strip():
                    content.append({"type": "text", "value": l})
        return content

    # -------------------------------------------------
    # Paste image
    # -------------------------------------------------
    def paste_image(self):
        if self.role == "user":
            return

        img = ImageGrab.grabclipboard()

        if isinstance(img, Image.Image):
            error = self.error_code_var.get()
            if not error:
                messagebox.showerror("Error", "Save the documentation first.")
                return

            folder = os.path.join(IMAGES_DIR, error)
            os.makedirs(folder, exist_ok=True)

            filename = f"img_{len(os.listdir(folder)) + 1}.png"
            path = os.path.join(folder, filename)
            img.save(path)

            self.text.insert("end", f"[IMAGE: {filename}]\n")
        else:
            messagebox.showinfo("No Image", "Clipboard does not contain an image.")

    # -------------------------------------------------
    # Add comment
    # -------------------------------------------------
    def add_comment(self):
        error = self.error_code_var.get()
        version = self.version_var.get().replace("v", "")

        win = tk.Toplevel(self.root)
        win.title("Add Comment")
        win.geometry("400x200")

        text = ScrolledText(win)
        text.pack(expand=True, fill="both")

        def save_comment():
            comment = text.get("1.0", "end").strip()
            with open(COMMENTS_CSV, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([error, version, self.username, comment, "now"])
            win.destroy()

        tk.Button(win, text="Save", command=save_comment).pack()

    # -------------------------------------------------
    # Refresh list
    # -------------------------------------------------
    def refresh_list(self):
        self.docs = load_docs()
        self.doc_list.delete(0, "end")
        for c in self.docs.values():
            self.doc_list.insert("end", f"{c['error_code']} - {c['title']}")


# -------------------------------------------------
# RUN APP (starts with login)
# -------------------------------------------------
LoginWindow()
