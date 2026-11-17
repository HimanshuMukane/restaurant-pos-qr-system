from datetime import datetime
from psycopg.rows import dict_row
from ..data.core import connect_db
from ..data import reservations as data_res
from app.socketbus import _push_state

# --- WINDOWS (minutes)
LOCKOUT_MIN   = 120   # cannot open normal session within 2 hours
PULSE_MIN     = 60    # start pulsating when <= 60 min AND table already active
AUTO_SEAT_MIN = 30    # auto-seat window (background, not on click)


def _make_ts_iso(res_date, res_time):
    """
    Return naive ISO like 'YYYY-MM-DDTHH:MM:00' (no timezone) so the browser
    won't shift it on parse. Works with time objects or 'HH:MM[:SS]' strings.
    """
    if not res_date or not res_time:
        return None
    try:
        # date: datetime.date
        d = res_date.isoformat() if hasattr(res_date, "isoformat") else str(res_date)

        # time: datetime.time OR 'HH:MM[:SS]'
        if hasattr(res_time, "hour"):
            hh = f"{res_time.hour:02d}"
            mm = f"{res_time.minute:02d}"
        else:
            s = str(res_time)
            hh, mm = s.split(":", 2)[:2]
            hh = hh.zfill(2)
            mm = mm.zfill(2)

        return f"{d}T{hh}:{mm}:00"
    except Exception:
        return None

def transfer_preorders_to_session(_ignored, reservation_id: int, session_id: str, by_user_id: int):
    """
    Copy all preordered items for reservation_id into the live session's order_items.
    Prefired lines are inserted with status='printed' so they don't print again.
    """
    with connect_db() as conn, conn.cursor() as c:
        # Insert as real order_items
        c.execute("""
            INSERT INTO public.order_items
              (session_id, table_number, item_name, qty, price, total_price,
               sauce, note, status, "timestamp", created_by_user_id, bill_group, void_qty)
            SELECT
              %(sid)s,
              COALESCE(r.table_number::text, s.table_number),
              ri.item_name,
              ri.qty::numeric,
              ri.price,
              (ri.qty::numeric * ri.price)::int,
              ri.sauce,
              ri.note,
              CASE WHEN ri.prefired_at IS NULL THEN 'new' ELSE 'printed' END,
              NOW(),
              %(uid)s,
              COALESCE(NULLIF(ri.bill_group,''), 'main'),
              0::numeric
            FROM public.reservation_items ri
            JOIN public.reservations r ON r.id = ri.reservation_id
            JOIN public.sessions s     ON s.id = %(sid)s
            WHERE ri.reservation_id = %(rid)s;
        """, {"sid": session_id, "rid": reservation_id, "uid": by_user_id})

        # (Optional) mark migrated for traceability
        c.execute("""
            UPDATE public.reservation_items
               SET migrated_to_session_id = %s,
                   migrated_at = NOW()
             WHERE reservation_id = %s
        """, (session_id, reservation_id))

        conn.commit()

def reservation_table_number(res_id: int) -> str:
    return f"RES:{int(res_id)}"

def ensure_reservation_session(_ignored, res_id: int, opened_by_user_id: int) -> str:
    """
    If the reservation already has a session_id, return it.
    Otherwise create a virtual session on table 'RES:<res_id>' and save it.
    """
    with connect_db() as conn, conn.cursor() as c:
        # Read current state
        c.execute("""
            SELECT session_id, guest_name, COALESCE(pax,1), COALESCE(dp_amount,0),
                   COALESCE(notes,''), COALESCE(table_number,'')
              FROM public.reservations
             WHERE id=%s
        """, (res_id,))
        row = c.fetchone()
        if not row:
            raise RuntimeError("Reservation not found")
        cur_sid, guest_name, pax, dp_amount, note, table_hint = row

        if cur_sid:  # already created
            return cur_sid

        pseudo_table = reservation_table_number(res_id)

        # Create a normal 'active' session on the virtual table
        from utils import db as _db
        sid = _db.create_session(
            None, pseudo_table, int(pax or 1), guest_name or None,
            int(dp_amount or 0), note or None, opened_by_user_id=opened_by_user_id
        )

        # Tie it back to reservation
        c.execute("UPDATE public.reservations SET session_id=%s WHERE id=%s", (sid, res_id))
        conn.commit()
        return sid

def seat_reservation_existing_session(_ignored, reservation_id: int, table_number: str, session_id: str, by_user_id: int):
    """
    Seat a reservation that already has a session_id by moving that session to the real table
    and marking the reservation as seated.
    """
    # Move the session to the target table (also updates order_items.table_number)
    from utils import db as _db
    _db.move_session_table(None, session_id, table_number, by_user_id=by_user_id)

    # Import any reservation_items into the live session (if you still use them)
    try:
        transfer_preorders_to_session(None, reservation_id, session_id, by_user_id)
    except Exception:
        # keep auto-seat flowing even if import fails
        pass

    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            UPDATE public.reservations
               SET status='seated', session_id=%s, seated_by_user_id=%s, table_number=%s
             WHERE id=%s
        """, (session_id, by_user_id, table_number, reservation_id))
        conn.commit()

    return session_id

# returns a list of {"reservation_id", "table_number", "session_id", "date", "time", "ts_iso"}
def auto_seat_due_reservations_verbose(_ignored=None, window_min=AUTO_SEAT_MIN, opened_by_user_id=None):
    from ..data import reservations as data_res
    from flask import current_app  # for logging; safe if app context exists

    rows = data_res.list_due_reservations(None, window_min=window_min)
    seated = []
    for r in rows:
        try:
            existing_sid = r.get("session_id")
            if existing_sid:
                try:
                    sid = seat_reservation_existing_session(
                        None, r["id"], r["table_number"], existing_sid, by_user_id=opened_by_user_id or 0
                    )
                except Exception:
                    sid = seat_reservation(
                        None, r["id"], r["table_number"],
                        pax=r.get("pax") or 1,
                        guest_name=r.get("guest_name"),
                        note=r.get("notes"),
                        by_user_id=opened_by_user_id or 0,
                    )
            else:
                sid = seat_reservation(
                    None, r["id"], r["table_number"],
                    pax=r.get("pax") or 1,
                    guest_name=r.get("guest_name"),
                    note=r.get("notes"),
                    by_user_id=opened_by_user_id or 0,
                )
            ts_iso = _make_ts_iso(r.get("date"), r.get("time"))
            seated.append({
                "reservation_id": r["id"],
                "table_number": str(r["table_number"]),
                "session_id": sid,
                "date": r.get("date"),
                "time": r.get("time"),
                "ts_iso": ts_iso,
            })
        except Exception:
            try:
                current_app.logger.exception(
                    "auto_seat_due_reservations_verbose failed for res_id=%s", r.get("id")
                )
            except Exception:
                pass
    return seated



def seat_reservation_by_id(_ignored, reservation_id, by_user_id):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""SELECT id, table_number, pax, guest_name, notes
                       FROM reservations WHERE id=%s""", (reservation_id,))
        r = c.fetchone()
    if not r:
        raise ValueError("Reservasi tidak ditemukan")
    if not r["table_number"]:
        raise ValueError("Reservasi belum memiliki nomor meja")
    # reuse your existing function
    return seat_reservation(
        None, reservation_id, r["table_number"],
        pax=r["pax"], guest_name=r["guest_name"], note=r["notes"], by_user_id=by_user_id
    )

def auto_seat_due_reservations(_ignored=None, window_min=AUTO_SEAT_MIN, opened_by_user_id=None):
    rows = data_res.list_due_reservations(None, window_min=window_min)
    count = 0
    for r in rows:
        try:
            existing_sid = r.get("session_id")
            if existing_sid:
                try:
                    seat_reservation_existing_session(
                        None, r["id"], r["table_number"], existing_sid, by_user_id=opened_by_user_id or 0
                    )
                except Exception:
                    seat_reservation(
                        None, r["id"], r["table_number"],
                        pax=r["pax"], guest_name=r["guest_name"], note=r.get("notes"),
                        by_user_id=opened_by_user_id or 0
                    )
            else:
                seat_reservation(
                    None, r["id"], r["table_number"],
                    pax=r["pax"], guest_name=r["guest_name"], note=r.get("notes"),
                    by_user_id=opened_by_user_id or 0
                )
            count += 1
        except Exception:
            # ignore races/conflicts
            pass
    return count

def get_lockout_for_table(_ignored, table_number):
    return data_res.get_lockout_reservation_for_table(None, table_number, lockout_min=LOCKOUT_MIN)

def get_next_for_table_today(_ignored, table_number):
    return data_res.get_next_reservation_for_table(None, table_number, only_today=True)

def today_state_map(_ignored=None):
    return data_res.get_today_reservation_times_by_table(None)

def seat_reservation(_ignored, reservation_id, table_number, *, pax, guest_name, note, by_user_id):
    now = datetime.now().isoformat()
    import uuid
    session_id = str(uuid.uuid4())

    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""SELECT id FROM sessions WHERE table_number=%s AND status='active' LIMIT 1""", (table_number,))
        if c.fetchone():
            raise ValueError("Meja sedang terpakai")

        c.execute("""
            INSERT INTO sessions(id,pax,table_number,created_at,guest_name,dp_amount,note,status,opened_by_user_id)
            VALUES(%s,%s,%s,%s,%s,0,%s,'active',%s)
        """, (session_id, pax, table_number, now, guest_name, note, by_user_id))

        c.execute("SELECT * FROM reservations WHERE id=%s", (reservation_id,))
        r = c.fetchone()
        if not r:
            raise ValueError("Reservasi tidak ditemukan")

        dp = r.get("dp_amount") or 0
        if dp > 0:
            c.execute("UPDATE sessions SET dp_amount = %s WHERE id = %s", (dp, session_id))

        c.execute("SELECT * FROM reservation_items WHERE reservation_id=%s", (reservation_id,))
        items = c.fetchall()
        for it in items:
            c.execute("""
                INSERT INTO order_items(session_id,table_number,item_name,qty,price,total_price,sauce,note,status,"timestamp",created_by_user_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'new',%s,%s)
            """, (
                session_id, table_number, it["item_name"], it["qty"], it["price"],
                (it["qty"] * it["price"]), it["sauce"], it["note"], now, by_user_id
            ))

        c.execute("""
            UPDATE reservations
               SET status='seated', session_id=%s, seated_by_user_id=%s, table_number=%s
             WHERE id=%s
        """, (session_id, by_user_id, table_number, reservation_id))

    return session_id


def transfer_preorders_to_session(_ignored, reservation_id: int, session_id: str, by_user_id: int):
    """
    Copy reservation_items -> order_items for this reservation into this session.
    No printing here; your normal kitchen-print flow triggers on 'printed'/'queued' status later.
    """
    with connect_db() as conn, conn.cursor() as c:
        # Insert one row per preorder item
        c.execute("""
            INSERT INTO public.order_items
              (session_id, table_number, item_name, qty, price, total_price,
               sauce, note, status, "timestamp", created_by_user_id, bill_group, void_qty)
            SELECT
              %(sid)s,
              COALESCE(r.table_number, s.table_number),
              i.item_name,
              i.qty::numeric,
              i.price::int,
              (i.qty::numeric * i.price::int)::int,
              NULLIF(i.sauce,''),
              NULLIF(i.note,''),
              'queued',                 
              NOW(),
              %(uid)s,
              'main',
              0::numeric
            FROM public.reservation_items i
            JOIN public.reservations r ON r.id = i.reservation_id
            JOIN public.sessions     s ON s.id = %(sid)s
           WHERE i.reservation_id = %(rid)s
        """, {"sid": session_id, "rid": reservation_id, "uid": by_user_id})
        conn.commit()
