from datetime import datetime
from psycopg.rows import dict_row
from .core import connect_db

def create_reservation_with_table(_ignored, *, table_number, guest_name, phone, pax, date, time,
                                  notes=None, dp_amount=0, dp_method=None, created_by_user_id=None,
                                  status="pending"):
    now = datetime.now().isoformat()
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            INSERT INTO reservations(
                guest_name, phone, pax, date, time, notes, status,
                table_number, session_id, created_at, created_by_user_id,
                dp_amount, dp_method, dp_paid_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,
                    %s, NULL, %s, %s,
                    %s, %s, %s)
            RETURNING id
        """, (
            guest_name, phone, pax, date, time, notes, status,
            table_number, now, created_by_user_id,
            dp_amount, dp_method, (now if (dp_amount or 0) > 0 else None)
        ))
        rid = c.fetchone()["id"]
    return rid

def list_future_reservations_for_table(_ignored, table_number):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
          SELECT id, guest_name, phone, pax, date, time, notes, status,
                 table_number, session_id,
                 to_timestamp(date || ' ' || "time", 'YYYY-MM-DD HH24:MI') AS ts_local
            FROM public.reservations
           WHERE table_number=%s
             AND status IN ('pending','confirmed')
             AND to_timestamp(date || ' ' || "time", 'YYYY-MM-DD HH24:MI') >= (now() AT TIME ZONE 'Asia/Jakarta')
           ORDER BY date, "time"
        """, (table_number,))
        return c.fetchall()


# utils/data/reservations.py
from psycopg.rows import dict_row
from .core import connect_db

def get_next_reservation_for_table(_ignored, table_number, only_today=True):
    """
    Returns the next pending/confirmed reservation for a table.
    Fields: id, table_number, pax, guest_name, date (date), time (time), notes
    """
    sql = [
        "SELECT id, table_number, pax, guest_name, date, time, notes",
        "  FROM public.reservations",
        " WHERE table_number = %s",
        "   AND status IN ('pending','confirmed')",
    ]
    params = [table_number]
    if only_today:
        sql.append("  AND date = CURRENT_DATE")
    sql.append(" ORDER BY date ASC, time ASC LIMIT 1")
    q = "\n".join(sql)

    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute(q, params)
        row = c.fetchone()
    return row  # dict or None

def get_lockout_reservation_for_table(_ignored, table_number, lockout_min=120):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT r.*,
                   to_timestamp(r.date || ' ' || r."time", 'YYYY-MM-DD HH24:MI') AS ts_local
              FROM reservations r
             WHERE r.table_number=%s
               AND r.status IN ('pending','confirmed')
               AND to_timestamp(r.date || ' ' || r."time", 'YYYY-MM-DD HH24:MI') BETWEEN now() AND now() + (%s || ' minutes')::interval
             ORDER BY r.date, r."time"
             LIMIT 1
        """, (table_number, lockout_min))
        return c.fetchone()

def update_reservation(_ignored, res_id, **fields):
    if not fields: return
    allowed = {
        "guest_name","phone","pax","date","time","notes",
        "status","table_number","dp_amount","dp_method","session_id"
    }
    sets, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=%s")
            vals.append(v)
    if not sets: return
    with connect_db() as conn, conn.cursor() as c:
        c.execute(f"UPDATE public.reservations SET {', '.join(sets)} WHERE id=%s", (*vals, res_id))
        conn.commit()


def get_today_reservation_times_by_table(_ignored=None):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT table_number,
                   MIN(to_timestamp(date || ' ' || "time", 'YYYY-MM-DD HH24:MI')) AS next_ts
              FROM reservations
             WHERE status IN ('pending','confirmed')
               AND date = CURRENT_DATE
               AND table_number IS NOT NULL
             GROUP BY table_number
        """)
        rows = c.fetchall()
    return {r["table_number"]: r["next_ts"] for r in rows}

def list_due_reservations(_ignored=None, window_min=30):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT r.*,
                   to_timestamp(r.date || ' ' || r."time", 'YYYY-MM-DD HH24:MI') AS ts_local
              FROM reservations r
         LEFT JOIN sessions s
                ON s.table_number = r.table_number AND s.status='active'
             WHERE r.status IN ('pending','confirmed')
               AND r.table_number IS NOT NULL
               AND to_timestamp(r.date || ' ' || r."time", 'YYYY-MM-DD HH24:MI') BETWEEN now() AND now() + (%s || ' minutes')::interval
               AND s.id IS NULL
             ORDER BY r.date, r."time"
        """, (window_min,))
        return c.fetchall()

def table_has_active_session(_ignored, table_number):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""SELECT 1 FROM sessions WHERE table_number=%s AND status='active' LIMIT 1""", (table_number,))
        return c.fetchone() is not None


def insert_reservation(_ignored, *, guest_name, phone, pax, date, time, notes,
                       dp_amount, dp_method, created_by_user_id) -> int:
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO public.reservations(
                guest_name, phone, pax, date, "time", notes, status,
                table_number, session_id, created_at, created_by_user_id,
                dp_amount, dp_method, dp_paid_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                'pending',
                NULL, NULL,
                NOW(), %s,
                %s, %s,
                CASE WHEN %s > 0 THEN NOW() ELSE NULL END
            )
            RETURNING id
        """, (
            guest_name, phone, pax, date, time, notes,
            created_by_user_id,
            dp_amount, dp_method, dp_amount
        ))
        rid = c.fetchone()[0]
        conn.commit()
        return rid

def add_reservation_item(_ignored, reservation_id, *, item_name, qty, price, sauce=None, note=None, user_id=None):
    now = datetime.now().isoformat()
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO reservation_items(reservation_id, item_name, qty, price, sauce, note, created_at, created_by_user_id)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """, (reservation_id, item_name, qty, price, sauce, note, now, user_id))

def list_reservation_items(_ignored, reservation_id):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("SELECT * FROM reservation_items WHERE reservation_id=%s ORDER BY id", (reservation_id,))
        return c.fetchall()

def delete_reservation_item(_ignored, item_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("DELETE FROM reservation_items WHERE id=%s", (item_id,))

def get_upcoming_reservations(_ignored=None):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT id, guest_name, phone, pax, date, time, notes,
                   status, table_number, session_id
            FROM reservations
            WHERE to_timestamp(date || ' ' || time, 'YYYY-MM-DD HH24:MI') >= (now() AT TIME ZONE 'Asia/Jakarta')
            ORDER BY to_timestamp(date || ' ' || time, 'YYYY-MM-DD HH24:MI') ASC
        """)
        return c.fetchall()
