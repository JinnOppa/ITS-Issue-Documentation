import tkinter as tk
from tkinter import ttk
import csv
from config.settings import ERROR_VERSIONS_CSV

class ViewErrorWindow(tk.Toplevel):
    def __init__(self, master, error_code):
        super().__init__(master)
        self.error_code = error_code
        self.title(f"View Documentation - {error_code}")
        self.geometry("700x500")

        tk.Label(self, text="Version").pack(anchor="w")

        self.version_cb = ttk.Combobox(self, state="readonly")
        self.version_cb.pack(fill="x")
        self.version_cb.bind("<<ComboboxSelected>>", self.load_content)

        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill="both", expand=True)

        self.text.tag_config("b", font=("Arial", 10, "bold"))
        self.text.tag_config("i", font=("Arial", 10, "italic"))
        self.text.tag_config("u", underline=1)

        self.load_versions()

    # def load_versions(self):
    #     versions = []
    #     with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
    #         for r in csv.DictReader(f):
    #             if r["error_code"] == self.error_code and r["is_active"] == "True":
    #                 versions.append(r["version"])

    #     self.version_cb["values"] = versions
    #     if versions:
    #         self.version_cb.set(versions[-1])
    #         self.load_content()
    def load_versions(self):
        versions = []

        with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["error_code"] == self.error_code and r["is_active"] == "True":
                    versions.append(str(r["version"]))  # FORCE STRING

        versions.sort()
        self.version_cb["values"] = versions

        if versions:
            self.version_cb.set(versions[-1])
            self.load_content()

    # def load_content(self, event=None):
    #     self.text.config(state="normal")
    #     self.text.delete("1.0", "end")

    #     version = self.version_cb.get()

    #     with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
    #         for r in csv.DictReader(f):
    #             if r["error_code"] == self.error_code and r["version"] == version:
    #                 self.render_content(r["content"])
    #                 break

    #     self.text.config(state="disabled")

    def load_content(self, event=None):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")

        version = self.version_cb.get()
        found = False

        with open(ERROR_VERSIONS_CSV, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (
                    r["error_code"] == self.error_code
                    and str(r["version"]) == str(version)
                    and r["is_active"] == "True"
                ):
                    self.render_content(r["content"])
                    found = True
                    break

        if not found:
            self.text.insert("end", "[No content found for this version]")

        self.text.config(state="disabled")


    # def render_content(self, raw):
    #     i = 0
    #     while i < len(raw):
    #         if raw.startswith("[B]", i):
    #             j = raw.find("[/B]", i)
    #             self.text.insert("end", raw[i+3:j], "b")
    #             i = j + 4
    #         elif raw.startswith("[I]", i):
    #             j = raw.find("[/I]", i)
    #             self.text.insert("end", raw[i+3:j], "i")
    #             i = j + 4
    #         elif raw.startswith("[U]", i):
    #             j = raw.find("[/U]", i)
    #             self.text.insert("end", raw[i+3:j], "u")
    #             i = j + 4
    #         else:
    #             self.text.insert("end", raw[i])
    #             i += 1

    def render_content(self, raw):
        if not raw:
            return

        i = 0
        while i < len(raw):
            if raw.startswith("[B]", i):
                j = raw.find("[/B]", i)
                self.text.insert("end", raw[i+3:j], "b")
                i = j + 4
            elif raw.startswith("[I]", i):
                j = raw.find("[/I]", i)
                self.text.insert("end", raw[i+3:j], "i")
                i = j + 4
            elif raw.startswith("[U]", i):
                j = raw.find("[/U]", i)
                self.text.insert("end", raw[i+3:j], "u")
                i = j + 4
            else:
                self.text.insert("end", raw[i])
                i += 1

