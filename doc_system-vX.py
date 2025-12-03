"""
doc_app_final.py

Full local Documentation System (Tkinter) - FINAL
- Login (users.csv)
- Roles: admin (create/edit) & user (view + comment)
- Version control: data/versions/<error_code>/v{n}/data.json
- Images: paste from clipboard or load from disk (staged) -> committed on Save New Version
- Render images inline in Text viewer (PhotoImage + image_create)
- Comments stored in CSV
- Shows Created Date (document) and Updated Date (version)
"""

import os
import csv
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import copy

# ----------------------------
# Configuration / Paths
# ----------------------------
DATA_DIR = "data"
VERSIONS_DIR = os.path.join(DATA_DIR, "versions")   # versions/<error_code>/v{n}/data.json + images/
DOCS_CSV = os.path.join(DATA_DIR, "documentation.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "comments.csv")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")

# ----------------------------
# Initialization
# ----------------------------
def ensure_dirs_and_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VERSIONS_DIR, exist_ok=True)

    if not os.path.exists(DOCS_CSV):
        with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["error_code", "title", "latest_version", "created_by", "created_at"])

    if not os.path.exists(COMMENTS_CSV):
        with open(COMMENTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["error_code", "version", "user", "comment", "timestamp"])

    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password", "role"])
            # default users (plain-text password for demo)
            writer.writerow(["admin", "admin", "admin"])
            writer.writerow(["client", "client", "user"])

ensure_dirs_and_files()

# ----------------------------
# Helper functions: docs / versions
# ----------------------------
def load_docs_index():
    docs = {}
    with open(DOCS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            docs[r["error_code"]] = r
    return docs

def save_docs_index(docs):
    with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["error_code", "title", "latest_version", "created_by", "created_at"])
        for ecode in sorted(docs.keys()):
            d = docs[ecode]
            writer.writerow([d["error_code"], d.get("title",""), d.get("latest_version","0"), d.get("created_by",""), d.get("created_at","")])

def get_versions_list(error_code):
    folder = os.path.join(VERSIONS_DIR, error_code)
    if not os.path.exists(folder):
        return []
    versions = []
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if name.startswith("v") and os.path.isdir(full):
            versions.append(name)
    return versions

def get_latest_version_num(error_code):
    docs = load_docs_index()
    if error_code not in docs:
        return 0
    try:
        return int(docs[error_code]["latest_version"])
    except:
        return 0

def load_version_data(error_code, version_num):
    vpath = os.path.join(VERSIONS_DIR, error_code, f"v{version_num}", "data.json")
    if not os.path.exists(vpath):
        return None
    with open(vpath, "r", encoding="utf-8") as f:
        return json.load(f)

def add_document_index_entry(error_code, title, created_by):
    docs = load_docs_index()
    if error_code in docs:
        raise ValueError("error_code already exists")
    docs[error_code] = {
        "error_code": error_code,
        "title": title,
        "latest_version": "0",
        "created_by": created_by,
        "created_at": datetime.now().isoformat()
    }
    save_docs_index(docs)

def save_new_version(error_code, content_blocks, updated_by):
    """
    content_blocks: list of {"type":"text","value":...} or {"type":"image","value":"filename.png"}
    Behavior:
      - new_version = latest + 1 (or 1)
      - create versions/<error_code>/v{new_version}/images/
      - move staged images if present from _staging -> new version images
      - for referenced images that exist in previous version use copy from prev version images
      - write data.json with updated_at timestamp
      - update docs index latest_version
    """
    docs = load_docs_index()
    if error_code not in docs:
        # create minimal index entry if missing
        docs[error_code] = {
            "error_code": error_code,
            "title": "",
            "latest_version": "0",
            "created_by": updated_by,
            "created_at": datetime.now().isoformat()
        }

    latest = int(docs[error_code].get("latest_version", "0"))
    new_version = latest + 1
    vfolder = os.path.join(VERSIONS_DIR, error_code, f"v{new_version}")
    images_folder = os.path.join(vfolder, "images")
    os.makedirs(images_folder, exist_ok=True)

    # Move staged images (if any)
    staging = os.path.join(VERSIONS_DIR, error_code, "_staging")
    staged_files = set()
    if os.path.exists(staging):
        for fname in os.listdir(staging):
            src = os.path.join(staging, fname)
            dst = os.path.join(images_folder, fname)
            shutil.move(src, dst)
            staged_files.add(fname)
        # try remove staging if empty
        try:
            os.rmdir(staging)
        except:
            pass

    # If image blocks reference existing images from previous version(s),
    # copy them into this new version images folder unless they were in staging already.
    # Determine previous images folder (latest)
    prev_images_folder = None
    if latest >= 1:
        prev_images_folder = os.path.join(VERSIONS_DIR, error_code, f"v{latest}", "images")

    # For each image block referenced in content_blocks, ensure a copy exists in new images folder
    for blk in content_blocks:
        if blk.get("type") == "image":
            fname = blk.get("value")
            if not fname:
                continue
            # if already moved from staging -> exists
            dstpath = os.path.join(images_folder, fname)
            if os.path.exists(dstpath):
                continue
            # if exists in prev images -> copy
            if prev_images_folder:
                candidate = os.path.join(prev_images_folder, fname)
                if os.path.exists(candidate):
                    try:
                        shutil.copy2(candidate, dstpath)
                        continue
                    except Exception:
                        pass
            # If not found anywhere, leave as-is; viewer will show MISSING IMAGE
    # Write version data
    data = {
        "version": new_version,
        "updated_by": updated_by,
        "updated_at": datetime.now().isoformat(),
        "content": content_blocks
    }
    with open(os.path.join(vfolder, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # update docs index
    docs[error_code]["latest_version"] = str(new_version)
    save_docs_index(docs)
    return new_version

# ----------------------------
# Comments helpers
# ----------------------------
def add_comment_row(error_code, version, user, comment_text):
    timestamp = datetime.now().isoformat()
    with open(COMMENTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([error_code, version, user, comment_text, timestamp])

def load_comments_for_doc(error_code):
    arr = []
    with open(COMMENTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["error_code"] == error_code:
                arr.append(r)
    return arr

# ----------------------------
# Users helpers
# ----------------------------
def load_users():
    users = {}
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            users[r["username"]] = r
    return users

# ----------------------------
# UI: Login window
# ----------------------------
class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login - Documentation System")
        self.root.geometry("360x220")
        self.root.resizable(False, False)

        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Username:").pack(anchor="w", pady=(6,0))
        self.ent_user = ttk.Entry(frm)
        self.ent_user.pack(fill="x")

        ttk.Label(frm, text="Password:").pack(anchor="w", pady=(6,0))
        self.ent_pass = ttk.Entry(frm, show="*")
        self.ent_pass.pack(fill="x")

        self.lbl_msg = ttk.Label(frm, text="", foreground="red")
        self.lbl_msg.pack(pady=6)

        btn = ttk.Button(frm, text="Login", command=self.attempt_login)
        btn.pack(pady=6)

        self.root.bind("<Return>", lambda e: self.attempt_login())
        self.root.mainloop()

    def attempt_login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        if not u or not p:
            self.lbl_msg.config(text="username & password required")
            return
        users = load_users()
        if u in users and users[u]["password"] == p:
            role = users[u]["role"]
            self.root.destroy()
            AppMain(role=role, username=u)
            return
        else:
            self.lbl_msg.config(text="invalid username/password")

# ----------------------------
# UI: Main App
# ----------------------------
class AppMain:
    def __init__(self, role, username):
        self.role = role
        self.username = username
        self.docs_index = load_docs_index()
        self.current_error = None
        self.current_version = None
        self.image_refs = []  # keep PhotoImage refs
        # create main window
        self.create_main_window()

    def create_main_window(self):
        self.root = tk.Tk()
        self.root.title(f"Doc System — {self.username} ({self.role})")
        self.root.geometry("1100x740")

        # top bar
        topbar = ttk.Frame(self.root, padding=6)
        topbar.pack(fill="x")
        ttk.Label(topbar, text=f"Logged in: {self.username} ({self.role})").pack(side="left")
        ttk.Button(topbar, text="Logout", command=self.logout).pack(side="right")

        # main frame
        main = ttk.Frame(self.root, padding=6)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, width=320)
        left.pack(side="left", fill="y")
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        # left: docs list
        ttk.Label(left, text="Documentation", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.lst_docs = tk.Listbox(left, width=48)
        self.lst_docs.pack(fill="y", expand=True, pady=6)
        self.lst_docs.bind("<<ListboxSelect>>", self.on_doc_select)

        lbtns = ttk.Frame(left)
        lbtns.pack(fill="x", pady=6)
        if self.role == "admin":
            ttk.Button(lbtns, text="Create New Doc", command=self.open_create_dialog).pack(side="left", padx=4)
        ttk.Button(lbtns, text="Refresh", command=self.refresh_docs).pack(side="left", padx=4)

        # right: metadata + viewer + controls
        meta = ttk.Frame(right)
        meta.pack(fill="x", pady=(0,6))
        # created & updated labels
        self.lbl_created = ttk.Label(meta, text="Created: -")
        self.lbl_created.pack(side="left", padx=(0,8))
        self.lbl_updated = ttk.Label(meta, text="Updated (version): -")
        self.lbl_updated.pack(side="left", padx=(0,16))

        ttk.Label(meta, text="Error Code:").pack(side="left")
        self.var_error = tk.StringVar()
        self.ent_error = ttk.Entry(meta, textvariable=self.var_error, width=12)
        self.ent_error.pack(side="left", padx=(4,8))

        ttk.Label(meta, text="Title:").pack(side="left")
        self.var_title = tk.StringVar()
        self.ent_title = ttk.Entry(meta, textvariable=self.var_title, width=40)
        self.ent_title.pack(side="left", padx=(4,8))

        ttk.Label(meta, text="Version:").pack(side="left")
        self.cb_versions = ttk.Combobox(meta, values=[], state="readonly", width=10)
        self.cb_versions.pack(side="left")
        self.cb_versions.bind("<<ComboboxSelected>>", self.on_version_change)

        # viewer (Text) - images inserted inline
        self.txt = ScrolledText(right, wrap="word")
        self.txt.pack(fill="both", expand=True)
        if self.role == "user":
            self.txt.config(state="disabled")

        # bottom controls
        ctl = ttk.Frame(right)
        ctl.pack(fill="x", pady=6)
        ttk.Button(ctl, text="Paste Image (clipboard)", command=self.handle_paste_image).pack(side="left", padx=4)
        ttk.Button(ctl, text="Insert Image From Disk", command=self.insert_image_from_disk).pack(side="left", padx=4)
        if self.role == "admin":
            ttk.Button(ctl, text="Save New Version", command=self.handle_save_version).pack(side="left", padx=4)

        ttk.Button(ctl, text="Add Comment", command=self.open_add_comment).pack(side="right", padx=4)

        # comments list
        ttk.Label(right, text="Comments:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.lst_comments = tk.Listbox(right, height=6)
        self.lst_comments.pack(fill="x", pady=(0,6))

        # populate list
        self.refresh_docs()
        self.root.mainloop()

    # ----------------------------
    # Docs list
    # ----------------------------
    def refresh_docs(self):
        self.docs_index = load_docs_index()
        self.lst_docs.delete(0,"end")
        for ecode, d in sorted(self.docs_index.items()):
            display = f"{ecode} — {d.get('title','(no title)')} (v{d.get('latest_version','0')})"
            self.lst_docs.insert("end", display)

    def on_doc_select(self, event):
        sel = self.lst_docs.curselection()
        if not sel: return
        text = self.lst_docs.get(sel[0])
        ecode = text.split(" — ")[0]
        self.load_document(ecode)

    def load_document(self, error_code):
        self.current_error = error_code
        docs = load_docs_index()
        doc = docs.get(error_code)
        if not doc:
            messagebox.showerror("Error", "Document metadata missing")
            return
        # populate metadata
        self.var_error.set(error_code)
        self.var_title.set(doc.get("title",""))
        created_at = doc.get("created_at","-")
        self.lbl_created.config(text=f"Created: {created_at}")
        # versions
        versions = get_versions_list(error_code)
        self.cb_versions['values'] = versions
        latest_num = int(doc.get("latest_version","0"))
        if latest_num > 0:
            self.cb_versions.set(f"v{latest_num}")
            self.load_version(latest_num)
        else:
            self.cb_versions.set("")
            self.txt.config(state="normal")
            self.txt.delete("1.0","end")
            if self.role == "user": self.txt.config(state="disabled")
        self.refresh_comments()

    # ----------------------------
    # Load version and render content
    # ----------------------------
    def load_version(self, version_num):
        if not self.current_error:
            return
        data = load_version_data(self.current_error, version_num)
        if not data:
            messagebox.showerror("Error", f"Version v{version_num} data not found")
            return
        self.current_version = version_num
        updated_at = data.get("updated_at","-")
        self.lbl_updated.config(text=f"Updated: {updated_at} (v{version_num})")
        # clear refs and render
        self.image_refs.clear()
        self.txt.config(state="normal")
        self.txt.delete("1.0","end")
        for blk in data.get("content", []):
            if blk.get("type") == "text":
                self.txt.insert("end", blk.get("value","") + "\n\n")
            elif blk.get("type") == "image":
                fname = blk.get("value")
                ipath = os.path.join(VERSIONS_DIR, self.current_error, f"v{version_num}", "images", fname)
                if os.path.exists(ipath):
                    try:
                        img = Image.open(ipath)
                        max_w, max_h = 800, 600
                        if img.width > max_w or img.height > max_h:
                            img.thumbnail((max_w, max_h))
                        photo = ImageTk.PhotoImage(img)
                        self.txt.insert("end", "\n")
                        self.txt.image_create("end", image=photo)
                        self.txt.insert("end", "\n\n")
                        self.image_refs.append(photo)
                    except Exception as e:
                        self.txt.insert("end", f"[ERROR LOADING IMAGE: {fname}]\n\n")
                else:
                    self.txt.insert("end", f"[MISSING IMAGE: {fname}]\n\n")
        if self.role == "user":
            self.txt.config(state="disabled")

    def on_version_change(self, event):
        val = self.cb_versions.get()
        if val and val.startswith("v"):
            try:
                n = int(val.lstrip("v"))
                self.load_version(n)
            except:
                pass

    # ----------------------------
    # Create new doc dialog (admin)
    # ----------------------------
    def open_create_dialog(self):
        if self.role != "admin": return
        dlg = tk.Toplevel(self.root)
        dlg.title("Create New Documentation")
        dlg.geometry("460x200")
        ttk.Label(dlg, text="Error Code (unique):").pack(anchor="w", padx=8, pady=(8,0))
        ent_code = ttk.Entry(dlg)
        ent_code.pack(fill="x", padx=8)
        ttk.Label(dlg, text="Title:").pack(anchor="w", padx=8, pady=(8,0))
        ent_title = ttk.Entry(dlg)
        ent_title.pack(fill="x", padx=8)

        def do_create():
            code = ent_code.get().strip()
            title = ent_title.get().strip()
            if not code:
                messagebox.showerror("Error", "Error Code required")
                return
            docs = load_docs_index()
            if code in docs:
                messagebox.showerror("Error", "Error Code already exists — must be unique")
                return
            add_document_index_entry(code, title, self.username)
            self.refresh_docs()
            dlg.destroy()
            messagebox.showinfo("OK", f"Document {code} created. Open it, then Save New Version to add content.")

        ttk.Button(dlg, text="Create", command=do_create).pack(pady=12)

    # ----------------------------
    # Paste image from clipboard (admin)
    # stores in staging: versions/<error_code>/_staging/<fname>
    # inserts placeholder line [IMAGE: fname] in editor text
    # ----------------------------
    def handle_paste_image(self):
        if self.role != "admin":
            messagebox.showerror("Forbidden", "Only admin can paste images")
            return
        ecode = self.var_error.get().strip()
        if not ecode:
            messagebox.showerror("Error", "Fill Error Code first")
            return
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            staging = os.path.join(VERSIONS_DIR, ecode, "_staging")
            os.makedirs(staging, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
            fname = f"img_{ts}.png"
            path = os.path.join(staging, fname)
            try:
                img.save(path, format="PNG")
                self.txt.config(state="normal")
                self.txt.insert("insert", f"[IMAGE: {fname}]\n")
                if self.role == "user":
                    self.txt.config(state="disabled")
                messagebox.showinfo("Pasted", f"Image pasted as {fname} (staged). Save New Version to commit.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save clipboard image: {e}")
        else:
            messagebox.showinfo("No Image", "No image in clipboard.")

    # ----------------------------
    # Insert image from disk (admin) - copies to staging and inserts placeholder
    # ----------------------------
    def insert_image_from_disk(self):
        if self.role != "admin":
            return
        ecode = self.var_error.get().strip()
        if not ecode:
            messagebox.showerror("Error", "Fill Error Code first")
            return
        files = filedialog.askopenfilenames(title="Select images")
        if not files:
            return
        staging = os.path.join(VERSIONS_DIR, ecode, "_staging")
        os.makedirs(staging, exist_ok=True)
        for f in files:
            try:
                base = os.path.basename(f)
                ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
                fname = f"{ts}_{base}"
                dst = os.path.join(staging, fname)
                shutil.copy2(f, dst)
                self.txt.config(state="normal")
                self.txt.insert("insert", f"[IMAGE: {fname}]\n")
                if self.role == "user":
                    self.txt.config(state="disabled")
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to copy {f}: {e}")
        messagebox.showinfo("Done", "Images staged and placeholder inserted. Save New Version to commit.")

    # ----------------------------
    # Save new version (admin)
    # - Parse text content and preserve referenced images (copy from previous version if referenced)
    # - Move staged images into new version folder
    # ----------------------------
    def handle_save_version(self):
        if self.role != "admin":
            messagebox.showerror("Forbidden", "Only admin can save versions")
            return
        ecode = self.var_error.get().strip()
        title = self.var_title.get().strip()
        if not ecode:
            messagebox.showerror("Error", "Error Code required")
            return
        # ensure doc entry exists
        docs = load_docs_index()
        if ecode not in docs:
            add_document_index_entry(ecode, title or "", self.username)
            docs = load_docs_index()
        else:
            # update title if changed
            if title and docs[ecode].get("title","") != title:
                docs[ecode]["title"] = title
                save_docs_index(docs)

        # parse editor text into blocks; keep image placeholders as image blocks
        raw = self.txt.get("1.0", "end").strip()
        lines = raw.splitlines()
        blocks = []
        for ln in lines:
            ln = ln.rstrip()
            if ln.startswith("[IMAGE:") and ln.endswith("]"):
                fname = ln[len("[IMAGE:"):].rstrip(" ]").strip()
                if fname:
                    blocks.append({"type":"image", "value": fname})
            else:
                if ln.strip():
                    # We aggregate continuous text lines into paragraphs for nicer structure
                    blocks.append({"type":"text", "value": ln})

        # Save new version: save_new_version will move staging and copy referenced previous images
        new_vnum = save_new_version(ecode, blocks, self.username)
        # update title saved
        docs = load_docs_index()
        docs[ecode]["title"] = title
        save_docs_index(docs)

        messagebox.showinfo("Saved", f"Saved new version v{new_vnum} for {ecode}")
        # refresh UI
        self.refresh_docs()
        self.load_document(ecode)

    # ----------------------------
    # Comments
    # ----------------------------
    def open_add_comment(self):
        if not self.current_error:
            messagebox.showerror("Error", "Select a document first")
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Comment")
        dlg.geometry("600x300")
        txt = ScrolledText(dlg)
        txt.pack(expand=True, fill="both", padx=6, pady=6)

        def do_save():
            text = txt.get("1.0","end").strip()
            if not text:
                messagebox.showerror("Error", "Comment empty")
                return
            v = self.current_version or get_latest_version_num(self.current_error)
            add_comment_row(self.current_error, v, self.username, text)
            dlg.destroy()
            self.refresh_comments()
            messagebox.showinfo("OK", "Comment saved")

        ttk.Button(dlg, text="Save Comment", command=do_save).pack(pady=6)

    def refresh_comments(self):
        self.lst_comments.delete(0,"end")
        if not self.current_error:
            return
        cmts = load_comments_for_doc(self.current_error)
        for c in cmts:
            ts = c.get("timestamp","")
            user = c.get("user","")
            text = c.get("comment","")
            self.lst_comments.insert("end", f"[{ts}] {user}: {text}")

    # ----------------------------
    # Logout
    # ----------------------------
    def logout(self):
        if messagebox.askyesno("Logout", "Logout and return to login?"):
            self.root.destroy()
            LoginWindow()

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    LoginWindow()
