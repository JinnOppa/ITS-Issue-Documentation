import tkinter as tk
from services.csv_service import ensure_csv
from config.settings import *
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from services.auth_service import ensure_default_admin


def main():
    ensure_csv(USERS_CSV, [
        "username", "password_hash", "role",
        "created_at", "created_by", "is_active"
    ])
    ensure_default_admin()
    
    ensure_csv(ERRORS_MASTER_CSV, [
        "error_code", "error_type",
        "create_date", "created_by", "is_active"
    ])
    ensure_csv(ERROR_VERSIONS_CSV, [
        "error_code", "version", "error_name",
        "error_category", "content",
        "update_date", "updated_by", "is_latest"
    ])
    ensure_csv(ACTIVITY_LOGS_CSV, [
        "timestamp", "username", "role",
        "action", "error_code", "version", "remarks"
    ])

    root = tk.Tk()
    root.title("Error Documentation System")

    def on_login(user):
        for w in root.winfo_children():
            w.destroy()
        MainWindow(root, user)

    LoginWindow(root, on_login)
    root.mainloop()

if __name__ == "__main__":
    main()
