import inspect
import sys
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.views import reservations as reservations_view


def _unwrap(fn):
    return inspect.unwrap(fn)


class FakeCursor:
    def __init__(self, rows, sess_rows, queries):
        self._rows = rows
        self._sess_rows = sess_rows
        self._queries = queries
        self._last_sql = ""

    def execute(self, sql, params=None):
        self._last_sql = sql or ""
        self._queries.append(self._last_sql)

    def fetchall(self):
        if "FROM public.reservations" in self._last_sql:
            return list(self._rows)
        if "FROM public.sessions" in self._last_sql:
            return list(self._sess_rows)
        return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, rows, sess_rows, queries):
        self._rows = rows
        self._sess_rows = sess_rows
        self._queries = queries

    def cursor(self, *args, **kwargs):
        return FakeCursor(self._rows, self._sess_rows, self._queries)

    def close(self):
        return None


def test_lookup_includes_walkins_without_guest_name(monkeypatch):
    app = Flask(__name__)

    queries = []
    rows = []  # no reservations
    sess_rows = [
        ("sid1", 17, "", 1, "2024-01-02", "09:00", None),
    ]

    monkeypatch.setattr(
        reservations_view.db,
        "connect_db",
        lambda *_: FakeConn(rows, sess_rows, queries),
    )
    monkeypatch.setattr(reservations_view.db, "load_tables", lambda *_: [])
    monkeypatch.setattr(
        reservations_view,
        "render_template",
        lambda *_args, **kwargs: kwargs,
    )

    with app.test_request_context("/reservations/lookup"):
        out = _unwrap(reservations_view.reservations_lookup)()

    items = out["items"]
    assert len(items) == 1
    assert items[0]["kind"] == "session"
    assert items[0]["display_name"] == "Meja 17"

    assert all("table_number::text" not in (q or "") for q in queries)


def test_lookup_excludes_empty_and_res_tables(monkeypatch):
    app = Flask(__name__)

    queries = []
    rows = []
    sess_rows = [
        ("sid1", "", "Guest", 1, "2024-01-02", "09:00", None),
        ("sid2", "RES:123", "Guest", 1, "2024-01-02", "09:01", None),
        ("sid3", "A1", "Guest", 1, "2024-01-02", "09:02", None),
    ]

    monkeypatch.setattr(
        reservations_view.db,
        "connect_db",
        lambda *_: FakeConn(rows, sess_rows, queries),
    )
    monkeypatch.setattr(reservations_view.db, "load_tables", lambda *_: [])
    monkeypatch.setattr(
        reservations_view,
        "render_template",
        lambda *_args, **kwargs: kwargs,
    )

    with app.test_request_context("/reservations/lookup"):
        out = _unwrap(reservations_view.reservations_lookup)()

    items = out["items"]
    ids = {i["session_id"] for i in items if i["kind"] == "session"}
    assert ids == {"sid3"}
