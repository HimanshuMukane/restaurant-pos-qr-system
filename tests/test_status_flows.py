import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.views import sessions as sessions_view
from app.views import admin as admin_view
from app.views import analytics as analytics_view


class FakeCursor:
    def __init__(self, conn, rows=None, row=None):
        self._conn = conn
        self._rows = rows or []
        self._row = row

    def execute(self, sql, params=None):
        self._conn.queries.append((sql, params))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, rows=None, row=None):
        self.queries = []
        self._rows = rows or []
        self._row = row

    def cursor(self, *args, **kwargs):
        return FakeCursor(self, rows=self._rows, row=self._row)

    def commit(self):
        return None

    def close(self):
        return None


def _unwrap(fn):
    return inspect.unwrap(fn)


def test_cancel_table_marks_session_cancelled(monkeypatch):
    app = Flask(__name__)
    fake_conn = FakeConn()

    monkeypatch.setattr(sessions_view.db, "connect_db", lambda *_: fake_conn)
    monkeypatch.setattr(sessions_view.db, "get_session_service_type", lambda *_: "dine_in")
    monkeypatch.setattr(sessions_view.db, "get_session_by_id", lambda *_: ("sid", "T1", "active"))
    monkeypatch.setattr(sessions_view, "session_closed", lambda *a, **k: None)
    monkeypatch.setattr(sessions_view, "_push_state", lambda *a, **k: None)
    monkeypatch.setattr(sessions_view, "current_user", SimpleNamespace(id=1))
    monkeypatch.setattr(sessions_view, "url_for", lambda *a, **k: "/")
    monkeypatch.setattr(sessions_view, "redirect", lambda *a, **k: None)
    monkeypatch.setattr(sessions_view, "jsonify", lambda obj: obj)
    from utils.data import core as data_core
    monkeypatch.setattr(data_core, "connect_db", lambda *_: FakeConn())

    with app.test_request_context("/sessions/cancel_table/sid", headers={"Accept": "application/json"}):
        _unwrap(sessions_view.cancel_table)("sid")

    sqls = " ".join(q for q, _ in fake_conn.queries)
    assert "SET status='cancelled'" in sqls


def test_cancelled_sessions_api_filters_cancelled(monkeypatch):
    app = Flask(__name__)
    fake_conn = FakeConn(rows=[])
    monkeypatch.setattr(admin_view.db, "connect_db", lambda *_: fake_conn)

    with app.test_request_context("/admin/api/cancelled_sessions?from=2024-01-01&to=2024-01-31"):
        _unwrap(admin_view.cancelled_sessions_api)()

    sqls = " ".join(q for q, _ in fake_conn.queries)
    assert "s.status = 'cancelled'" in sqls


def test_outstanding_counts_active_only(monkeypatch):
    app = Flask(__name__)
    fake_conn = FakeConn(row={"outstanding_pre_tax_service": 0, "open_sessions": 0})
    monkeypatch.setattr(analytics_view.db, "connect_db", lambda *_: fake_conn)

    with app.test_request_context("/api/analytics/outstanding"):
        _unwrap(analytics_view.analytics_outstanding)()

    sqls = " ".join(q for q, _ in fake_conn.queries)
    assert "status = 'active'" in sqls
