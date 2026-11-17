from datetime import datetime
from psycopg.rows import dict_row
from .core import connect_db
import uuid


def get_all_sessions(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT table_number, id, created_at FROM sessions")
        return c.fetchall()

def create_session(_ignored, table_number, pax=1, guest_name=None, dp_amount=0, note=None, opened_by_user_id=None):
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO sessions (id, pax, table_number, created_at, guest_name, dp_amount, note, status, opened_by_user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
        """, (session_id, pax, table_number, created_at, guest_name, dp_amount, note, opened_by_user_id))
    return session_id

def get_session_by_table(_ignored, table_number):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT id FROM sessions
            WHERE table_number = %s
              AND status = 'active'
              AND COALESCE(service_type, 'dine_in') <> 'takeaway'
            ORDER BY created_at DESC
            LIMIT 1
        """, (table_number,))
        row = c.fetchone()
        return row[0] if row else None

def get_orders_by_session(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT * FROM orders WHERE session_id = %s", (session_id,))
        return c.fetchall()

def delete_session(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("DELETE FROM sessions WHERE id = %s", (session_id,))

def get_session_detail(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT pax, guest_name, dp_amount, note, created_at, status, closed_at
            FROM sessions
            WHERE id = %s
        """, (session_id,))
        return c.fetchone()

def close_session(_ignored, session_id, closed_by_user_id=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            UPDATE sessions
            SET status='closed', closed_at=%s, closed_by_user_id=%s
            WHERE id = %s
        """, (datetime.now().isoformat(), closed_by_user_id, session_id))

def get_active_sessions_guests(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT table_number, COALESCE(guest_name,'')
            FROM sessions
            WHERE status = 'active'
              AND COALESCE(service_type, 'dine_in') <> 'takeaway'
        """)
        rows = c.fetchall()
        return {r[0]: (r[1] or "") for r in rows}

def get_active_sessions(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT table_number, id, created_at
              FROM sessions
             WHERE status = 'active'
               AND COALESCE(service_type, 'dine_in') <> 'takeaway'
        """)
        rows = c.fetchall()
        return {row[0]: row[1] for row in rows}

def get_session_by_id(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT id, table_number, status
            FROM sessions
            WHERE id = %s
            LIMIT 1
        """, (session_id,))
        return c.fetchone()

def get_open_session_for_table(table_number: str):
    with connect_db() as conn, conn.cursor() as c:
        c.execute(
            """
            SELECT id, table_number, status
            FROM sessions
            WHERE table_number = %s
              AND status = 'active'
              AND COALESCE(service_type, 'dine_in') <> 'takeaway'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (table_number,)
        )
        return c.fetchone()

def open_session(table_number: str, guest_name: str | None = None, opened_by_user_id: int | None = None,
                 pax: int = 1, note: str | None = None, dp_amount: int = 0) -> str:
    import uuid
    sid = str(uuid.uuid4())
    with connect_db() as conn, conn.cursor() as c:
        c.execute(
            """
            INSERT INTO sessions (id, pax, table_number, guest_name, dp_amount, note, status,
                                  created_at, opened_by_user_id)
            VALUES (%s, %s, %s, %s, %s, %s, 'active', now(), %s)
            """,
            (sid, pax, table_number, guest_name, dp_amount, note, opened_by_user_id)
        )
    return sid

def sessions_active_status(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT status FROM sessions WHERE id = %s", (session_id,))
        row = c.fetchone()
        return row[0] if row else None


# --- Helpers for linked sessions (dine-in + takeaway) ----------------------

def get_session_service_type(_ignored, session_id: str):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT service_type FROM sessions WHERE id = %s", (session_id,))
        row = c.fetchone()
        return (row[0] if row else None)

def list_active_sessions_for_table(_ignored, table_number: str):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute(
            """
            SELECT id, table_number, status, service_type, guest_name,
                   pickup_time, created_at
              FROM sessions
             WHERE table_number = %s
               AND COALESCE(status,'') = 'active'
               AND closed_at IS NULL
             ORDER BY created_at ASC
            """,
            (table_number,),
        )
        return c.fetchall()

def get_active_takeaway_for_table(_ignored, table_number: str):
    with connect_db() as conn, conn.cursor() as c:
        c.execute(
            """
            SELECT
              s.id,
              COALESCE(s.guest_name, '') AS guest_name,
              s.pickup_time,
              s.note,
              s.created_at,
              COALESCE(sum_net.total, 0)::int AS subtotal
            FROM public.sessions s
            LEFT JOIN LATERAL (
              SELECT SUM((GREATEST(oi.qty - COALESCE(oi.void_qty,0),0) * oi.price)::int) AS total
                FROM public.order_items oi
               WHERE oi.session_id = s.id
                 AND oi.status <> 'cancelled'
            ) AS sum_net ON TRUE
           WHERE s.table_number = %s
             AND COALESCE(s.service_type, 'dine_in') = 'takeaway'
             AND COALESCE(s.status,'') = 'active'
             AND s.closed_at IS NULL
           ORDER BY s.created_at DESC
           LIMIT 1
            """,
            (table_number,),
        )
        row = c.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "guest_name": row[1],
            "pickup_time": row[2],
            "note": row[3],
            "created_at": row[4],
            "subtotal": int(row[5] or 0),
        }

def get_session_header(session_id: str):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT table_number, pax, COALESCE(guest_name,''), created_at
            FROM sessions
            WHERE id = %s
        """, (session_id,))
        row = c.fetchone()
        if not row:
            raise ValueError("Session not found")
        return {
            "table_number": row[0],
            "pax": row[1],
            "guest_name": row[2],
            "opened_at": row[3],
        }
