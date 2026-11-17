# events.py
import uuid
import time
import os
from datetime import datetime, timezone
from .socketbus import broadcast, publish

_FLOOR_CACHE = {"ts": 0.0, "map": {}}
_FLOOR_TTL_SEC = 15


def _build_table_floor_map():
    mapping = {}
    try:
        from utils import db
        layouts = db.get_floor_layouts() or {}
        for floor, info in layouts.items():
            boxes = (info or {}).get("boxes") or {}
            for key in boxes.keys():
                if key is None:
                    continue
                mapping[str(key)] = str(floor)
    except Exception:
        mapping = {}

    if mapping:
        return mapping

    try:
        from utils import db
        tables = db.load_tables() or []
        for t in tables:
            if not isinstance(t, dict):
                continue
            num = t.get("number")
            fl = t.get("floor")
            if num is None or fl is None:
                continue
            mapping[str(num)] = str(fl)
    except Exception:
        pass

    return mapping


def _resolve_floor(table_number, floor_hint=None):
    if table_number is None:
        return floor_hint
    key = str(table_number).strip()
    if not key:
        return floor_hint
    now = time.time()
    if (now - _FLOOR_CACHE["ts"]) > _FLOOR_TTL_SEC or not _FLOOR_CACHE["map"]:
        _FLOOR_CACHE["map"] = _build_table_floor_map()
        _FLOOR_CACHE["ts"] = now
    return _FLOOR_CACHE["map"].get(key) or floor_hint


def _table_number_for_session(session_id):
    if not session_id:
        return None
    try:
        from utils import db
        row = db.get_session_by_id(None, session_id)
        if row:
            return row[1]
    except Exception:
        return None
    return None


def _qr_creator_clauses(alias="oi"):
    clauses, params = [], []

    qr_uid_env = os.getenv("QR_USER_ID", "").strip()
    try:
        qr_uid = int(qr_uid_env) if qr_uid_env else None
    except ValueError:
        qr_uid = None
    if qr_uid:
        clauses.append(f"{alias}.created_by_user_id = %s")
        params.append(qr_uid)

    qr_uname = (os.getenv("QR_USERNAME") or "qr_service").strip()
    if qr_uname:
        clauses.append(
            f"EXISTS (SELECT 1 FROM public.users u WHERE u.id = {alias}.created_by_user_id AND LOWER(u.username) = LOWER(%s))"
        )
        params.append(qr_uname)

    if not clauses:
        return "", []
    return " AND (" + " OR ".join(clauses) + ")", params


def _round_half_up_int(value):
    return int(float(value or 0) + 0.5)


def _compute_table_total(subtotal, service_type):
    try:
        from utils.config_store import get_billing_config

        cfg = get_billing_config()
        service_pct = int(cfg.get("service_percent", 5))
        tax_pct = int(cfg.get("tax_percent", 10))
        tax_on_service = bool(cfg.get("tax_on_service"))
    except Exception:
        service_pct = 5
        tax_pct = 10
        tax_on_service = True

    base = int(subtotal or 0)
    is_takeaway = str(service_type or "").lower() == "takeaway"
    service = 0 if is_takeaway else _round_half_up_int(base * (service_pct / 100.0))
    tax_base = base + service if tax_on_service else base
    tax = _round_half_up_int(tax_base * (tax_pct / 100.0))
    return base + service + tax


def build_table_state_payload(table_number=None, session_id=None, floor_hint=None):
    eff_table = str(table_number or "").strip() if table_number is not None else ""
    if not eff_table and session_id:
        resolved = _table_number_for_session(session_id)
        eff_table = str(resolved or "").strip()
    if not eff_table:
        return None

    floor = _resolve_floor(eff_table, floor_hint) or floor_hint or "1"

    try:
        from utils import db

        conn = db.connect_db(None)
    except Exception:
        return {
            "table_number": eff_table,
            "floor": str(floor),
            "session_id": None,
            "occupied": False,
            "billing": False,
            "empty_session": False,
            "guest_name": None,
            "total_amount": None,
            "has_unsent": False,
            "has_qr_unsent": False,
        }

    qr_clause, qr_params = _qr_creator_clauses("oi")

    try:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT
                    s.id,
                    COALESCE(s.guest_name, ''),
                    COALESCE(s.service_type, 'dine_in'),
                    CASE WHEN s.billing_started_at IS NOT NULL THEN TRUE ELSE FALSE END AS billing,
                    COALESCE((
                        SELECT SUM((GREATEST(oi.qty - COALESCE(oi.void_qty, 0), 0) * oi.price)::int)
                          FROM public.order_items oi
                         WHERE oi.session_id = s.id
                           AND COALESCE(oi.status, '') <> 'cancelled'
                    ), 0)::int AS subtotal,
                    COALESCE((
                        SELECT COUNT(*)
                          FROM public.order_items oi
                         WHERE oi.session_id = s.id
                           AND COALESCE(oi.status, '') <> 'cancelled'
                    ), 0)::int AS item_count
                FROM public.sessions s
                WHERE s.table_number = %s
                  AND COALESCE(s.status, '') = 'active'
                  AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
                ORDER BY s.created_at DESC
                LIMIT 1
                """,
                (eff_table,),
            )
            row = c.fetchone()

            active_session_id = None
            guest_name = None
            service_type = "dine_in"
            billing = False
            subtotal = 0
            item_count = 0

            if row:
                active_session_id = str(row[0])
                guest_name = (row[1] or "").strip() or None
                service_type = row[2] or "dine_in"
                billing = bool(row[3])
                subtotal = int(row[4] or 0)
                item_count = int(row[5] or 0)

            total_amount = _compute_table_total(subtotal, service_type) if active_session_id else None
            empty_session = bool(active_session_id) and item_count == 0

            try:
                c.execute(
                    f"""
                    SELECT
                      (
                        EXISTS (
                          SELECT 1
                            FROM public.sessions s
                            JOIN public.order_items oi ON oi.session_id = s.id
                           WHERE s.table_number = %s
                             AND COALESCE(s.status,'') = 'active'
                             AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
                             AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                             AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                        )
                        OR
                        EXISTS (
                          SELECT 1
                            FROM qr.qr_orders qo
                           WHERE qo.table_number = %s
                             AND COALESCE(qo.status,'new') IN ('new','pending')
                             AND qo.sent_at IS NULL
                        )
                      ) AS has_unsent,
                      (
                        EXISTS (
                          SELECT 1
                            FROM public.sessions s
                            JOIN public.order_items oi ON oi.session_id = s.id
                           WHERE s.table_number = %s
                             AND COALESCE(s.status,'') = 'active'
                             AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
                             AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                             AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                             {qr_clause}
                        )
                        OR
                        EXISTS (
                          SELECT 1
                            FROM qr.qr_orders qo
                           WHERE qo.table_number = %s
                             AND COALESCE(qo.status,'new') IN ('new','pending')
                             AND qo.sent_at IS NULL
                        )
                      ) AS has_qr_unsent
                    """,
                    [eff_table, eff_table, eff_table, *qr_params, eff_table],
                )
                flags = c.fetchone() or (False, False)
                has_unsent = bool(flags[0])
                has_qr_unsent = bool(flags[1])
            except Exception:
                c.execute(
                    f"""
                    SELECT
                      EXISTS (
                        SELECT 1
                          FROM public.sessions s
                          JOIN public.order_items oi ON oi.session_id = s.id
                         WHERE s.table_number = %s
                           AND COALESCE(s.status,'') = 'active'
                           AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
                           AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                           AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                      ) AS has_unsent,
                      EXISTS (
                        SELECT 1
                          FROM public.sessions s
                          JOIN public.order_items oi ON oi.session_id = s.id
                         WHERE s.table_number = %s
                           AND COALESCE(s.status,'') = 'active'
                           AND COALESCE(s.service_type, 'dine_in') <> 'takeaway'
                           AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                           AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                           {qr_clause}
                      ) AS has_qr_unsent
                    """,
                    [eff_table, eff_table, *qr_params],
                )
                flags = c.fetchone() or (False, False)
                has_unsent = bool(flags[0])
                has_qr_unsent = bool(flags[1])

        return {
            "table_number": eff_table,
            "floor": str(floor),
            "session_id": active_session_id,
            "occupied": bool(active_session_id),
            "billing": billing,
            "empty_session": empty_session,
            "guest_name": guest_name,
            "total_amount": total_amount,
            "has_unsent": has_unsent,
            "has_qr_unsent": has_qr_unsent,
        }
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

def _env():
    return {"ts": datetime.now(timezone.utc).isoformat(), "event_id": str(uuid.uuid4())}


def push_table_state_changed(table_number=None, session_id=None, outlet="DEMO", floor="1"):
    payload = build_table_state_payload(table_number=table_number, session_id=session_id, floor_hint=floor)
    if not payload:
        return
    payload = {**payload, **_env()}
    eff_floor = payload.get("floor") or floor or "1"
    eff_table = payload.get("table_number")
    eff_session = payload.get("session_id") or session_id

    broadcast("table.state.changed", payload, room=f"outlet:{outlet}")
    broadcast("table.state.changed", payload, room=f"outlet:{outlet}:floor:{eff_floor}")
    if eff_table:
        broadcast("table.state.changed", payload, room=f"table:{eff_table}")
    if eff_session:
        broadcast("table.state.changed", payload, room=f"session:{eff_session}")

def session_created(table_number, session_id, pax=None, guest_name=None, ts_iso=None, outlet="DEMO", floor="1"):
    payload = {
        "table_number": str(table_number),
        "session_id": session_id,
        "pax": pax,
        "guest_name": guest_name,
        **_env()
    }
    if ts_iso:
        payload["ts_iso"] = ts_iso  # ← pass upcoming reservation time to clients
    eff_floor = _resolve_floor(table_number, floor) or "1"
    publish("session_created", payload, outlet=outlet, floor=eff_floor, table_number=table_number, session_id=session_id)
    push_table_state_changed(table_number=table_number, session_id=session_id, outlet=outlet, floor=eff_floor)

def session_closed(table_number, session_id, outlet="DEMO", floor="1"):
    payload = {"table_number": str(table_number), "session_id": session_id, **_env()}
    eff_floor = _resolve_floor(table_number, floor) or "1"
    publish("session_closed", payload, outlet=outlet, floor=eff_floor, table_number=table_number, session_id=session_id)
    push_table_state_changed(table_number=table_number, session_id=session_id, outlet=outlet, floor=eff_floor)

def table_moved(from_table, to_table, session_id, outlet="DEMO", floor="1"):
    payload = {"from_table": str(from_table), "to_table": str(to_table), "session_id": session_id, **_env()}
    floors = []
    from_floor = _resolve_floor(from_table, floor)
    to_floor = _resolve_floor(to_table, floor)
    if from_floor:
        floors.append(from_floor)
    if to_floor and to_floor not in floors:
        floors.append(to_floor)
    if floors:
        for fl in floors:
            broadcast("table_moved", payload, room=f"outlet:{outlet}:floor:{fl}")
    else:
        broadcast("table_moved", payload, room=f"outlet:{outlet}")
    broadcast("table_moved", payload, room=f"table:{from_table}")
    broadcast("table_moved", payload, room=f"table:{to_table}")
    broadcast("session_moved", payload, room=f"session:{session_id}")
    push_table_state_changed(table_number=from_table, outlet=outlet, floor=from_floor or floor)
    push_table_state_changed(table_number=to_table, session_id=session_id, outlet=outlet, floor=to_floor or floor)

def session_items_changed(table_number, session_id, outlet="DEMO", floor="1"):
    eff_table = table_number
    if eff_table is None:
        eff_table = _table_number_for_session(session_id)
    payload = {"table_number": str(eff_table) if eff_table is not None else "", "session_id": session_id, **_env()}
    eff_floor = _resolve_floor(eff_table, floor) or "1"
    publish(
        "session_items_changed",
        payload,
        outlet=outlet,
        floor=eff_floor,
        table_number=eff_table,
        session_id=session_id,
    )
    push_table_state_changed(table_number=eff_table, session_id=session_id, outlet=outlet, floor=eff_floor)

def session_billing(table_number, session_id):
    payload = {"table_number": str(table_number), "session_id": session_id, **_env()}
    broadcast("session_billing", payload)
    push_table_state_changed(table_number=table_number, session_id=session_id)
