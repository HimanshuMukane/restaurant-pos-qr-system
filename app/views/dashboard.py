from flask import Blueprint, render_template
from flask_login import login_required
from ..authz import roles_required
from utils import db
from datetime import datetime, timedelta
import re
from ..helpers import now_wib
from utils.config_store import get_billing_config

bp = Blueprint("dashboard", __name__)

def _floor_sort_key(value):
    s = str(value)
    m = re.match(r"^(\d+)(.*)$", s)
    if m:
        return (0, int(m.group(1)), m.group(2))
    return (1, s)

def _augment_reservation_rows(rows, due_soon_minutes=120):
    out = []
    now = now_wib()
    try:
        from zoneinfo import ZoneInfo
        TZ = ZoneInfo("Asia/Jakarta")
    except Exception:
        TZ = None
    for r in rows:
        d = dict(r)
        try:
            s = f"{d.get('date','')}T{d.get('time','')}:00"
            start_dt = datetime.fromisoformat(s)
            if TZ and start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=TZ)
        except Exception:
            start_dt = None
        if start_dt:
            delta = start_dt - now
            mins = int(delta.total_seconds() // 60)
            d['starts_in_minutes'] = max(0, mins)
            d['due_soon'] = (0 <= delta.total_seconds() <= due_soon_minutes * 60)
        else:
            d['starts_in_minutes'] = 0
            d['due_soon'] = False
        out.append(d)
    return out


@bp.get("/")
@login_required
@roles_required('admin', 'cashier', 'waiter', 'viewer')
def dashboard():
    tables = db.load_tables()
    session_map = db.get_active_sessions(None)
    active_guest_map = db.get_active_sessions_guests(None)
    floors = sorted({t["floor"] for t in tables}, key=_floor_sort_key)
    raw_res = db.get_upcoming_reservations(None)
    reservations = _augment_reservation_rows(raw_res)
    floor_layouts = db.get_floor_layouts()

    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        # Tables with billing already started
        c.execute("""
            SELECT table_number
            FROM sessions
            WHERE status = 'active'
              AND billing_started_at IS NOT NULL
        """)
        billing_rows = c.fetchall()

        # Active sessions that have **no (non-cancelled) items** yet
        # NOTE: replace "order_items" and the status filter with whatever
        # your real items table / non-void condition is.
        c.execute("""
            SELECT s.table_number
            FROM sessions s
            LEFT JOIN order_items oi
                   ON oi.session_id = s.id
                  AND oi.status <> 'cancelled'
            WHERE s.status = 'active'
            GROUP BY s.table_number
            HAVING COUNT(oi.id) = 0
        """)
        empty_rows = c.fetchall()

        # Totals per active (non-takeaway) table, incl. svc/tax (matches bill popup math)
        c.execute("""
            SELECT
              s.table_number,
              COALESCE(SUM((GREATEST(oi.qty - COALESCE(oi.void_qty,0),0) * oi.price)::INT), 0) AS subtotal,
              COALESCE(s.service_type, 'dine_in') AS service_type
            FROM sessions s
            LEFT JOIN order_items oi
                   ON oi.session_id = s.id
                  AND oi.status <> 'cancelled'
            WHERE s.status = 'active'
              AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
            GROUP BY s.table_number, s.service_type
        """)
        total_rows = c.fetchall()
    finally:
        conn.close()

    billing_map = {str(r[0]).strip(): True for r in billing_rows}
    empty_session_map = {str(r[0]).strip(): True for r in empty_rows}
    bill_totals_map = {}

    def _round(v):
        # match JS Math.round for positive numbers
        return int(v + 0.5)

    billing_cfg = get_billing_config()
    service_pct_default = int(billing_cfg.get("service_percent", 5))
    tax_pct_default = int(billing_cfg.get("tax_percent", 10))
    tax_on_service = bool(billing_cfg.get("tax_on_service"))

    for tn, subtotal_raw, svc_type in total_rows:
        base = int(subtotal_raw or 0)
        is_ta = (str(svc_type or '').lower() == 'takeaway')
        service = 0 if is_ta else _round(base * (service_pct_default / 100.0))
        tax_base = base + service if tax_on_service else base
        tax     = _round(tax_base * (tax_pct_default / 100.0))
        total   = base + service + tax
        bill_totals_map[str(tn).strip()] = total


    reserved_state = {}
    for r in reservations:  # reservations already have starts_in_minutes due to _augment_reservation_rows
        tn = (r.get("table_number") or "").strip()
        if not tn:
            continue
        if r.get("status") not in ("confirmed", "pending"):
            continue
        mins = int(r.get("starts_in_minutes") or 999999)
        prev = reserved_state.get(tn)
        if prev is None or mins < prev["minutes"]:
            reserved_state[tn] = {
            "guest_name": r.get("guest_name") or "",
            "minutes": mins,
            "lockout": mins <= 120,   # 2-hour lockout for opening new session
            "due_hour": mins <= 120,  # make OCCUPIED tiles pulse within 120 min
        }


    return render_template(
        "dashboard.html",
        tables=tables,
        session_map=session_map,
        active_guest_map=active_guest_map,
        floor_layouts=floor_layouts,
        floors=floors,
        reservations=reservations,
        billing_map=billing_map,
        reserved_state=reserved_state,
        empty_session_map=empty_session_map,
        bill_totals_map=bill_totals_map,
    )
