from .base_model import BaseModel


class UserRoleModel(BaseModel):
    table = 'user_roles'
    fields = ['id', 'user_id', 'role_id', 'company_id', 'created_at']

    def assign(self, user_id, role_id, company_id=None):
        try:
            cur = self.conn.execute('INSERT INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (user_id, role_id, company_id))
            self.conn.commit()
            return cur.lastrowid
        except Exception as e:
        # could be unique constraint violation
            return None

    def for_user(self, user_id):
        cur = self.conn.execute('''
        SELECT ur.*, r.name as role_name FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = ?
        ''', (user_id,))
        return [dict(r) for r in cur.fetchall()]