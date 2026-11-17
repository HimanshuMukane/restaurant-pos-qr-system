import os
from datetime import datetime, timedelta
from threading import Lock
from flask_socketio import SocketIO, emit, join_room
from flask_login import current_user
from flask import current_app

POS_NS = "/pos"

def _origins():
    raw = os.getenv("CORS_ALLOW", "*")
    return [o.strip() for o in raw.split(",")] if raw else "*"

socketio = SocketIO(
    cors_allowed_origins=_origins(),
    async_mode=os.getenv("SOCKETIO_ASYNC_MODE", "threading"),
    manage_session=False,   # let Flask-Login manage the session cookie
    ping_interval=25,
    ping_timeout=60,
    logger=True,
    engineio_logger=True,
)

def init_socketio(app):
    socketio.init_app(
        app,
        message_queue=os.getenv("SOCKETIO_REDIS_URL") or os.getenv("REDIS_URL")
    )
    return socketio

# ===========================
# Auto-seat background thread
# ===========================
_AUTO_THREAD_STARTED = False
_AUTO_THREAD_LOCK = Lock()

# env toggles
_AUTO_ENABLED  = os.getenv("RESERVATIONS_AUTO_SEAT_ENABLED", "1").lower() not in ("0", "false", "no")
_AUTO_INTERVAL = int(os.getenv("RESERVATIONS_AUTO_SEAT_INTERVAL", "60"))  # seconds

def _start_auto_thread():
    """Start the auto-seat loop once (idempotent)."""
    global _AUTO_THREAD_STARTED
    if not _AUTO_ENABLED:
        return
    with _AUTO_THREAD_LOCK:
        if _AUTO_THREAD_STARTED:
            return
        _AUTO_THREAD_STARTED = True
        socketio.start_background_task(_auto_loop)

# ===========================
# Nightly demo reset thread
# ===========================
_NIGHTLY_THREAD_STARTED = False
_NIGHTLY_THREAD_LOCK = Lock()

# Run at this hour each night (24h, local server time). Override with DEMO_RESET_HOUR env var.
_NIGHTLY_RESET_HOUR = int(os.getenv("DEMO_RESET_HOUR", "3"))


def _start_nightly_thread(app):
    """Start the nightly demo reset loop once (idempotent). No-op if not in DEMO_MODE."""
    global _NIGHTLY_THREAD_STARTED
    if not app.config.get("DEMO_MODE"):
        return
    with _NIGHTLY_THREAD_LOCK:
        if _NIGHTLY_THREAD_STARTED:
            return
        _NIGHTLY_THREAD_STARTED = True
        socketio.start_background_task(_nightly_loop)


def _nightly_loop():
    while True:
        # Sleep until next occurrence of _NIGHTLY_RESET_HOUR
        now = datetime.now()
        target = now.replace(hour=_NIGHTLY_RESET_HOUR, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        seconds_to_sleep = (target - datetime.now()).total_seconds()
        socketio.sleep(max(seconds_to_sleep, 0))

        try:
            from utils.demo_seed import run_nightly_reset
            run_nightly_reset()
            if current_app:
                current_app.logger.info("[DEMO] Nightly reset completed.")
        except Exception:
            if current_app:
                current_app.logger.exception("[DEMO] Nightly reset failed.")


def push_session_created(table_number: str, session_id: str, ts_iso: str | None = None):
    payload = {"table_number": str(table_number), "session_id": str(session_id)}
    if ts_iso is not None:  # include key only if provided
        payload["ts_iso"] = ts_iso
    broadcast("session_created", payload)
    broadcast("session_created", payload, room=f"table:{table_number}")
    try:
        from .events import push_table_state_changed
        push_table_state_changed(table_number=table_number, session_id=session_id)
    except Exception:
        pass

def _auto_loop():
    """Every _AUTO_INTERVAL seconds, auto-seat due reservations and broadcast."""
    from utils.services import reservations as svc_res  # local import to avoid circulars
    while True:
        try:
            seated = svc_res.auto_seat_due_reservations_verbose(
                None,
                window_min=svc_res.AUTO_SEAT_MIN,
                opened_by_user_id=0,  # system user
            )
            for row in seated:
                tn  = row.get("table_number")
                sid = row.get("session_id")
                tsi = row.get("ts_iso")  # scheduled timestamp of the reservation (for reference)

                if not tn or not sid:
                    continue

                # 1) tell everyone a reservation was auto-seated (reservations pages listen to this)
                payload = {"table_number": str(tn), "session_id": str(sid)}
                if tsi is not None:
                    payload["ts_iso"] = tsi
                broadcast("reservations.autoseated", payload)
                broadcast("reservations.autoseated", payload, room=f"table:{tn}")

                # 2) also tell floor dashboards "a session was created"
                push_session_created(tn, sid, tsi)

                # 3) clear any residual reservation overlay for that table for all listeners
                push_reservation_changed(tn, None)

        except Exception:  # never crash the loop
            if current_app:
                current_app.logger.exception("[AUTO-SEAT] background loop error")
        # cooperative sleep (works with eventlet/gevent/threading)
        socketio.sleep(_AUTO_INTERVAL)

# ---------------------------
# Authenticated connections
# ---------------------------
@socketio.on("connect", namespace=POS_NS)
def _on_connect():
    # Ensure only logged-in users connect
    if not getattr(current_user, "is_authenticated", False):
        return False
    emit("connected", {"user": getattr(current_user, "username", None)})
    # Start background loops once
    _start_auto_thread()
    _start_nightly_thread(current_app._get_current_object())

# ---------------------------
# Room subscription helpers
# ---------------------------
@socketio.on("hello", namespace=POS_NS)
def _hello(msg):
    outlet = (msg or {}).get("outlet") or "DEMO"
    floor  = (msg or {}).get("floor") or "1"
    join_room(f"outlet:{outlet}")
    join_room(f"outlet:{outlet}:floor:{floor}")
    emit("subscribed", {"rooms": [f"outlet:{outlet}", f"outlet:{outlet}:floor:{floor}"]})

@socketio.on("watch.table", namespace=POS_NS)
def _watch_table(data):
    t = str((data or {}).get("table") or (data or {}).get("table_number") or (data or {}).get("table_id") or "").strip()
    if not t:
        emit("error", {"message": "table required"}); return
    join_room(f"table:{t}")
    emit("subscribed", {"rooms": [f"table:{t}"]})

@socketio.on("watch.session", namespace=POS_NS)
def _watch_session(data):
    s = str((data or {}).get("session_id") or "").strip()
    if not s:
        emit("error", {"message":"session_id required"}); return
    join_room(f"session:{s}")
    emit("subscribed", {"rooms": [f"session:{s}"]})

# ---------------------------
# Emit utilities
# ---------------------------
def broadcast(event, payload, room=None, namespace=POS_NS):
    """Backwards-compatible broadcast() you already use."""
    if room:
        socketio.emit(event, payload, room=room, namespace=namespace)
    else:
        socketio.emit(event, payload, namespace=namespace)

def publish(event, payload, *, outlet="DEMO", floor="1", table_number=None, session_id=None):
    """Fan-out to venue/floor + optional table + optional session."""
    broadcast(event, payload, room=f"outlet:{outlet}:floor:{floor}")
    if table_number:
        broadcast(event, payload, room=f"table:{table_number}")
    if session_id:
        broadcast(event, payload, room=f"session:{session_id}")

def _push_state(session_id: str):
    try:
        from .events import build_table_state_payload, push_table_state_changed

        payload = build_table_state_payload(session_id=session_id) or {}
        payload["session_id"] = session_id

        eff_floor = str(payload.get("floor") or "1")
        eff_table = payload.get("table_number")

        publish(
            "session.state.changed",
            payload,
            outlet="DEMO",
            floor=eff_floor,
            table_number=eff_table,
            session_id=session_id,
        )
        push_table_state_changed(session_id=session_id)
    except Exception:
        pass

# ---------------------------
# Reservation push helpers
# ---------------------------
def _push_reservation_changed_safe(table_number, ts_iso=None):
    """Preferred helper from routes/services. Adds a tiny delay to avoid race with DB commit."""
    push_reservation_changed_deferred(table_number, ts_iso, delay=0.12)

def push_reservation_changed(table_number: str, ts_iso: str | None):
    """
    Always include ts_iso in payload:
      - create/update: ts_iso = "YYYY-MM-DDTHH:MM:SS" (naive local)
      - cancel/consumed: ts_iso = None
    """
    payload = {"table_number": str(table_number), "ts_iso": ts_iso}
    broadcast("reservations.changed", payload)
    broadcast("reservations.changed", payload, room=f"table:{table_number}")

def push_reservation_autoseated(table_number: str, session_id: str):
    """Manual emit, if you ever seat programmatically outside the auto loop."""
    payload = {"table_number": str(table_number), "session_id": str(session_id)}
    broadcast("reservations.autoseated", payload)
    broadcast("reservations.autoseated", payload, room=f"table:{table_number}")

def push_reservation_changed_deferred(table_number: str, ts_iso: str | None = None, delay: float = 0.12):
    """Emit after a short delay so DB commit lands and the 'occupied' class is present."""
    def _job():
        try:
            socketio.sleep(delay)
            push_reservation_changed(table_number, ts_iso)
        except Exception:
            if current_app:
                current_app.logger.exception("push_reservation_changed_deferred failed")
    socketio.start_background_task(_job)
