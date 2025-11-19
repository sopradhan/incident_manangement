from .base_model import BaseModel

class DepartmentModel(BaseModel):
    table = 'departments'
    fields = ['id', 'company_id', 'name', 'created_at', 'updated_at']

    def for_company(self, company_id):
        cur = self.conn.execute('SELECT * FROM departments WHERE company_id = ?', (company_id,))
        return [dict(r) for r in cur.fetchall()]