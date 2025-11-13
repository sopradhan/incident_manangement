from .base_model import BaseModel

class DepartmentUserModel(BaseModel):
    table = 'department_users'
    fields = ['id', 'department_id', 'user_id', 'created_at']