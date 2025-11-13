from .base_model import BaseModel

class CompanyUserModel(BaseModel):
    table = 'company_users'
    fields = ['id', 'company_id', 'user_id', 'role', 'created_at']

    def add(self, company_id, user_id, role=None):
        try:
            cur = self.conn.execute('INSERT INTO company_users (company_id, user_id, role) VALUES (?, ?, ?)', (company_id, user_id, role))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            return None

    def for_company(self, company_id):
        cur = self.conn.execute('''
        SELECT cu.*, u.name AS user_name, u.email FROM company_users cu
        JOIN users u ON u.id = cu.user_id
        WHERE cu.company_id = ?
        ''', (company_id,))
        return [dict(r) for r in cur.fetchall()]