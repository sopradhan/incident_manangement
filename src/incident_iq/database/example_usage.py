from db.connection import get_connection
from models.user import UserModel
from models.company_user import CompanyUserModel
from models.user_role import UserRoleModel

conn = get_connection()
users = UserModel(conn)

# 🟢 CREATE
new_user_id = {
    'name': 'bob',
    'email': 'bob@example.com',
    'password': '_hash(pw_123)'
}

# users.insert(new_user_id)
# print("New user created:", users.find(new_user_id))

# # 🟡 READ
# all_users = users.all()
# print("All Users:", all_users)

# # 🔵 UPDATE
# users.update(new_user_id, {'name': 'Charlie Brown'})
# print("Updated:", users.find(new_user_id))

# # 🔴 DELETE
# users.delete(7)
# print("After delete:", users.find(7))

# # 📎 Check user roles
# user_roles = UserRoleModel(conn).for_user(1)
# print("Roles for Root User:", user_roles)

# 🏢 Check company users
# company_users = CompanyUserModel(conn).for_company(2)
# print("Company users for Acme Corp:", company_users)

# user1= UserModel(conn).find_user_full_profile(2)
# print("User full details:", company_users)

# user2 = UserModel(conn).find_user_with_roles(3)
# print("User details with:", company_users)

auth= users.authenticate("svk@example.com","souvik123")
print(auth)

rows = users.raw_execute("SELECT * FROM users WHERE email = ?", ('svk@example.com',))
for row in rows:
    print(dict(row)) 

# users.raw_execute(
#     "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
#     ('Charl', 'charl@example.com', 'hashed_pw_123')
# )

