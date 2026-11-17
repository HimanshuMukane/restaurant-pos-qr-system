import os
from flask_login import UserMixin
from utils.data.core import connect_db
from psycopg.rows import dict_row
from utils.tenancy import get_current_tenant_id

DEMO_ALIASES = {
    "admin":   {"password": "admin123",   "role": "admin",   "label": "Admins"},
    "cashier": {"password": "cashier123", "role": "cashier", "label": "Cashiers"},
    "waiter":  {"password": "waiter123",  "role": "waiter",  "label": "Waiters"},
}

def _conn():
    return connect_db()

def get_user_by_id(_db_path, user_id):
    with _conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT id, tenant_id, username, full_name, password_hash, role, is_active, demo_password_plain
            FROM users WHERE id = %s
        """, (user_id,))
        return cur.fetchone()

def get_user_by_username(_db_path, username, tenant_id=None):
    if not tenant_id:
        tenant_id = get_current_tenant_id()
    with _conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT id, tenant_id, username, full_name, password_hash, role, is_active, demo_password_plain
            FROM users WHERE username = %s AND (tenant_id = %s OR %s = '')
            LIMIT 1
        """, (username, tenant_id, tenant_id))
        return cur.fetchone()

def get_active_user_by_role(_db_path, role, tenant_id=None):
    if not tenant_id:
        tenant_id = get_current_tenant_id()
    with _conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT id, tenant_id, username, full_name, password_hash, role, is_active, demo_password_plain
            FROM users
            WHERE role = %s
              AND (tenant_id = %s OR %s = '')
              AND is_active = 1
            ORDER BY id
            LIMIT 1
        """, ((role or "").strip().lower(), tenant_id, tenant_id))
        return cur.fetchone()

def get_demo_alias(username):
    return DEMO_ALIASES.get((username or "").strip().lower())

def build_demo_users(_db_path, configured_groups):
    out = []
    role_cache = {}
    for group in configured_groups or []:
        built_entries = []
        for entry in group.get("entries") or []:
            role = (entry.get("role") or "").strip().lower()
            if role and role not in role_cache:
                role_cache[role] = get_active_user_by_role(_db_path, role)
            row = role_cache.get(role)
            built_entries.append({
                "username": entry.get("username") or "",
                "password": ((row or {}).get("demo_password_plain") or entry.get("password") or ""),
                "role": role,
            })
        out.append({
            "label": group.get("label") or "",
            "entries": built_entries,
        })
    return out

class User(UserMixin):
    def __init__(self, row):
        base = dict(row)
        self.id = base["id"]
        self.username = base.get("display_username") or base["username"]
        self.full_name = base.get("display_full_name") or base.get("full_name") or self.username
        self.password_hash = base.get("password_hash")
        self.role = base.get("role") or "viewer"
        self.is_active_user = bool(base.get("is_active", 1))
        self.demo_alias = base.get("demo_alias")
        self.demo_password_plain = base.get("demo_password_plain")
        self.tenant_id = base.get("tenant_id", "default")

    @property
    def is_active(self):
        return self.is_active_user

    @property
    def is_admin(self):
        return self.role == "admin"
    @property
    def is_cashier(self):
        return self.role == "cashier"
    @property
    def is_waiter(self):
        return self.role == "waiter"
    @property
    def is_viewer(self):
        return self.role == "viewer"
