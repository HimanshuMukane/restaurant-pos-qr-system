import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.services import reservations as svc_res


def test_auto_seat_verbose_reuses_existing_session(monkeypatch):
    calls = {}

    def _list_due(*_a, **_k):
        return [{
            "id": 10,
            "table_number": "A1",
            "session_id": "SID-10",
            "pax": 2,
            "guest_name": "Ada",
            "notes": "",
            "date": "2024-01-02",
            "time": "12:00",
        }]

    def _seat_existing(_ignored, reservation_id, table_number, session_id, by_user_id):
        calls["existing"] = (reservation_id, table_number, session_id, by_user_id)
        return session_id

    def _seat_new(*_a, **_k):
        calls["new"] = True
        return "NEW-SID"

    monkeypatch.setattr(svc_res.data_res, "list_due_reservations", _list_due)
    monkeypatch.setattr(svc_res, "seat_reservation_existing_session", _seat_existing)
    monkeypatch.setattr(svc_res, "seat_reservation", _seat_new)

    out = svc_res.auto_seat_due_reservations_verbose(None, window_min=30, opened_by_user_id=9)

    assert calls.get("existing") == (10, "A1", "SID-10", 9)
    assert "new" not in calls
    assert out and out[0]["session_id"] == "SID-10"


def test_auto_seat_reuses_existing_session(monkeypatch):
    calls = {"existing": 0, "new": 0}

    def _list_due(*_a, **_k):
        return [{
            "id": 11,
            "table_number": "B2",
            "session_id": "SID-11",
            "pax": 3,
            "guest_name": "Budi",
            "notes": "",
        }]

    def _seat_existing(*_a, **_k):
        calls["existing"] += 1
        return "SID-11"

    def _seat_new(*_a, **_k):
        calls["new"] += 1
        return "NEW-SID"

    monkeypatch.setattr(svc_res.data_res, "list_due_reservations", _list_due)
    monkeypatch.setattr(svc_res, "seat_reservation_existing_session", _seat_existing)
    monkeypatch.setattr(svc_res, "seat_reservation", _seat_new)

    count = svc_res.auto_seat_due_reservations(None, window_min=30, opened_by_user_id=7)

    assert count == 1
    assert calls["existing"] == 1
    assert calls["new"] == 0
