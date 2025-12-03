# doc_app_tkinter_singlecsv.py
"""
Documentation System - Single CSV + Tkinter Tabbed UI (ttkbootstrap if available)

Features:
- Login (data/users.csv) with roles admin/user
- Admin: create doc, edit -> create new version. Paste images (Ctrl+V) supported.
- User: view + comment only.
- Single CSV: data/documentation.csv with columns:
    error_code,title,created_by,created_at,versions
  where versions is a JSON string containing list of versions.
- Images saved to data/images/<error_code>/v{n}/images/<fname>
- Tabbed UI (ttk.Notebook), created & updated dates shown dd-mm-yyyy.
- Comments stored in data/comments.csv (simple rows).
"""

import os
import csv
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from io import BytesIO
try:
    from PIL import Image, ImageTk, ImageGrab
except Exception:
    raise SystemExit("Pillow is required. Install with: pip install pillow")

# try ttkbootstrap
USE_TTB = False
try:
    import ttkbootstrap as ttb
    from ttkbootstrap.constants import *
    USE_TTB = True
except Exception:
    ttb = None

# -------------------------
# Configuration & paths
# -------------------------
DATA_DIR = "data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")  # images/<error_code>/v{n}/images/
DOCS_CSV = os.path.join(DATA_DIR, "documentation.csv")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
COMMENTS_CSV = os.path.join(DATA_DIR, "comments.csv")

DATE_FMT_DISPLAY = "%d-%m-%Y"

# -------------------------
# Helpers: init storage
# -------------------------
def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    # docs csv: single CSV; versions column will be JSON string
    if not os.path.exists(DOCS_CSV):
        with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["error_code", "title", "created_by", "created_at", "versions"])
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["username", "password", "role"])
            w.writerow(["admin", "admin", "admin"])
            w.writerow(["client", "client", "user"])
    if not os.path.exists(COMMENTS_CSV):
        with open(COMMENTS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["error_code", "version", "user", "comment", "timestamp"])

ensure_storage()

# -------------------------
# Utility functions
# -------------------------
def read_docs_csv():
    docs = {}
    with open(DOCS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # ensure versions parsed
            versions = []
            try:
                versions = json.loads(r.get("versions","[]") or "[]")
            except Exception:
                versions = []
            r["versions"] = versions
            docs[r["error_code"]] = r
    return docs

def write_docs_csv(docs):
    # docs: dict mapping error_code -> row dict (with "versions" as list)
    rows = []
    for code, r in sorted(docs.items()):
        rr = r.copy()
        rr["versions"] = json.dumps(rr.get("versions", []), ensure_ascii=False)
        rows.append(rr)
    with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["error_code", "title", "created_by", "created_at", "versions"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rr in rows:
            writer.writerow(rr)

def read_users():
    users = {}
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            users[r["username"]] = r
    return users

def append_comment(error_code, version, user, comment_text):
    ts = datetime.now().isoformat()
    with open(COMMENTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([error_code, version, user, comment_text, ts])

def read_comments(error_code):
    arr = []
    with open(COMMENTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["error_code"] == error_code:
                arr.append(r)
    return arr

def iso_to_display(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime(DATE_FMT_DISPLAY)
    except Exception:
        return iso_str or "-"

# -------------------------
# Version helpers (single CSV approach)
# Each doc row contains versions = [ {version, updated_by, updated_at, content: [blocks] }, ... ]
# Blocks: {"type":"text","value":...} or {"type":"image","value": "fname.png"}
# Images saved on filesystem under IMAGES_DIR/<error_code>/v{n}/images/<fname>
# When new version saved, staging images (IMAGES_DIR/<error_code>/_staging/) are moved into the new version images folder.
# Also copy referenced images from previous version if still referenced and not in staging.
# -------------------------
def ensure_doc_entry(error_code, title, created_by):
    docs = read_docs_csv()
    if error_code in docs:
        raise ValueError("error_code exists")
    docs[error_code] = {
        "error_code": error_code,
        "title": title,
        "created_by": created_by,
        "created_at": datetime.now().isoformat(),
        "versions": []
    }
    write_docs_csv(docs)

def get_latest_version_num(error_code):
    docs = read_docs_csv()
    if error_code not in docs:
        return 0
    vlist = docs[error_code].get("versions", [])
    if not vlist:
        return 0
    return max([v.get("version",0) for v in vlist])

def save_new_version_from_blocks(error_code, blocks, updated_by):
    """
    blocks: list of blocks (text/image)
    Behavior:
    - new_version = latest+1
    - create folder IMAGES_DIR/<error_code>/v{new_version}/images/
    - move staging files from _staging into that images folder
    - copy referenced images from previous version images folders if needed
    - append version entry into CSV (versions JSON)
    """
    docs = read_docs_csv()
    if error_code not in docs:
        # create with basic metadata
        docs[error_code] = {
            "error_code": error_code,
            "title": "",
            "created_by": updated_by,
            "created_at": datetime.now().isoformat(),
            "versions": []
        }
    versions = docs[error_code]["versions"]
    latest = 0
    if versions:
        latest = max([v.get("version",0) for v in versions])
    new_v = latest + 1

    # prepare folders
    vfolder = os.path.join(IMAGES_DIR, error_code, f"v{new_v}")
    images_folder = os.path.join(vfolder, "images")
    os.makedirs(images_folder, exist_ok=True)

    # move staged files
    staging = os.path.join(IMAGES_DIR, error_code, "_staging")
    staged = set()
    if os.path.exists(staging):
        for fname in os.listdir(staging):
            src = os.path.join(staging, fname)
            dst = os.path.join(images_folder, fname)
            try:
                shutil.move(src, dst)
                staged.add(fname)
            except Exception:
                try:
                    shutil.copy2(src, dst)
                    staged.add(fname)
                except Exception:
                    pass
        # try remove staging
        try:
            os.rmdir(staging)
        except Exception:
            pass

    # copy referenced images from previous version if applicable
    prev_images_folder = None
    if latest >= 1:
        prev_images_folder = os.path.join(IMAGES_DIR, error_code, f"v{latest}", "images")

    for blk in blocks:
        if blk.get("type") == "image":
            fname = blk.get("value")
            if not fname:
                continue
            dst = os.path.join(images_folder, fname)
            if os.path.exists(dst):
                continue
            # if staged already moved, continue
            if fname in staged:
                continue
            # copy from previous images folder if exists
            if prev_images_folder:
                cand = os.path.join(prev_images_folder, fname)
                if os.path.exists(cand):
                    try:
                        shutil.copy2(cand, dst)
                        continue
                    except Exception:
                        pass
            # otherwise leave missing (viewer will show placeholder)

    # write version object
    version_obj = {
        "version": new_v,
        "updated_by": updated_by,
        "updated_at": datetime.now().isoformat(),
        "content": blocks
    }
    versions.append(version_obj)
    docs[error_code]["versions"] = versions
    write_docs_csv(docs)
    return new_v

# -------------------------
# UI components
# -------------------------
class LoginWindow:
    def __init__(self):
        if USE_TTB:
            self.root = ttb.Window(themename="flatly")
        else:
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
        ttk.Button(frm, text="Login", command=self.do_login).pack(pady=6)

        self.root.bind("<Return>", lambda e: self.do_login())
        self.root.mainloop()

    def do_login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        if not u or not p:
            self.lbl_msg.config(text="username & password required")
            return
        users = read_users()
        if u in users and users[u]["password"] == p:
            role = users[u]["role"]
            self.root.destroy()
            AppMain(role=role, username=u)
        else:
            self.lbl_msg.config(text="invalid username/password")


class AppMain:
    def __init__(self, role, username):
        self.role = role
        self.username = username
        self.docs = read_docs_csv()
        self.current_error = None
        self.current_version = None
        self.image_refs = []  # keep PhotoImage refs
        self.build_ui()

    def build_ui(self):
        # main window (ttkbootstrap or plain)
        if USE_TTB:
            self.root = ttb.Window(themename="flatly")
        else:
            self.root = tk.Tk()
        self.root.title(f"DocSystem — {self.username} ({self.role})")
        self.root.geometry("1100x740")

        top = ttk.Frame(self.root, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text=f"Logged in: {self.username} ({self.role})").pack(side="left")
        ttk.Button(top, text="Logout", command=self.logout).pack(side="right")

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Documents (list + viewer)
        self.tab_docs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_docs, text="Documents")

        # Tab 2: Editor (admin only) - create & edit
        self.tab_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="Editor")

        # Tab 3: Comments (view/add)
        self.tab_comments = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_comments, text="Comments")

        self.build_tab_documents()
        self.build_tab_editor()
        self.build_tab_comments()

        # If user role, disable editor tab
        if self.role != "admin":
            self.notebook.tab(self.tab_editor, state="disabled")

        self.refresh_doc_list()
        self.root.mainloop()

    # -------------------------
    # Documents tab
    # left: list; right: metadata + viewer + version dropdown
    # -------------------------
    def build_tab_documents(self):
        left = ttk.Frame(self.tab_docs, width=320)
        left.pack(side="left", fill="y", padx=6, pady=6)
        right = ttk.Frame(self.tab_docs)
        right.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        ttk.Label(left, text="Documentation", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.lst_docs = tk.Listbox(left, width=48)
        self.lst_docs.pack(fill="y", expand=True, pady=6)
        self.lst_docs.bind("<<ListboxSelect>>", self.on_doc_select)

        btns = ttk.Frame(left)
        btns.pack(fill="x")
        ttk.Button(btns, text="Refresh", command=self.refresh_doc_list).pack(side="left", padx=4)
        if self.role == "admin":
            ttk.Button(btns, text="Create New", command=self.open_create_dialog).pack(side="left", padx=4)
            ttk.Button(btns, text="Edit Selected", command=self.open_editor_from_selected).pack(side="left", padx=4)

        # right area
        meta = ttk.Frame(right)
        meta.pack(fill="x", pady=(0,6))
        self.lbl_created = ttk.Label(meta, text="Created: -"); self.lbl_created.pack(side="left", padx=(0,8))
        self.lbl_updated = ttk.Label(meta, text="Updated: -"); self.lbl_updated.pack(side="left", padx=(0,16))
        ttk.Label(meta, text="Error Code:").pack(side="left")
        self.var_ec = tk.StringVar(); self.ent_ec = ttk.Entry(meta, textvariable=self.var_ec, width=12); self.ent_ec.pack(side="left", padx=4)
        ttk.Label(meta, text="Title:").pack(side="left")
        self.var_title = tk.StringVar(); self.ent_title = ttk.Entry(meta, textvariable=self.var_title, width=40); self.ent_title.pack(side="left", padx=4)
        ttk.Label(meta, text="Version:").pack(side="left")
        self.cb_versions = ttk.Combobox(meta, values=[], state="readonly", width=10); self.cb_versions.pack(side="left")
        self.cb_versions.bind("<<ComboboxSelected>>", self.on_version_change)

        # viewer
        self.txt_view = ScrolledText(right, wrap="word")
        self.txt_view.pack(fill="both", expand=True)
        if self.role != "admin":
            self.txt_view.config(state="disabled")
        # viewer controls (paste, quick save)
        vctl = ttk.Frame(right); vctl.pack(fill="x", pady=6)
        if self.role == "admin":
            ttk.Button(vctl, text="Paste Image (clipboard)", command=self.paste_image_into_viewer).pack(side="left", padx=4)
            ttk.Button(vctl, text="Insert Image File", command=self.insert_image_into_viewer).pack(side="left", padx=4)
            ttk.Button(vctl, text="Quick Save New Version", command=self.quick_save_from_viewer).pack(side="left", padx=4)
        ttk.Button(vctl, text="Add Comment", command=self.open_comment_dialog_from_viewer).pack(side="right", padx=4)

    def refresh_doc_list(self):
        self.docs = read_docs_csv()
        self.lst_docs.delete(0, "end")
        for k, r in sorted(self.docs.items()):
            latest = 0
            try:
                latest = max([v.get("version",0) for v in r.get("versions", [])]) if r.get("versions") else 0
            except:
                latest = 0
            self.lst_docs.insert("end", f"{k} — {r.get('title','(no title)')} (v{latest})")

    def on_doc_select(self, evt=None):
        sel = self.lst_docs.curselection()
        if not sel: return
        line = self.lst_docs.get(sel[0])
        code = line.split(" — ")[0]
        self.load_document_into_view(code)

    def load_document_into_view(self, error_code):
        self.current_error = error_code
        self.docs = read_docs_csv()
        row = self.docs.get(error_code)
        if not row:
            messagebox.showerror("Error", "Document missing")
            return
        self.var_ec.set(row["error_code"])
        self.var_title.set(row.get("title",""))
        # created date
        self.lbl_created.config(text=f"Created: {iso_to_display(row.get('created_at',''))}")
        # versions
        versions = row.get("versions", []) or []
        vers_names = [f"v{v['version']}" for v in versions]
        self.cb_versions['values'] = vers_names
        if versions:
            latest = max([v['version'] for v in versions])
            self.cb_versions.set(f"v{latest}")
            self.load_version_into_view(error_code, latest)
        else:
            self.cb_versions.set("")
            self.txt_view.config(state="normal"); self.txt_view.delete("1.0","end")
            if self.role != "admin": self.txt_view.config(state="disabled")
        # comments
        self.refresh_comments_list()

    def load_version_into_view(self, error_code, vnum):
        row = read_docs_csv().get(error_code)
        if not row:
            return
        versions = row.get("versions", []) or []
        ver_obj = next((v for v in versions if v.get("version")==vnum), None)
        if not ver_obj:
            messagebox.showerror("Error", f"Version v{vnum} not found")
            return
        self.current_version = vnum
        self.lbl_updated.config(text=f"Updated: {iso_to_display(ver_obj.get('updated_at'))} (v{vnum})")
        # render content into text + inline images
        self.image_refs.clear()
        self.txt_view.config(state="normal"); self.txt_view.delete("1.0","end")
        for blk in ver_obj.get("content", []):
            if blk.get("type")=="text":
                self.txt_view.insert("end", blk.get("value","") + "\n\n")
            elif blk.get("type")=="image":
                fname = blk.get("value")
                ipath = os.path.join(IMAGES_DIR, error_code, f"v{vnum}", "images", fname)
                if os.path.exists(ipath):
                    try:
                        img = Image.open(ipath)
                        maxw, maxh = 800, 600
                        if img.width > maxw or img.height > maxh:
                            img.thumbnail((maxw, maxh))
                        photo = ImageTk.PhotoImage(img)
                        self.txt_view.insert("end", "\n")
                        self.txt_view.image_create("end", image=photo)
                        self.txt_view.insert("end", "\n\n")
                        self.image_refs.append(photo)
                    except Exception:
                        self.txt_view.insert("end", f"[ERROR LOADING IMAGE: {fname}]\n\n")
                else:
                    self.txt_view.insert("end", f"[MISSING IMAGE: {fname}]\n\n")
        if self.role != "admin":
            self.txt_view.config(state="disabled")

    def on_version_change(self, evt=None):
        val = self.cb_versions.get()
        if not val: return
        if val.startswith("v"):
            try:
                n = int(val.lstrip("v"))
                self.load_version_into_view(self.current_error, n)
            except:
                pass

    # paste image into viewer (stages to _staging and inserts placeholder)
    def paste_image_into_viewer(self):
        if self.role != "admin":
            messagebox.showerror("Forbidden","Admin only"); return
        ecode = self.var_ec.get().strip() or self.current_error
        if not ecode:
            messagebox.showerror("Select document or set Error Code first"); return
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            staging = os.path.join(IMAGES_DIR, ecode, "_staging")
            os.makedirs(staging, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
            fname = f"img_{ts}.png"
            path = os.path.join(staging, fname)
            try:
                img.save(path, format="PNG")
                self.txt_view.config(state="normal"); self.txt_view.insert("insert", f"[IMAGE: {fname}]\n")
                if self.role != "admin": self.txt_view.config(state="disabled")
                messagebox.showinfo("Pasted","Image staged; Save to commit new version.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")
        else:
            messagebox.showinfo("No Image", "Clipboard does not contain an image")

    def insert_image_into_viewer(self):
        if self.role != "admin": return
        ecode = self.var_ec.get().strip() or self.current_error
        if not ecode:
            messagebox.showerror("Select document or set Error Code first"); return
        files = filedialog.askopenfilenames(title="Select images")
        if not files: return
        staging = os.path.join(IMAGES_DIR, ecode, "_staging"); os.makedirs(staging, exist_ok=True)
        for f in files:
            base = os.path.basename(f); ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
            fname = f"{ts}_{base}"
            dst = os.path.join(staging, fname)
            try:
                shutil.copy2(f, dst)
                self.txt_view.config(state="normal"); self.txt_view.insert("insert", f"[IMAGE: {fname}]\n")
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to copy {f}: {e}")
        if self.role != "admin":
            self.txt_view.config(state="disabled")
        messagebox.showinfo("Staged", "Images staged; Save to commit new version.")

    def quick_save_from_viewer(self):
        # parse viewer text content to blocks and save new version
        if self.role != "admin":
            return
        ecode = self.var_ec.get().strip() or self.current_error
        if not ecode:
            messagebox.showerror("Error","Set Error Code first"); return
        raw = self.txt_view.get("1.0","end").strip()
        lines = raw.splitlines()
        blocks = []
        para = []
        def flush_para():
            nonlocal para
            if para:
                text = " ".join([p.strip() for p in para if p.strip()])
                blocks.append({"type":"text","value":text})
                para = []
        for ln in lines:
            ln = ln.rstrip()
            if ln.startswith("[IMAGE:") and ln.endswith("]"):
                flush_para()
                fname = ln[len("[IMAGE:"):].rstrip(" ]").strip()
                if fname:
                    blocks.append({"type":"image","value":fname})
            else:
                para.append(ln)
        flush_para()
        newv = save_new_version_from_blocks(ecode, blocks, self.username)
        # update title if changed
        docs = read_docs_csv(); docs[ecode]["title"] = self.var_title.get().strip(); write_docs_csv(docs)
        messagebox.showinfo("Saved", f"Saved new version v{newv}")
        self.refresh_doc_list(); self.load_document_into_view(ecode)

    # -------------------------
    # Editor tab (admin)
    # Provide a full editor area with paste support and "Save New Version"
    # -------------------------
    def build_tab_editor(self):
        frm = ttk.Frame(self.tab_editor, padding=8)
        frm.pack(fill="both", expand=True)
        top = ttk.Frame(frm); top.pack(fill="x")
        ttk.Label(top, text="Error Code:").pack(side="left")
        self.ed_ec = tk.StringVar(); ttk.Entry(top, textvariable=self.ed_ec, width=16).pack(side="left", padx=6)
        ttk.Label(top, text="Title:").pack(side="left")
        self.ed_title = tk.StringVar(); ttk.Entry(top, textvariable=self.ed_title, width=50).pack(side="left", padx=6)
        btns = ttk.Frame(top); btns.pack(side="left", padx=6)
        ttk.Button(btns, text="Load Existing", command=self.load_existing_into_editor).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=self.clear_editor_fields).pack(side="left", padx=4)

        # editor area
        self.editor = ScrolledText(frm, wrap="word")
        self.editor.pack(fill="both", expand=True, pady=6)
        # editor controls
        ectl = ttk.Frame(frm); ectl.pack(fill="x")
        ttk.Button(ectl, text="Paste Image (clipboard)", command=self.paste_into_editor).pack(side="left", padx=4)
        ttk.Button(ectl, text="Insert Image File", command=self.insert_file_into_editor).pack(side="left", padx=4)
        ttk.Button(ectl, text="Save New Version", command=self.save_new_version_from_editor).pack(side="left", padx=4)
        ttk.Button(ectl, text="Create Document (if new)", command=self.create_doc_from_editor).pack(side="left", padx=4)

    def load_existing_into_editor(self):
        code = self.ed_ec.get().strip()
        if not code:
            messagebox.showerror("Enter error code to load existing"); return
        docs = read_docs_csv()
        if code not in docs:
            messagebox.showerror("Not found"); return
        row = docs[code]
        self.ed_title.set(row.get("title",""))
        versions = row.get("versions", []) or []
        if versions:
            latest = max([v['version'] for v in versions])
            vobj = next((v for v in versions if v['version']==latest), None)
            # fill editor with content placeholders
            self.editor.delete("1.0","end")
            for blk in vobj.get("content", []):
                if blk.get("type")=="text":
                    self.editor.insert("end", blk.get("value","") + "\n\n")
                elif blk.get("type")=="image":
                    self.editor.insert("end", f"[IMAGE: {blk.get('value')}]\n\n")
        else:
            self.editor.delete("1.0","end")
        messagebox.showinfo("Loaded", f"Loaded {code} for editing (latest v{latest if versions else 0})")

    def clear_editor_fields(self):
        self.ed_ec.set(""); self.ed_title.set(""); self.editor.delete("1.0","end")

    def paste_into_editor(self):
        img = ImageGrab.grabclipboard()
        code = self.ed_ec.get().strip()
        if not code:
            messagebox.showerror("Set Error Code first"); return
        if isinstance(img, Image.Image):
            staging = os.path.join(IMAGES_DIR, code, "_staging"); os.makedirs(staging, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d%H%M%S%f"); fname = f"img_{ts}.png"; path = os.path.join(staging, fname)
            try:
                img.save(path, format="PNG")
                self.editor.insert("insert", f"[IMAGE: {fname}]\n")
                messagebox.showinfo("Pasted", "Image pasted and staged. Save new version to commit.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")
        else:
            messagebox.showinfo("No Image", "Clipboard does not contain image")

    def insert_file_into_editor(self):
        code = self.ed_ec.get().strip()
        if not code:
            messagebox.showerror("Set Error Code first"); return
        files = filedialog.askopenfilenames(title="Select images")
        if not files: return
        staging = os.path.join(IMAGES_DIR, code, "_staging"); os.makedirs(staging, exist_ok=True)
        for f in files:
            base = os.path.basename(f); ts = datetime.now().strftime("%Y%m%d%H%M%S%f"); fname = f"{ts}_{base}"
            dst = os.path.join(staging, fname)
            try:
                shutil.copy2(f, dst)
                self.editor.insert("insert", f"[IMAGE: {fname}]\n")
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to copy {f}: {e}")
        messagebox.showinfo("Staged", "Images staged. Save new version to commit.")

    def save_new_version_from_editor(self):
        if self.role != "admin":
            messagebox.showerror("Forbidden"); return
        code = self.ed_ec.get().strip()
        title = self.ed_title.get().strip()
        if not code:
            messagebox.showerror("Error", "Error code required"); return
        # parse editor text to blocks
        raw = self.editor.get("1.0","end").strip()
        lines = raw.splitlines()
        blocks = []
        para = []
        def flush_para():
            nonlocal para
            if para:
                txt = " ".join([p.strip() for p in para if p.strip()])
                if txt:
                    blocks.append({"type":"text","value":txt})
                para = []
        for ln in lines:
            ln = ln.rstrip()
            if ln.startswith("[IMAGE:") and ln.endswith("]"):
                flush_para()
                fname = ln[len("[IMAGE:"):].rstrip(" ]").strip()
                if fname:
                    blocks.append({"type":"image","value":fname})
            else:
                para.append(ln)
        flush_para()
        # ensure doc index exists
        docs = read_docs_csv()
        if code not in docs:
            docs[code] = {
                "error_code": code,
                "title": title,
                "created_by": self.username,
                "created_at": datetime.now().isoformat(),
                "versions": []
            }
        else:
            # update title if changed
            docs[code]["title"] = title
        write_docs_csv(docs)
        newv = save_new_version_from_blocks(code, blocks, self.username)
        messagebox.showinfo("Saved", f"New version v{newv} saved for {code}")
        self.refresh_doc_list()
        # if currently viewing same doc, reload
        if self.current_error == code:
            self.load_document_into_view(code)

    def create_doc_from_editor(self):
        if self.role != "admin":
            messagebox.showerror("Forbidden"); return
        code = self.ed_ec.get().strip(); title = self.ed_title.get().strip()
        if not code:
            messagebox.showerror("Error","Error code required"); return
        try:
            ensure_doc_entry = ensure_doc_entry_if_needed(code, title, self.username)
        except Exception:
            pass
        # call save new version from editor later

    # -------------------------
    # Comments tab
    # -------------------------
    def build_tab_comments(self):
        frm = ttk.Frame(self.tab_comments, padding=8); frm.pack(fill="both", expand=True)
        top = ttk.Frame(frm); top.pack(fill="x")
        ttk.Label(top, text="Error Code:").pack(side="left")
        self.cm_ec = tk.StringVar(); ttk.Entry(top, textvariable=self.cm_ec, width=20).pack(side="left", padx=6)
        ttk.Button(top, text="Load Comments", command=self.load_comments_for_code).pack(side="left", padx=6)
        self.lst_comments_tab = tk.Listbox(frm)
        self.lst_comments_tab.pack(fill="both", expand=True, pady=6)
        ttk.Button(frm, text="Add Comment", command=self.add_comment_from_tab).pack()

    def load_comments_for_code(self):
        code = self.cm_ec.get().strip()
        if not code:
            messagebox.showerror("Error","Enter error code"); return
        rows = read_comments(code)
        self.lst_comments_tab.delete(0,"end")
        for r in rows:
            ts = r.get("timestamp","")
            user = r.get("user","")
            comm = r.get("comment","")
            self.lst_comments_tab.insert("end", f"[{ts}] {user}: {comm}")

    def add_comment_from_tab(self):
        code = self.cm_ec.get().strip()
        if not code:
            messagebox.showerror("Error","Enter error code"); return
        dlg = tk.Toplevel(self.root); dlg.title("Add Comment"); dlg.geometry("600x300")
        ta = ScrolledText(dlg); ta.pack(fill="both", expand=True, padx=6, pady=6)
        def do_save():
            txt = ta.get("1.0","end").strip()
            if not txt:
                messagebox.showerror("Empty"); return
            v = get_latest_version_num(code)
            append_comment(code, v, self.username, txt); dlg.destroy(); messagebox.showinfo("OK","Saved")
        ttk.Button(dlg, text="Save", command=do_save).pack(pady=6)

    # -------------------------
    # comment helpers
    # -------------------------
    def refresh_comments_list(self):
        self.lst_comments.delete(0,"end")
        if not self.current_error:
            return
        rows = read_comments(self.current_error)
        for r in rows:
            ts = r.get("timestamp","")
            user = r.get("user","")
            comm = r.get("comment","")
            self.lst_comments.insert("end", f"[{ts}] {user}: {comm}")

    def open_comment_dialog_from_viewer(self):
        if not (self.current_error or self.var_ec.get().strip()):
            messagebox.showerror("Select doc first"); return
        code = self.current_error or self.var_ec.get().strip()
        dlg = tk.Toplevel(self.root); dlg.title("Add Comment"); dlg.geometry("600x300")
        ta = ScrolledText(dlg); ta.pack(fill="both", expand=True, padx=6, pady=6)
        def do_save():
            txt = ta.get("1.0","end").strip()
            if not txt: messagebox.showerror("Empty"); return
            v = self.current_version or get_latest_version_num(code)
            append_comment(code, v, self.username, txt); dlg.destroy(); messagebox.showinfo("Saved","OK"); self.refresh_comments_list()
        ttk.Button(dlg, text="Save Comment", command=do_save).pack(pady=6)

    # -------------------------
    # Utilities
    # -------------------------
    def open_create_dialog(self):
        dlg = tk.Toplevel(self.root); dlg.title("Create Document"); dlg.geometry("520x200")
        ttk.Label(dlg, text="Error Code (unique):").pack(anchor="w", padx=6, pady=(6,0))
        ec = ttk.Entry(dlg); ec.pack(fill="x", padx=6)
        ttk.Label(dlg, text="Title:").pack(anchor="w", padx=6, pady=(6,0))
        tt = ttk.Entry(dlg); tt.pack(fill="x", padx=6)
        def do_create():
            code = ec.get().strip(); title = tt.get().strip()
            if not code:
                messagebox.showerror("Error","Error code required"); return
            docs = read_docs_csv()
            if code in docs:
                messagebox.showerror("Error","Code exists"); return
            # create entry with empty versions
            docs[code] = {
                "error_code": code,
                "title": title,
                "created_by": self.username,
                "created_at": datetime.now().isoformat(),
                "versions": []
            }
            write_docs_csv(docs)
            messagebox.showinfo("Created", f"{code} created. Open it then save a new version to add content.")
            dlg.destroy(); self.refresh_doc_list()
        ttk.Button(dlg, text="Create", command=do_create).pack(pady=8)

    def open_editor_from_selected(self):
        sel = self.lst_docs.curselection()
        if not sel:
            messagebox.showerror("Select a doc first"); return
        code = self.lst_docs.get(sel[0]).split(" — ")[0]
        # switch to Editor tab and prefill
        self.notebook.select(self.tab_editor)
        self.ed_ec.set(code)
        self.load_existing_into_editor()

    def logout(self):
        if messagebox.askyesno("Logout", "Return to login?"):
            self.root.destroy()
            LoginWindow()

# helper functions used in multiple places
def read_docs_csv():
    return read_docs_csv_cached()

def read_docs_csv_cached():
    # simple wrapper to read fresh each time
    return read_docs_csv.__wrapped__() if hasattr(read_docs_csv, "__wrapped__") else _read_docs_csv_f()

def _read_docs_csv_f():
    return read_docs_csv.__wrapped__() if False else read_docs_csv_real()

def read_docs_csv_real():
    return read_docs_csv.__wrapped__() if hasattr(read_docs_csv, "__wrapped__") else read_docs_csv_base()

def read_docs_csv_base():
    # fallback: call read_docs_csv original
    return read_docs_csv.__globals__['read_docs_csv']()  # trick to call original

# But simpler: override read_docs_csv to actual implementation (fixing confusion)
def read_docs_csv_actual():
    return read_docs_csv.__globals__['read_docs_csv'].__wrapped__() if hasattr(read_docs_csv.__globals__['read_docs_csv'], "__wrapped__") else _read_docs_csv_simple()

def _read_docs_csv_simple():
    # direct implementation (same as function defined earlier)
    docs = {}
    with open(DOCS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                versions = json.loads(r.get("versions","[]") or "[]")
            except Exception:
                versions = []
            r["versions"] = versions
            docs[r["error_code"]] = r
    return docs

# Fix read_docs_csv to proper function
read_docs_csv = read_docs_csv_real if False else _read_docs_csv_simple

# same for write
def write_docs_csv(docs):
    rows = []
    for code, r in sorted(docs.items()):
        rr = {
            "error_code": code,
            "title": r.get("title",""),
            "created_by": r.get("created_by", ""),
            "created_at": r.get("created_at",""),
            "versions": json.dumps(r.get("versions", []), ensure_ascii=False)
        }
        rows.append(rr)
    with open(DOCS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["error_code", "title", "created_by", "created_at", "versions"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rr in rows:
            writer.writerow(rr)

# ensure wrappers used earlier work
write_docs_csv.__name__ = "write_docs_csv"

# adjust function references used earlier
# tie actual functions used in class methods
# (we already have implementations: _read_docs_csv_simple and write_docs_csv)

# final run
if __name__ == "__main__":
    # small sanity: ensure images folder exists
    os.makedirs(IMAGES_DIR, exist_ok=True)
    LoginWindow()
