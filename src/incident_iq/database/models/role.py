from .base_model import BaseModel


class RoleModel(BaseModel):
    table = 'roles'
    fields = ['id', 'name', 'guard', 'created_at', 'updated_at']


    def find_by_name(self, name):
        cur = self.conn.execute('SELECT * FROM roles WHERE name = ?', (name,))
        r = cur.fetchone()
        return dict(r) if r else None