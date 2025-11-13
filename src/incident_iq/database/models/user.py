from .base_model import BaseModel
from typing import List, Dict, Any

import hashlib

def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

class UserModel(BaseModel):
    table = 'users'
    fields = ['id', 'name', 'email', 'password', 'created_at', 'updated_at']


    def find_by_email(self, email):
        cur = self.conn.execute('SELECT * FROM users WHERE email = ?', (email,))
        r = cur.fetchone()

        return dict(r) if r else None
    
    def find_user_with_companies(self, user_id):
        sql = '''
        SELECT u.*, cu.company_id, c.name as company_name, cu.role as company_role
        FROM users u
        LEFT JOIN company_users cu ON u.id = cu.user_id
        LEFT JOIN companies c ON cu.company_id = c.id
        WHERE u.id = ?
        '''
        cur = self.conn.execute(sql, (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def find_user_with_departments(self, user_id):
        sql = '''
        SELECT u.*, du.department_id, d.name as department_name
        FROM users u
        LEFT JOIN department_users du ON u.id = du.user_id
        LEFT JOIN departments d ON du.department_id = d.id
        WHERE u.id = ?
        '''
        cur = self.conn.execute(sql, (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def find_user_with_roles(self, user_id):
        sql = '''
        SELECT u.*, r.name as role_name, r.guard
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.id = ?
        '''
        cur = self.conn.execute(sql, (user_id,))
        return [dict(row) for row in cur.fetchall()]

    def find_user_full_profile(self, user_id):
        sql = '''
        SELECT u.*, 
            cu.company_id, c.name as company_name, cu.role as company_role,
            du.department_id, d.name as department_name,
            r.name as role_name, r.guard
        FROM users u
        LEFT JOIN company_users cu ON u.id = cu.user_id
        LEFT JOIN companies c ON cu.company_id = c.id
        LEFT JOIN department_users du ON u.id = du.user_id
        LEFT JOIN departments d ON du.department_id = d.id
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.id = ?
        '''
        cur = self.conn.execute(sql, (user_id,))
        return [dict(row) for row in cur.fetchall()]
    
    def authenticate(self,email,password):
        cur = self.conn.execute('select password from users where email = ?',(email,))
        r = cur.fetchone()
        if not r:
            return False
        stored_hash = r['password']
        return stored_hash == _hash(password)
    
