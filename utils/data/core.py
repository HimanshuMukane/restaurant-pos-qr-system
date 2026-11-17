import os
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor
import json
import re
from datetime import datetime, date, time
from decimal import Decimal
from zoneinfo import ZoneInfo
from utils.tenancy import get_current_tenant_id

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "pos_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "pos_password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "pos_qr_db")

TZ = ZoneInfo("Asia/Jakarta")
UNPAID_STATUSES = ("new", "edited", "served", "printed")

TENANT_TABLES = {
    'sessions', 'order_items', 'payments', 'reservations',
    'reservation_items', 'floor_layouts', 'qr_orders', 'users', 'tenant_feedback'
}

class MySQLRowDict(dict):
    """A dict subclass that also supports indexing and iterating by integer position like a row/tuple."""
    def __init__(self, d, col_names):
        super().__init__(d)
        self._col_names = col_names

    def __getitem__(self, key):
        if isinstance(key, int):
            col = self._col_names[key]
            return super().__getitem__(col)
        return super().__getitem__(key)

    def get(self, key, default=None):
        if isinstance(key, int):
            if 0 <= key < len(self._col_names):
                col = self._col_names[key]
                return super().get(col, default)
            return default
        return super().get(key, default)

    def __iter__(self):
        for col in self._col_names:
            yield super().__getitem__(col)

    def keys(self):
        return super().keys()

    def values(self):
        return [super().__getitem__(c) for c in self._col_names]

    def items(self):
        return [(c, super().__getitem__(c)) for c in self._col_names]


class MySQLCompatCursor:
    def __init__(self, raw_cursor, conn):
        self._cur = raw_cursor
        self._conn = conn
        self._last_row_id = None
        self._description = None
        self._returning_id = False

    def _transform_query(self, query):
        if not isinstance(query, str):
            return query
        # Remove inline SQL comments (-- comment) before transforming
        q = re.sub(r'--[^\r\n]*', '', query)
        # Remove public. schema qualifier
        q = re.sub(r'\bpublic\.', '', q, flags=re.IGNORECASE)
        # Remove qr. schema qualifier
        q = re.sub(r'\bqr\.', '', q, flags=re.IGNORECASE)
        # ILIKE -> LIKE
        q = re.sub(r'\bILIKE\b', 'LIKE', q, flags=re.IGNORECASE)
        # Quote "timestamp" and "time" column identifiers for MySQL
        q = re.sub(r'\"timestamp\"', '`timestamp`', q, flags=re.IGNORECASE)
        q = re.sub(r'\"time\"', '`time`', q, flags=re.IGNORECASE)

        # Replace postgres to_timestamp(date || ' ' || time, ...) with STR_TO_DATE(CONCAT(date, ' ', time), '%%Y-%%m-%%d %%H:%%i')
        q = re.sub(
            r"to_timestamp\s*\(\s*([a-zA-Z0-9_`]+)\s*\|\|\s*' '\s*\|\|\s*([a-zA-Z0-9_`]+)\s*,\s*'YYYY-MM-DD HH24:MI'\s*\)",
            r"STR_TO_DATE(CONCAT(\1, ' ', \2), '%%Y-%%m-%%d %%H:%%i')",
            q,
            flags=re.IGNORECASE
        )
        # Replace AT TIME ZONE '...' or AT TIME ZONE %s with blank in MySQL
        q = re.sub(r"\s+AT\s+TIME\s+ZONE\s+('[^']+'|%s|\"[^\"]+\")", "", q, flags=re.IGNORECASE)

        # Strip postgres double colon casts like ::INT, ::NUMERIC(10,1), ::bigint, ::date, ::timestamp, etc.
        q = re.sub(r'::[a-zA-Z0-9_]+(\([0-9,\s]+\))?', '', q)
        # In MySQL TEXT is not a valid CAST type, replace CAST(... AS TEXT) with CAST(... AS CHAR)
        q = re.sub(r'\bAS\s+TEXT\b', 'AS CHAR', q, flags=re.IGNORECASE)

        # Check if query had RETURNING id
        if re.search(r'\s+RETURNING\s+', q, flags=re.IGNORECASE):
            self._returning_id = True
            q = re.sub(r'\s+RETURNING\s+.*$', '', q, flags=re.IGNORECASE | re.DOTALL)
        else:
            self._returning_id = False
        return q

    def _inject_tenant_insert(self, query, params):
        """If this is an INSERT INTO a tenant table and tenant_id isn't listed, inject it."""
        if not isinstance(query, str):
            return query, params
        m = re.match(r'^\s*INSERT\s+INTO\s+([a-zA-Z0-9_`]+)\s*\(([^)]+)\)\s*VALUES\s*\((.+)\)', query, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return query, params
        table_raw = m.group(1).replace('`', '').strip().lower()
        if table_raw not in TENANT_TABLES:
            return query, params
        cols = [c.strip().replace('`', '').lower() for c in m.group(2).split(',')]
        if 'tenant_id' in cols:
            return query, params

        new_cols = "tenant_id, " + m.group(2).strip()
        new_vals = "%s, " + m.group(3).strip()
        new_query = f"INSERT INTO {m.group(1)} ({new_cols}) VALUES ({new_vals})"

        tenant_id = get_current_tenant_id()
        if params is None:
            new_params = (tenant_id,)
        elif isinstance(params, (list, tuple)):
            new_params = (tenant_id, *params)
        elif isinstance(params, dict):
            new_params = dict(params)
            new_params['tenant_id'] = tenant_id
        else:
            new_params = (tenant_id, params)

        return new_query, new_params

    def _inject_tenant_where(self, query, params):
        """
        For SELECT, UPDATE, DELETE queries on single tenant tables (e.g. FROM sessions WHERE ...),
        if tenant_id is not already in the query, automatically append 'AND tenant_id = %s' or 'WHERE tenant_id = %s'.
        """
        if not isinstance(query, str):
            return query, params

        q_clean = query.strip()
        # Look for simple single-table pattern: FROM <table> WHERE ... or FROM <table> [LIMIT ...]
        # Avoid multi-table joins or queries that already filter tenant_id
        if re.search(r'\btenant_id\b', q_clean, flags=re.IGNORECASE):
            return query, params

        # Match: SELECT ... FROM <table_name> [WHERE ...]
        # or UPDATE <table_name> SET ... WHERE ...
        # or DELETE FROM <table_name> WHERE ...
        m_sel = re.match(r'^(SELECT\s+.+\s+FROM\s+([a-zA-Z0-9_`]+))(\s+WHERE\s+(.+?))?(\s+ORDER\s+BY.+|\s+LIMIT.+|\s+GROUP\s+BY.+)?$', q_clean, flags=re.IGNORECASE | re.DOTALL)
        if m_sel:
            tbl = m_sel.group(2).replace('`', '').strip().lower()
            if tbl in TENANT_TABLES:
                prefix = m_sel.group(1)
                where_clause = m_sel.group(4)
                suffix = m_sel.group(5) or ""
                tenant_id = get_current_tenant_id()
                if where_clause:
                    new_q = f"{prefix} WHERE ({where_clause}) AND tenant_id = %s{suffix}"
                else:
                    new_q = f"{prefix} WHERE tenant_id = %s{suffix}"

                if params is None:
                    new_params = (tenant_id,)
                elif isinstance(params, (list, tuple)):
                    new_params = (*params, tenant_id)
                elif isinstance(params, dict):
                    new_params = dict(params)
                    new_params['tenant_id'] = tenant_id
                else:
                    new_params = (params, tenant_id)
                return new_q, new_params

        m_upd = re.match(r'^(UPDATE\s+([a-zA-Z0-9_`]+)\s+SET\s+.+?\s+WHERE\s+)(.+)$', q_clean, flags=re.IGNORECASE | re.DOTALL)
        if m_upd:
            tbl = m_upd.group(2).replace('`', '').strip().lower()
            if tbl in TENANT_TABLES:
                prefix = m_upd.group(1)
                where_clause = m_upd.group(3)
                tenant_id = get_current_tenant_id()
                new_q = f"{prefix}({where_clause}) AND tenant_id = %s"
                if params is None:
                    new_params = (tenant_id,)
                elif isinstance(params, (list, tuple)):
                    new_params = (*params, tenant_id)
                elif isinstance(params, dict):
                    new_params = dict(params)
                    new_params['tenant_id'] = tenant_id
                else:
                    new_params = (params, tenant_id)
                return new_q, new_params

        m_del = re.match(r'^(DELETE\s+FROM\s+([a-zA-Z0-9_`]+)\s+WHERE\s+)(.+)$', q_clean, flags=re.IGNORECASE | re.DOTALL)
        if m_del:
            tbl = m_del.group(2).replace('`', '').strip().lower()
            if tbl in TENANT_TABLES:
                prefix = m_del.group(1)
                where_clause = m_del.group(3)
                tenant_id = get_current_tenant_id()
                new_q = f"{prefix}({where_clause}) AND tenant_id = %s"
                if params is None:
                    new_params = (tenant_id,)
                elif isinstance(params, (list, tuple)):
                    new_params = (*params, tenant_id)
                elif isinstance(params, dict):
                    new_params = dict(params)
                    new_params['tenant_id'] = tenant_id
                else:
                    new_params = (params, tenant_id)
                return new_q, new_params

        return query, params

    def execute(self, query, params=None):
        transformed = self._transform_query(query)
        transformed, params = self._inject_tenant_insert(transformed, params)
        transformed, params = self._inject_tenant_where(transformed, params)

        if params is not None:
            if isinstance(params, (list, tuple)):
                p_list = []
                for p in params:
                    if isinstance(p, (dict, list)):
                        p_list.append(json.dumps(p))
                    elif isinstance(p, bool):
                        p_list.append(1 if p else 0)
                    else:
                        p_list.append(p)
                res = self._cur.execute(transformed, tuple(p_list))
            elif isinstance(params, dict):
                p_dict = {}
                for k, v in params.items():
                    if isinstance(v, (dict, list)):
                        p_dict[k] = json.dumps(v)
                    elif isinstance(v, bool):
                        p_dict[k] = 1 if v else 0
                    else:
                        p_dict[k] = v
                res = self._cur.execute(transformed, p_dict)
            else:
                res = self._cur.execute(transformed, params)
        else:
            res = self._cur.execute(transformed)

        self._description = self._cur.description
        self._last_row_id = self._cur.lastrowid
        return res

    def executemany(self, query, seq_of_params):
        transformed = self._transform_query(query)
        return self._cur.executemany(transformed, seq_of_params)

    def _wrap_row(self, row):
        if row is None:
            return None
        col_names = [col[0] for col in self._cur.description] if self._cur.description else list(row.keys())
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                v = float(v) if (v % 1) != 0 else int(v)
            elif isinstance(v, (bytes, bytearray)):
                try:
                    v = v.decode('utf-8')
                except Exception:
                    pass
            clean_row[k] = v
        return MySQLRowDict(clean_row, col_names)

    def fetchone(self):
        if self._returning_id:
            self._returning_id = False
            lid = self._cur.lastrowid
            if lid:
                return MySQLRowDict({"id": lid}, ["id"])
        row = self._cur.fetchone()
        return self._wrap_row(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [self._wrap_row(r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cur.fetchmany(size)
        return [self._wrap_row(r) for r in rows]

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def description(self):
        return self._cur.description

    def close(self):
        self._cur.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MySQLCompatConnection:
    def __init__(self, raw_conn):
        self._raw_conn = raw_conn

    def cursor(self, row_factory=None):
        raw_cur = self._raw_conn.cursor(DictCursor)
        return MySQLCompatCursor(raw_cur, self)

    def commit(self):
        self._raw_conn.commit()

    def rollback(self):
        self._raw_conn.rollback()

    def close(self):
        self._raw_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def connect_db(_ignored=None):
    """Returns a MySQL compatibility connection."""
    raw = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False
    )
    return MySQLCompatConnection(raw)
