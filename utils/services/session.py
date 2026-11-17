from datetime import datetime, timedelta
from ..data.core import connect_db
import uuid


LEASE_SECONDS = 90  

def try_acquire_session_lock(conn_none, session_id, user_id, lease_sec=LEASE_SECONDS):
    conn = connect_db(conn_none)
    now = datetime.utcnow()
    new_until = now + timedelta(seconds=lease_sec)
    nonce = str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute("""
        UPDATE sessions
           SET lock_user_id=%s, lock_until=%s, lock_nonce=%s, lock_acquired_at=NOW()
         WHERE id=%s
           AND (lock_user_id IS NULL OR lock_user_id=%s OR lock_until < %s)
    """, (user_id, new_until, nonce, session_id, user_id, now))
    ok = cur.rowcount > 0

    owner_username, out_nonce = None, None
    if ok:
        out_nonce = nonce
    else:
        cur.execute("""
            SELECT u.username
              FROM sessions s LEFT JOIN users u ON u.id = s.lock_user_id
             WHERE s.id=%s
        """, (session_id,))
        row = cur.fetchone()
        owner_username = row[0] if row else None

    conn.commit()
    conn.close()
    return ok, (out_nonce or owner_username)

def heartbeat_session_lock(conn_none, session_id, user_id, nonce, lease_sec=LEASE_SECONDS):
    conn = connect_db(conn_none)
    new_until = datetime.utcnow() + timedelta(seconds=lease_sec)
    cur = conn.cursor()
    cur.execute("""
        UPDATE sessions
           SET lock_until=%s
         WHERE id=%s AND lock_user_id=%s AND lock_nonce=%s
    """, (new_until, session_id, user_id, nonce))
    ok = cur.rowcount > 0
    conn.commit(); conn.close()
    return ok

def release_session_lock(conn_none, session_id, user_id, nonce):
    conn = connect_db(conn_none)
    cur = conn.cursor()
    cur.execute("""
        UPDATE sessions
           SET lock_user_id=NULL, lock_until=NULL, lock_nonce=NULL
         WHERE id=%s AND lock_user_id=%s AND lock_nonce=%s
    """, (session_id, user_id, nonce))
    ok = cur.rowcount > 0
    conn.commit(); conn.close()
    return ok

def get_session_lock_owner(conn_none, session_id):
    conn = connect_db(conn_none)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.lock_user_id, u.username, s.lock_until, s.lock_nonce
          FROM sessions s LEFT JOIN users u ON u.id = s.lock_user_id
         WHERE s.id=%s
    """, (session_id,))
    row = cur.fetchone()
    conn.close()
    return row if row else (None, None, None, None)


def user_holds_session_lock(conn_none, session_id, user_id):
    conn = connect_db(conn_none)
    cur = conn.cursor()
    cur.execute("""
        SELECT 1
          FROM sessions
         WHERE id=%s AND lock_user_id=%s AND (lock_until IS NULL OR lock_until > %s)
    """, (session_id, user_id, datetime.utcnow()))
    ok = cur.fetchone() is not None
    conn.close()
    return ok
