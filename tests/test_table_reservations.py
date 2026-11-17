import inspect
from types import SimpleNamespace
from datetime import datetime as real_datetime

from flask import Flask

from app.views import sessions as sessions_view


def _unwrap(fn):
    return inspect.unwrap(fn)


class _FixedDateTime:
    @classmethod
    def now(cls):
        return real_datetime(2024, 1, 2, 9, 0, 0)


def _base_monkeypatch(monkeypatch, created):
    monkeypatch.setattr(sessions_view.db, "get_session_by_table", lambda *_: None)
    monkeypatch.setattr(sessions_view.svc_res, "get_lockout_for_table", lambda *_: None)
    monkeypatch.setattr(sessions_view.svc_res, "get_next_for_table_today", lambda *_: None)
    monkeypatch.setattr(sessions_view.db, "list_future_reservations_for_table", lambda *_: [])
    monkeypatch.setattr(sessions_view, "push_reservation_changed_deferred", lambda *a, **k: None)
    monkeypatch.setattr(sessions_view.svc_res, "_make_ts_iso", lambda *_: None)
    monkeypatch.setattr(sessions_view, "flash", lambda *a, **k: None)
    monkeypatch.setattr(sessions_view, "render_template", lambda *a, **k: "ok")
    monkeypatch.setattr(
        sessions_view,
        "current_user",
        SimpleNamespace(id=7, role="admin", is_authenticated=True),
    )

    def _create(_ignored, **kwargs):
        created.update(kwargs)
        return 123

    monkeypatch.setattr(sessions_view.data_res, "create_reservation_with_table", _create)


def test_open_reservation_defaults_date_and_uses_hour_minute(monkeypatch):
    app = Flask(__name__)
    created = {}
    _base_monkeypatch(monkeypatch, created)
    monkeypatch.setattr(sessions_view, "datetime", _FixedDateTime)

    with app.test_request_context(
        "/table/T1",
        method="POST",
        data={
            "kind": "open_reservation",
            "guest_name": "Alice",
            "pax": "2",
            "hour": "9",
            "minute": "5",
            "dp_amount": "0",
        },
    ):
        _unwrap(sessions_view.view_table)("T1")

    assert created["date"] == "2024-01-02"
    assert created["time"] == "09:05"
    assert created["table_number"] == "T1"


def test_open_reservation_parses_seconds_and_ddmmyyyy(monkeypatch):
    app = Flask(__name__)
    created = {}
    _base_monkeypatch(monkeypatch, created)
    monkeypatch.setattr(sessions_view, "datetime", _FixedDateTime)

    with app.test_request_context(
        "/table/T2",
        method="POST",
        data={
            "kind": "open_reservation",
            "guest_name": "Bob",
            "pax": "3",
            "date": "02/01/2024",
            "time": "7:30:00",
            "dp_amount": "0",
        },
    ):
        _unwrap(sessions_view.view_table)("T2")

    assert created["date"] == "2024-01-02"
    assert created["time"] == "07:30"
    assert created["table_number"] == "T2"
