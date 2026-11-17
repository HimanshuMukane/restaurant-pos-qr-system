import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import events


def _reset_floor_cache():
    events._FLOOR_CACHE["ts"] = 0.0
    events._FLOOR_CACHE["map"] = {}


def test_session_items_changed_resolves_floor_from_layout(monkeypatch):
    _reset_floor_cache()

    def _map():
        return {"B2": "2"}

    calls = []

    def _publish(event, payload, *, outlet="DEMO", floor="1", table_number=None, session_id=None):
        calls.append(
            {
                "event": event,
                "payload": payload,
                "outlet": outlet,
                "floor": floor,
                "table_number": table_number,
                "session_id": session_id,
            }
        )

    monkeypatch.setattr(events, "_build_table_floor_map", _map)
    monkeypatch.setattr(events, "_table_number_for_session", lambda _sid: "B2")
    monkeypatch.setattr(events, "publish", _publish)
    monkeypatch.setattr(events, "push_table_state_changed", lambda *a, **k: None)

    events.session_items_changed(None, "SID-1")

    assert calls
    call = calls[0]
    assert call["event"] == "session_items_changed"
    assert call["floor"] == "2"
    assert call["table_number"] == "B2"
    assert call["payload"]["table_number"] == "B2"


def test_table_moved_broadcasts_to_both_floors(monkeypatch):
    _reset_floor_cache()

    def _map():
        return {"A1": "1", "B2": "2"}

    calls = []

    def _broadcast(event, payload, room=None, namespace=None):
        calls.append({"event": event, "room": room})

    monkeypatch.setattr(events, "_build_table_floor_map", _map)
    monkeypatch.setattr(events, "broadcast", _broadcast)

    events.table_moved("A1", "B2", "SID-2")

    rooms = {c["room"] for c in calls if c["room"]}
    assert "outlet:DEMO:floor:1" in rooms
    assert "outlet:DEMO:floor:2" in rooms
    assert "table:A1" in rooms
    assert "table:B2" in rooms
    assert "session:SID-2" in rooms


def test_push_table_state_changed_broadcasts_to_outlet_floor_table_and_session(monkeypatch):
    calls = []

    def _broadcast(event, payload, room=None, namespace=None):
        calls.append({"event": event, "payload": payload, "room": room})

    monkeypatch.setattr(
        events,
        "build_table_state_payload",
        lambda table_number=None, session_id=None, floor_hint=None: {
            "table_number": "B2",
            "floor": "2",
            "session_id": "SID-9",
            "occupied": True,
            "billing": False,
            "empty_session": False,
            "guest_name": "Nina",
            "total_amount": 125000,
            "has_unsent": True,
            "has_qr_unsent": True,
        },
    )
    monkeypatch.setattr(events, "broadcast", _broadcast)

    events.push_table_state_changed(table_number="B2", session_id="SID-9", outlet="DEMO", floor="2")

    rooms = {c["room"] for c in calls if c["room"]}
    assert "outlet:DEMO" in rooms
    assert "outlet:DEMO:floor:2" in rooms
    assert "table:B2" in rooms
    assert "session:SID-9" in rooms
    assert all(c["event"] == "table.state.changed" for c in calls)


def test_session_items_changed_also_pushes_table_state(monkeypatch):
    _reset_floor_cache()

    published = []
    pushed = []

    monkeypatch.setattr(events, "_build_table_floor_map", lambda: {"A1": "1"})
    monkeypatch.setattr(events, "publish", lambda *args, **kwargs: published.append((args, kwargs)))
    monkeypatch.setattr(
        events,
        "push_table_state_changed",
        lambda table_number=None, session_id=None, outlet="DEMO", floor="1": pushed.append(
            {
                "table_number": table_number,
                "session_id": session_id,
                "outlet": outlet,
                "floor": floor,
            }
        ),
    )

    events.session_items_changed("A1", "SID-7")

    assert published
    assert pushed == [
        {
            "table_number": "A1",
            "session_id": "SID-7",
            "outlet": "DEMO",
            "floor": "1",
        }
    ]
