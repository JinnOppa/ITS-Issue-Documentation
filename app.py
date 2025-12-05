# PART 1.3
# app.py
import streamlit as st
from services import auth
from services import db as db_module

st.set_page_config(page_title="IT Docs System", layout="wide")

# Ensure DB is initialized (import side-effect already does this)
# but call the functions to be safe
db_module.initialize_db()
db_module.create_default_admin_if_missing()

# session user
if "user" not in st.session_state:
    st.session_state["user"] = None

def login_page():
    st.title("IT Documentation System — Login")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            ok, res = auth.authenticate_user(username.strip(), password)
            if ok:
                st.session_state["user"] = res
                st.success(f"Logged in as {res['username']} ({res['role']})")
                st.rerun()
            else:
                st.error(res)

def logout():
    st.session_state["user"] = None
    st.rerun()

def admin_lead_dashboard(user):
    st.header(f"Admin Lead Dashboard — {user['username']}")
    menu = st.sidebar.selectbox("Choose action", ["View Docs", "Create Docs", "User Management"])
    if menu == "User Management":
        user_management_page(user)
    elif menu == "View Docs":
        st.info("Viewer page — Part 2 coming")
    elif menu == "Create Docs":
        st.info("Create Docs — Part 2 coming")

def admin_regular_dashboard(user):
    st.header(f"Admin Regular Dashboard — {user['username']}")
    menu = st.sidebar.selectbox("Choose action", ["View Docs", "Create Docs", "User Management"])
    if menu == "User Management":
        user_management_page(user)
    elif menu == "View Docs":
        st.info("Viewer page — Part 2 coming")
    elif menu == "Create Docs":
        st.info("Create Docs — Part 2 coming")

def regular_user_dashboard(user):
    st.header(f"User Dashboard — {user['username']}")
    st.info("Viewer page — Part 2 coming")

# User listing (for admin lead and admin regular)
def user_list_page(current_user):
    st.subheader("User List")
    if not auth.can_view_users(current_user):
        st.error("You are not authorized to view users.")
        return
    rows = auth.list_users()
    for r in rows:
        st.write(f"- {r['id']} — **{r['username']}** — {r['role']} — created: {r['date_created']}")

# Full user management page (create + view + delete maybe later) — only admin_lead
def user_management_page(current_user):
    if not auth.can_manage_users(current_user):
        st.error("You are not authorized to manage users.")
        return

    st.subheader("Create User")

    # determine UI allowed roles
    if current_user["role"] == "admin_lead":
        allowed_roles = ("admin_lead", "admin_regular", "regular_user")
    elif current_user["role"] == "admin_regular":
        allowed_roles = ("regular_user",)
    else:
        allowed_roles = ()

    # show CREATE form only if roles exist
    if allowed_roles:
        with st.form("create_user_form"):
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")
            role_choice = st.selectbox("Role", allowed_roles)

            submitted = st.form_submit_button("Create")

            if submitted:
                ok, err = auth.create_user(
                    new_username.strip(),
                    new_password,
                    role_choice,
                    creator_role=current_user["role"]
                )
                if ok:
                    st.success(f"User '{new_username}' created with role '{role_choice}'.")
                    st.rerun()
                else:
                    st.error(f"Failed to create user: {err}")

    st.write("---")
    st.subheader("Existing Users")
    user_list_page(current_user)

# def user_management_page(current_user):
#     if not auth.can_manage_users(current_user):
#         st.error("You are not authorized to manage users.")
#         return

#     st.subheader("Create User")
#     with st.form("create_user_form"):
#         new_username = st.text_input("Username", key="new_username")
#         new_password = st.text_input("Password", type="password", key="new_password")
#         # allowed roles shown in UI depending on creator role
#         allowed_roles = ("admin_lead","admin_regular", "regular_user")
#         role_choice = st.selectbox("Role", allowed_roles)
#         submitted = st.form_submit_button("Create")
#         if submitted:
#             # server-side: pass creator_role for authorization
#             ok, err = auth.create_user(new_username.strip(), new_password, role_choice, creator_role=current_user["role"])
#             if ok:
#                 st.success(f"User '{new_username}' created with role '{role_choice}'.")
#             else:
#                 st.error(f"Failed to create user: {err}")

#     st.write("---")
#     st.subheader("Existing Users")
#     user_list_page(current_user)

# Main router
def main():
    if st.session_state["user"] is None:
        login_page()
    else:
        user = st.session_state["user"]
        st.sidebar.write(f"Logged in as **{user['username']}** ({user['role']})")
        if st.sidebar.button("Logout"):
            logout()

        # route by role
        if user["role"] == "admin_lead":
            admin_lead_dashboard(user)
        elif user["role"] == "admin_regular":
            admin_regular_dashboard(user)
        else:
            regular_user_dashboard(user)

if __name__ == "__main__":
    main()


# PART 1.2
# import streamlit as st
# from services import auth

# st.set_page_config(page_title="IT Documentation System", layout="wide")

# # ----- LOGIN FORM -----
# def login_form():
#     st.title("Login")

#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")

#     if st.button("Login"):
#         ok, result = auth.authenticate_user(username, password)
#         if ok:
#             st.session_state["user"] = result
#             st.success("Login successful!")
#             st.rerun()
#         else:
#             st.error(result)

# def logout():
#     st.session_state.user = None
#     st.rerun()

# # ----- MAIN APP -----
# def main_app(user):
#     st.sidebar.title("Menu")
#     st.sidebar.write(f"Logged in as: **{user['username']}** ({user['role']})")
#     if st.sidebar.button("Logout"):
#         logout()

#     # ----- MENU BY ROLE -----
#     if user["role"] == "admin_lead":
#         menu = ["View Docs", "Create Docs", "User Management"]
#     elif user["role"] == "admin_regular":
#         menu = ["View Docs", "Create Docs", "User List"]
#     else:
#         menu = ["View Docs"]

#     choice = st.sidebar.selectbox("Select Page", menu)

#     st.title(choice)

#     if choice == "User Management":
#         st.info("User Management page (will be added in later parts)")

#     elif choice == "User List":
#         st.info("User List page (view-only) - to be implemented.")

#     elif choice == "View Docs":
#         st.info("Documentation viewer (Part 2)")

#     elif choice == "Create Docs":
#         st.info("Documentation creation (Part 2)")


# # ----- ROUTER -----
# if "user" not in st.session_state:
#     login_form()
# else:
#     main_app(st.session_state["user"])



# PART 1.1

# # app.py
# import streamlit as st
# from services import auth
# from services.db import ensure_folders
# import services.db as db_module

# st.set_page_config(page_title="IT Docs System (Streamlit)", layout="wide")
# ensure_folders()  # ensure images/ and db folder exist

# # Simple session helpers
# if "user" not in st.session_state:
#     st.session_state.user = None

# def login_form():
#     st.title("IT Documentation System — Login")
#     with st.form("login_form"):
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")
#         submitted = st.form_submit_button("Login")
#         if submitted:
#             ok, res = auth.authenticate_user(username.strip(), password)
#             if ok:
#                 st.session_state.user = res
#                 st.success(f"Logged in as {res['username']} ({res['role']})")
#                 st.rerun()
#             else:
#                 st.error(res)

# def admin_dashboard():
#     st.title("Admin Dashboard")
#     st.write(f"Hello **{st.session_state.user['username']}** (admin)")
#     st.markdown("**Next steps:**\n\n- Create / update documentation (coming next)\n- Manage users (create, remove)")
#     st.divider()
#     # Quick create user form for testing
#     st.subheader("Create test user")
#     with st.form("create_user_form"):
#         u = st.text_input("username", value="testuser")
#         p = st.text_input("password", value="password123")
#         role = st.selectbox("role", ["user", "admin"])
#         submitted = st.form_submit_button("Create user")
#         if submitted:
#             ok, err = auth.create_user(u.strip(), p, role)
#             if ok:
#                 st.success(f"User '{u}' created.")
#             else:
#                 st.error(f"Failed to create user: {err}")

# def user_viewer():
#     st.title("Documentation Viewer")
#     st.write(f"Hello **{st.session_state.user['username']}** (regular user)")
#     st.markdown("Viewer page will allow searching and viewing documentation (coming next).")

# def logout():
#     st.session_state.user = None
#     st.rerun()

# # App routing
# if not st.session_state.user:
#     login_form()
# else:
#     st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}**")
#     st.sidebar.write(f"Role: **{st.session_state.user['role']}**")
#     if st.sidebar.button("Logout"):
#         logout()

#     if st.session_state.user["role"] == "admin":
#         st.sidebar.header("Admin Menu")
#         choice = st.sidebar.radio("Go to", ["Dashboard"])
#         if choice == "Dashboard":
#             admin_dashboard()
#     else:
#         st.sidebar.header("User Menu")
#         choice = st.sidebar.radio("Go to", ["Viewer"])
#         if choice == "Viewer":
#             user_viewer()
