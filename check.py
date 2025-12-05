from services.db import update_user, delete_user

# test update username
update_user(2, new_username="updatedname")

# test update password hash
update_user(2, new_password_hash="$2b$12$abcd....")

# test update role
update_user(2, new_role="regular_user")

# test delete
delete_user(3)
