from .base_model import BaseModel


class CompanyModel(BaseModel):
    table = 'companies'
    fields = ['id', 'name', 'created_at', 'updated_at']

    def find_by_name(self, name):
        cur = self.conn.execute('SELECT * FROM companies WHERE name = ?', (name,))
        r = cur.fetchone()
        return dict(r) if r else None