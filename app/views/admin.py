from datetime import datetime, date
import threading, queue, uuid
from urllib.parse import quote
from flask import Blueprint, render_template, request, jsonify, url_for, abort, current_app
from flask_login import login_required, current_user
import bcrypt
import psycopg
from psycopg.rows import dict_row
from ..authz import roles_required
from ..helpers import load_qr_settings, write_qr_settings, qr_png_b64
from utils import db
from utils.services import printing
from utils.services.escpos_receipt import build_receipt_bytes
from utils.config_store import get_app_config, update_config

bp = Blueprint("admin", __name__, url_prefix="/admin")
VALID_USER_ROLES = ("admin", "cashier", "waiter", "viewer")


@bp.get("/transactions")
@login_required
@roles_required("admin", "cashier")
def transactions_page():
    return render_template("admin/transactions.html")


@bp.get("/api/transactions")
@login_required
@roles_required("admin", "cashier")
def transactions_api():
    q_id = request.args.get("id", type=int)
    show_refunds = (request.args.get("show_refunds", "").lower() in ("1", "true", "yes", "on"))
    show_dp = (request.args.get("show_dp", "").lower() in ("1", "true", "yes", "on"))
    method = (request.args.get("method") or "").strip()
    cashier_id = request.args.get("cashier", type=int) or request.args.get("cashier_id", type=int)
    dfrom = (request.args.get("from") or "").strip()
    dto   = (request.args.get("to")   or "").strip()
    name  = (request.args.get("name") or "").strip()

    # sorting (safe list)
    sort_key = (request.args.get("sort") or "time").lower()
    sort_dir = (request.args.get("dir") or "desc").lower()
    dir_sql  = "ASC" if sort_dir == "asc" else "DESC"
    if sort_key == "id":
        order_by = f"p.id {dir_sql}"
    elif sort_key == "amount":
        order_by = f"p.amount {dir_sql}, p.id {dir_sql}"
    elif sort_key == "hour":
        order_by = f"EXTRACT(HOUR FROM (p.paid_at AT TIME ZONE 'Asia/Jakarta')) {dir_sql}, p.paid_at {dir_sql}, p.id {dir_sql}"
    else:  # time
        order_by = f"p.paid_at {dir_sql}, p.id {dir_sql}"

    where, params = [], []

    # ID filter (overrides others)
    if q_id:
        where.append("p.id = %s"); params.append(q_id)
    else:
        # Date filters in WIB but compared in UTC for index-friendliness
        # p.paid_at >= (from::date 00:00 WIB -> UTC)
        # p.paid_at <  ((to+1)::date 00:00 WIB -> UTC)
        if dfrom:
            where.append("p.paid_at >= (%s::date::timestamp AT TIME ZONE 'Asia/Jakarta')")
            params.append(dfrom)
        if dto:
            where.append("p.paid_at <  ((%s::date + INTERVAL '1 day')::timestamp AT TIME ZONE 'Asia/Jakarta')")
            params.append(dto)

        if method:
            where.append("LOWER(p.method) = LOWER(%s)"); params.append(method)

        if cashier_id:
            where.append("p.created_by_user_id = %s"); params.append(cashier_id)

        if not show_refunds:
            where.append("COALESCE(p.is_refund,false) = false")

        if not show_dp:
            where.append("COALESCE(p.is_dp,false) = false")

        if name:
            like = f"%{name}%"
            where.append("""
              (
                s.guest_name ILIKE %s
                OR s.table_number ILIKE %s
                OR EXISTS (
                  SELECT 1
                  FROM public.order_items oi
                  WHERE oi.session_id = p.session_id
                    AND COALESCE(NULLIF(TRIM(oi.bill_group),''),'main')
                        = COALESCE(NULLIF(TRIM(p.bill_group),''),'main')
                    AND oi.status <> 'cancelled'
                    AND (oi.qty - COALESCE(oi.void_qty, 0)) > 0
                    AND oi.item_name ILIKE %s
                )
              )
            """)
            params.extend([like, like, like])

    sql = f"""
    SELECT
        p.id,
        p.session_id,
        COALESCE(NULLIF(TRIM(p.bill_group), ''), 'main') AS bill_group,
        p.paid_at,
        TO_CHAR(p.paid_at AT TIME ZONE 'Asia/Jakarta', 'YYYY-MM-DD"T"HH24:MI:SS') AS paid_at_wib_text,
        EXTRACT(HOUR FROM (p.paid_at AT TIME ZONE 'Asia/Jakarta'))::int AS paid_hour_wib,
        p.method,
        p.card_type,
        p.amount,
        p.cash_received,
        p.change_given,
        COALESCE(p.is_refund,false) AS is_refund,
        p.refund_of,
        p.discount_amount,
        p.discount_percent,
        p.tax,
        p.service,
        p.total_before_discount,
        -- expose DP applied on this payment
        COALESCE(p.dp_applied_amount,0)::int AS dp_applied,
        COALESCE(p.is_dp,false) AS is_dp,
        s.table_number,
        s.guest_name,
        s.status AS session_status,
        COALESCE(NULLIF(TRIM(u.full_name),''), u.username) AS cashier_name,
        -- ABS sum of refunds/reopens linked to this payment
        COALESCE((
          SELECT SUM(ABS(r.amount))::int
          FROM public.payments r
          WHERE COALESCE(r.is_refund,false) = true
            AND r.refund_of = p.id
        ), 0) AS refunded_amount_abs,
        -- For remaining calculation on the client (ABS base of the original)
        CASE WHEN COALESCE(p.is_refund,false) THEN NULL ELSE ABS(p.amount)::int END AS original_amount_abs
    FROM public.payments p
    LEFT JOIN public.sessions s ON s.id = p.session_id
    LEFT JOIN public.users    u ON u.id = p.created_by_user_id
    {('WHERE ' + ' AND '.join(where)) if where else ''}
    ORDER BY {order_by}
    LIMIT 500
    """

    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    out = []
    for (pid, sid, group, paid_at, paid_at_wib_text, paid_hour_wib,
         method_, card_type, amount, cash_received, change_given,
         is_refund, refund_of, disc_amt, disc_pct, tax, service, tbd,
         dp_applied, is_dp, table_number, guest_name, session_status, cashier_name,
         refunded_amount_abs, original_amount_abs) in rows:

        amount_i        = int(amount or 0)
        refunded_amount = int(refunded_amount_abs or 0)

        if is_refund:
            refundable_left = 0
        else:
            orig_base = int(original_amount_abs or abs(amount_i))
            refundable_left = max(orig_base - refunded_amount, 0)

        is_backfill = (str(method_ or "").lower() == "backfill")

        out.append({
            "id": pid,
            "session_id": sid,
            "bill_group": group,
            "paid_at": paid_at.isoformat() if hasattr(paid_at, "isoformat") else str(paid_at),
            "paid_at_wib": paid_at_wib_text,
            "paid_hour_wib": paid_hour_wib,
            "method": method_,
            "card_type": card_type,
            "amount": amount_i,  # refunds/reopen are negative rows
            "dp_applied": int(dp_applied or 0),  # <-- for your DP column
            "cash_received": (int(cash_received or 0) if cash_received is not None else None),
            "change_given": int(change_given or 0),
            "is_refund": bool(is_refund),
            "is_dp": bool(is_dp),
            "is_backfill": is_backfill,
            "refund_of": refund_of,
            "discount_amount": int(disc_amt or 0),
            "discount_percent": int(disc_pct or 0),
            "tax": int(tax or 0),
            "service": int(service or 0),
            "total_before_discount": int(tbd or 0),
            "table_number": table_number,
            "guest_name": guest_name or None,
            "cashier_name": cashier_name or "-",
            "is_closed": (session_status == 'closed'),  # <-- helps your Aksi logic
            "refunded_amount": refunded_amount,         # ABS sum of linked refunds/reopens
            "original_amount": original_amount_abs or None,  # ABS original
            "refundable_left": refundable_left,
            "reprint_url": url_for("billing.reprint_final_receipt", payment_id=pid, _external=False),
        })

    return jsonify({"rows": out})


@bp.post("/api/transactions/backfill")
@login_required
@roles_required("admin", "cashier")
def backfill_transaction():
    data = request.get_json(silent=True) or {}
    date_str = (data.get("date") or "").strip()
    time_str = (data.get("time") or "").strip()
    try:
        amount = int(str(data.get("amount") or "").strip() or 0)
    except (TypeError, ValueError):
        amount = 0

    if not date_str:
        return jsonify({"status": "error", "message": "Tanggal wajib diisi"}), 400
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"status": "error", "message": "Format tanggal tidak valid"}), 400

    if time_str:
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return jsonify({"status": "error", "message": "Format waktu tidak valid"}), 400
    else:
        time_str = "12:00"

    if amount <= 0:
        return jsonify({"status": "error", "message": "Jumlah tidak valid"}), 400

    paid_at = f"{date_str} {time_str}"

    conn = db.connect_db(None)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO public.payments
                (session_id, amount, method, paid_at,
                 cash_received, change_given,
                 discount_percent, discount_amount, tax, service, total_before_discount,
                 card_type, created_by_user_id, bill_group, dp_applied_amount,
                 is_refund, is_dp)
            VALUES
                (NULL, %s, 'backfill', (%s::timestamp AT TIME ZONE 'Asia/Jakarta'),
                 NULL, 0,
                 0, 0, 0, 0, %s,
                 NULL, %s, 'backfill', 0,
                 false, false)
            RETURNING id
        """, (
            amount,
            paid_at,
            amount,
            getattr(current_user, "id", None),
        ))
        pid = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    return jsonify({"status": "ok", "id": pid})



@bp.post("/api/refund")
@login_required
@roles_required("admin", "cashier")
def create_refund():
    data = request.get_json() or {}
    payment_id = int(data.get("payment_id") or 0)
    amount     = int(data.get("amount") or 0)
    reason     = (data.get("reason") or "").strip() or None

    if payment_id <= 0 or amount <= 0:
        return jsonify({"status": "error", "message": "Data refund tidak valid"}), 400

    # load original payment
    orig = db.get_payment(None, payment_id)
    if not orig or orig.get("is_refund"):
        return jsonify({"status": "error", "message": "Payment tidak ditemukan atau payment adalah refund"}), 400

    # how much already refunded (ABS sum for consistency)
    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT COALESCE(SUM(ABS(amount)),0)::int
            FROM public.payments
            WHERE is_refund = true AND refund_of = %s
        """, (payment_id,))
        refunded_abs = int(cur.fetchone()[0] or 0)
    finally:
        conn.close()

    original_abs = abs(int(orig.get("amount") or 0))
    refundable = max(original_abs - refunded_abs, 0)
    if amount > refundable:
        return jsonify({"status": "error", "message": f"Maksimal bisa refund Rp {refundable:,}"}), 400

    # insert refund row: NEGATIVE amount, method='refund', all components zero
    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO public.payments
                (session_id, amount, method, paid_at, cash_received, change_given,
                 discount_percent, discount_amount, tax, service, total_before_discount,
                 card_type, created_by_user_id, bill_group, dp_applied_amount,
                 is_refund, refund_of, refund_reason, refunded_by_user_id)
            VALUES
                (%s,       %s,      'refund', now(),   NULL,         0,
                 0,               0,               0,   0,       0,
                 NULL,    %s,                %s,       0,
                 true,     %s,        %s,            %s)
            RETURNING id
        """, (
            orig["session_id"],
            -abs(amount),  # NEGATIVE
            getattr(current_user, "id", None),
            (orig.get("bill_group") or "main"),
            payment_id, reason, getattr(current_user, "id", None)
        ))
        rid = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    return jsonify({"status": "ok", "refund_id": rid})


@bp.get("/api/users")
@login_required
@roles_required("admin")
def list_users():
    conn = db.connect_db(None)
    cur = conn.cursor(row_factory=dict_row)
    try:
        cur.execute("""
            SELECT id, username, full_name, role, is_active, created_at
            FROM public.users
            ORDER BY id ASC
        """)
        rows = cur.fetchall()
    finally:
        conn.close()

    out = []
    for row in rows:
        created_at = row["created_at"]
        out.append({
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"] or "",
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": created_at.isoformat() if created_at else None,
        })

    return jsonify({"rows": out})


@bp.patch("/api/users/<int:user_id>")
@login_required
@roles_required("admin")
def update_user(user_id: int):
    data = request.get_json(silent=True) or {}
    updates = {}

    if "username" in data:
        username = (data.get("username") or "").strip().lower()
        if not username or " " in username:
            return jsonify({"status": "error", "message": "username invalid"}), 400
        updates["username"] = username

    if "full_name" in data:
        full_name = (data.get("full_name") or "").strip()
        updates["full_name"] = full_name or None

    if "role" in data:
        role = (data.get("role") or "").strip().lower()
        if role not in VALID_USER_ROLES:
            return jsonify({"status": "error", "message": "role invalid"}), 400
        updates["role"] = role

    if "is_active" in data:
        is_active = data.get("is_active")
        if not isinstance(is_active, bool):
            return jsonify({"status": "error", "message": "is_active must be boolean"}), 400
        updates["is_active"] = is_active

    if "password" in data:
        password = (data.get("password") or "").strip()
        if not password:
            return jsonify({"status": "error", "message": "password kosong"}), 400
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        updates["password_hash"] = pw_hash
        if current_app.config.get("DEMO_MODE"):
            updates["demo_password_plain"] = password

    if not updates:
        return jsonify({"status": "error", "message": "no changes provided"}), 400

    set_parts = []
    params = []
    for key, value in updates.items():
        set_parts.append(f"{key} = %s")
        params.append(value)
    params.append(user_id)

    conn = db.connect_db(None)
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE public.users SET {', '.join(set_parts)} WHERE id = %s RETURNING id",
            params
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return jsonify({"status": "error", "message": "user not found"}), 404
        conn.commit()
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"status": "error", "message": "username sudah dipakai"}), 409
    finally:
        conn.close()

    return jsonify({"status": "ok"})

# -------- BUKA ULANG: reverse original payments with method='reopen' --------

@bp.post("/transactions/reopen_copy/<session_id>")
@login_required
@roles_required("admin", "cashier")
def reopen_copy(session_id):
    """
    Re-open a closed session:
      - Reverse any remaining original payments with method='reopen' (NEGATIVE, zero components, is_refund=true).
      - Reactivate the session.
      - As a safety net, convert any stray refund-style rows created during the same action into proper 'reopen'.
    """
    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "Buka ulang").strip()
    note   = (data.get("refund_note") or "").strip()
    reason_full = f"{reason} – {note}" if note else reason

    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        # 1) Fetch session/table
        cur.execute("SELECT id, table_number FROM public.sessions WHERE id=%s", (session_id,))
        row = cur.fetchone()
        if not row:
            return jsonify(status="error", message="Sesi tidak ditemukan"), 404
        table_number = row[1]

        # 2) Reverse remaining on each ORIGINAL payment
        cur.execute("""
            SELECT p.id, p.amount::int,
                   COALESCE(NULLIF(TRIM(p.bill_group),''),'main') AS bill_group
            FROM public.payments p
            WHERE p.session_id=%s
              AND COALESCE(p.is_refund,false)=false
              AND COALESCE(p.is_dp,false)=false   -- keep DP intact so it can be re-used
        """, (session_id,))
        originals = cur.fetchall()

        reversed_count = 0
        inserted_ids   = []
        for pid, orig_amt, bill_group in originals:
            cur.execute("""
                SELECT COALESCE(SUM(ABS(amount)),0)::int
                FROM public.payments
                WHERE is_refund=true AND refund_of=%s
            """, (pid,))
            already_abs = int(cur.fetchone()[0] or 0)
            remain = max(abs(int(orig_amt or 0)) - already_abs, 0)
            if remain <= 0:
                continue

            # Insert proper REOPEN reversal (NEGATIVE, zero components)
            cur.execute("""
                INSERT INTO public.payments
                    (session_id, amount, method, paid_at,
                    cash_received, change_given,
                    discount_percent, discount_amount, tax, service, total_before_discount,
                    card_type, created_by_user_id, bill_group, dp_applied_amount,
                    is_refund, refund_of)
                VALUES
                    (%s, %s, 'reopen', now(),
                    NULL, 0,
                    0, 0, 0, 0, 0,
                    NULL, %s, %s, 0,
                    true, %s)
                RETURNING id
            """, (
                session_id, -remain,
                getattr(current_user, "id", None),
                bill_group,
                pid,
            ))

            inserted_ids.append(cur.fetchone()[0])
            reversed_count += 1

            # If the original payment consumed DP, put it back by zeroing the applied amount.
            cur.execute("UPDATE public.payments SET dp_applied_amount = 0 WHERE id = %s", (pid,))

        # 3) Reactivate session
        cur.execute("UPDATE public.sessions SET status='active', closed_at=NULL WHERE id=%s", (session_id,))

        # 4) SAFETY NET:
        #    If any refund-style rows slipped in (legacy handler), normalize them to 'reopen' with zero components.
        #    We scope by session_id, recent timestamp, and the reason text to avoid touching unrelated refunds.
                # SAFETY NET (strong): normalize any refund-style reversals for this session to proper 'reopen'
        # Build the set of original payment IDs for this session
        cur.execute("""
            WITH orig AS (
              SELECT id
              FROM public.payments
              WHERE session_id = %s
                AND COALESCE(is_refund,false) = false
                AND COALESCE(is_dp,false)     = false
            )
            UPDATE public.payments AS r
               SET method = 'reopen',
                   discount_percent = 0,
                   discount_amount  = 0,
                   tax = 0,
                   service = 0,
                   total_before_discount = 0,
                   dp_applied_amount = 0,
                   cash_received = NULL,
                   change_given  = 0,
                   card_type     = NULL
             WHERE r.is_refund = true
               AND r.amount    < 0
               AND r.method   <> 'reopen'
               AND r.refund_of IN (SELECT id FROM orig)
        """, (session_id,))

        conn.commit()
    finally:
        conn.close()

    return jsonify(
        status="success",
        version="reopen_hardened",
        reversed=reversed_count,
        inserted_ids=inserted_ids,
        redirect=f"/table/{table_number}/{session_id}?exact=1"
    )

# -------- Tools: nuke (keep some tables) --------

EXCLUDE_TABLES = {"users", "floor_layouts", "alembic_version"}  # keep migrations intact

def _list_public_tables(conn):
    with conn.cursor() as c:
        c.execute("""
            SELECT schemaname, tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
        """)
        rows = c.fetchall()
    tables = []
    for schemaname, tablename in rows:
        if tablename in EXCLUDE_TABLES:
            continue
        if tablename.startswith('pg_') or tablename.startswith('sql_'):
            continue
        tables.append(f'{schemaname}.{tablename}')
    return sorted(tables)

@bp.get("/tools")
@login_required
@roles_required("admin")
def page():
    return render_template("admin_tools.html", active_tab="admin")

@bp.get("/cancelled")
@login_required
@roles_required("admin", "cashier")
def cancelled_page():
    return render_template("cancelled_sessions.html", active_tab="admin")

@bp.get("/api/cancelled_sessions")
@login_required
@roles_required("admin", "cashier")
def cancelled_sessions_api():
    dfrom = (request.args.get("from") or "").strip()
    dto   = (request.args.get("to") or "").strip()

    where = ["s.status = 'cancelled'"]
    params = []

    if dfrom:
        where.append("s.closed_at >= (%s::date::timestamp AT TIME ZONE 'Asia/Jakarta')")
        params.append(dfrom)
    if dto:
        where.append("s.closed_at <  ((%s::date + INTERVAL '1 day')::timestamp AT TIME ZONE 'Asia/Jakarta')")
        params.append(dto)

    # "Cancelled" here = closed session with no payments and with cancelled or void qty
    where.append("""
      NOT EXISTS (
        SELECT 1 FROM public.payments p
        WHERE p.session_id = s.id
          AND COALESCE(p.is_refund,false) = false
      )
    """)

    sql = f"""
    SELECT
      s.id AS session_id,
      s.table_number,
      TO_CHAR(s.created_at AT TIME ZONE 'Asia/Jakarta', 'YYYY-MM-DD HH24:MI') AS created_wib,
      TO_CHAR(s.closed_at AT TIME ZONE 'Asia/Jakarta', 'YYYY-MM-DD HH24:MI') AS closed_wib,
      s.opened_by_user_id,
      s.closed_by_user_id,
      COALESCE(NULLIF(TRIM(uo.full_name),''), uo.username) AS opened_by,
      COALESCE(NULLIF(TRIM(uc.full_name),''), uc.username) AS closed_by,
      COALESCE(SUM(CASE WHEN oi.status = 'cancelled' THEN oi.qty ELSE 0 END), 0) AS qty_cancelled,
      COALESCE(SUM(CASE WHEN oi.status = 'cancelled' THEN oi.qty * oi.price ELSE 0 END), 0) AS value_cancelled,
      COALESCE(SUM(CASE WHEN oi.status <> 'cancelled' THEN oi.void_qty ELSE 0 END), 0) AS qty_void,
      COALESCE(SUM(CASE WHEN oi.status <> 'cancelled' THEN oi.void_qty * oi.price ELSE 0 END), 0) AS value_void
    FROM public.sessions s
    LEFT JOIN public.order_items oi ON oi.session_id = s.id
    LEFT JOIN public.users uo ON uo.id = s.opened_by_user_id
    LEFT JOIN public.users uc ON uc.id = s.closed_by_user_id
    WHERE {" AND ".join(where)}
    GROUP BY s.id, s.table_number, s.created_at, s.closed_at, s.opened_by_user_id, s.closed_by_user_id, opened_by, closed_by
    HAVING
      SUM(CASE WHEN oi.status = 'cancelled' AND COALESCE(oi.qty,0) > 0 THEN 1 ELSE 0 END) > 0
      OR
      SUM(CASE WHEN oi.status <> 'cancelled' AND COALESCE(oi.void_qty,0) > 0 THEN 1 ELSE 0 END) > 0
    ORDER BY s.closed_at DESC NULLS LAST
    LIMIT 500
    """

    conn = db.connect_db(None)
    try:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute(sql, params)
            rows = c.fetchall() or []
    finally:
        conn.close()

    out = []
    for r in rows:
        out.append({
            "session_id": r.get("session_id"),
            "table_number": r.get("table_number"),
            "opened_at_wib": r.get("created_wib") or "",
            "closed_at_wib": r.get("closed_wib") or "",
            "opened_by": r.get("opened_by") or "-",
            "closed_by": r.get("closed_by") or "-",
            "estimate": int((r.get("value_cancelled") or 0) + (r.get("value_void") or 0)),
        })

    return jsonify({"status": "ok", "rows": out})

@bp.get("/api/cancelled_sessions/<session_id>/items")
@login_required
@roles_required("admin", "cashier")
def cancelled_session_items_api(session_id):
    conn = db.connect_db(None)
    try:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute("""
                SELECT
                  oi.item_name,
                  oi.price,
                  SUM(CASE WHEN oi.status='cancelled' THEN oi.qty ELSE 0 END) AS qty_cancelled,
                  SUM(CASE WHEN oi.status<>'cancelled' THEN oi.void_qty ELSE 0 END) AS qty_void,
                  SUM(CASE WHEN oi.status='cancelled' THEN oi.qty * oi.price ELSE 0 END) AS value_cancelled,
                  SUM(CASE WHEN oi.status<>'cancelled' THEN oi.void_qty * oi.price ELSE 0 END) AS value_void
                FROM public.order_items oi
                WHERE oi.session_id = %s
                GROUP BY oi.item_name, oi.price
                HAVING
                  SUM(CASE WHEN oi.status='cancelled' THEN oi.qty ELSE 0 END) > 0
                  OR
                  SUM(CASE WHEN oi.status<>'cancelled' THEN oi.void_qty ELSE 0 END) > 0
                ORDER BY oi.item_name ASC
            """, (session_id,))
            rows = c.fetchall() or []
    finally:
        conn.close()

    items = []
    for r in rows:
        total_value = int((r.get("value_cancelled") or 0) + (r.get("value_void") or 0))
        items.append({
            "item_name": r.get("item_name"),
            "price": int(r.get("price") or 0),
            "qty_cancelled": float(r.get("qty_cancelled") or 0),
            "qty_void": float(r.get("qty_void") or 0),
            "total_value": total_value,
        })

    return jsonify({"status": "ok", "items": items})

@bp.get("/api/qr_settings")
@login_required
@roles_required("admin")
def get_qr_settings():
    return jsonify(load_qr_settings())

@bp.post("/api/qr_settings")
@login_required
@roles_required("admin")
def update_qr_settings():
    data = request.get_json(silent=True) or {}
    mode = (data.get("qr_session_mode") or data.get("mode") or data.get("qr_mode") or "").strip().lower()
    if mode not in ("session", "table"):
        return jsonify({"status": "error", "message": "invalid qr_session_mode"}), 400
    cfg = load_qr_settings()
    cfg["qr_session_mode"] = mode
    write_qr_settings(cfg)
    return jsonify({"status": "ok", "qr_session_mode": mode})


def _build_table_qr_url(table_number: str) -> str:
    cfg = current_app.config
    base = (cfg.get("QR_ORDER_BASE") or "").rstrip("/")
    default_lang = (cfg.get("QR_DEFAULT_LANG") or "id").strip().lower()
    table_safe = quote(str(table_number or "").strip(), safe="")
    if base:
        target = f"{base}/order/{table_safe}"
    else:
        target = f"/order/{table_safe}"
    return f"{target}?lang={default_lang}"


@bp.get("/tools/qr_a5")
@login_required
@roles_required("admin")
def qr_a5():
    table = (request.args.get("table") or "").strip()
    if not table:
        abort(400, "table required")
    qr_url = _build_table_qr_url(table)
    qr_b64 = qr_png_b64(qr_url)
    qr_png_url = f"data:image/png;base64,{qr_b64}"
    cfg = current_app.config
    brand_name = cfg.get("BRAND_NAME", "Demo Restaurant")
    logo_url = cfg.get("BRAND_LOGO_URL")
    wifi_ssid = cfg.get("GUEST_WIFI_SSID", "Demo Restaurant")
    wifi_pass = cfg.get("GUEST_WIFI_PASS", "demo-wifi-pass")
    issued_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    autoprint = (request.args.get("autoprint") == "1")
    return render_template(
        "qr_ticket.html",
        table=table,
        qr_url=qr_url,
        qr_png_url=qr_png_url,
        brand_name=brand_name,
        logo_url=logo_url,
        wifi_ssid=wifi_ssid,
        wifi_pass=wifi_pass,
        issued_at=issued_at,
        short_code=str(table).upper(),
        paper_mode="a4_half",
        show_meta=False,
        autoprint=autoprint,
    )


@bp.get("/api/config")
@login_required
@roles_required("admin")
def get_pos_config():
    return jsonify(get_app_config())


@bp.post("/api/config")
@login_required
@roles_required("admin")
def update_pos_config():
    data = request.get_json(silent=True) or {}
    payload = data.get("config") if isinstance(data, dict) and "config" in data else data
    try:
        cfg = update_config(payload or {})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc) or "update failed"}), 400
    return jsonify({"status": "ok", "config": cfg})


@bp.get("/tools/open_sessions")
@login_required
@roles_required("admin")
def list_open_sessions():
    """
    Return all active sessions (open tables) with metadata so admins can jump to them.
    """
    with db.connect_db(None) as conn, conn.cursor() as c:
        c.execute("""
            SELECT id, table_number, guest_name, COALESCE(pax,1) AS pax,
                   TO_CHAR(created_at AT TIME ZONE 'Asia/Jakarta', 'YYYY-MM-DD HH24:MI') AS opened_at
            FROM sessions
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        rows = c.fetchall()
    out = [
        {
            "id": r[0],
            "table_number": r[1],
            "guest_name": r[2] or "",
            "pax": int(r[3] or 1),
            "opened_at": r[4],
        }
        for r in rows
    ]
    return jsonify({"rows": out})


@bp.get("/tools/preview")
@login_required
@roles_required("admin")
def preview():
    with db.connect_db() as conn:
        tables = _list_public_tables(conn)
    return jsonify(status="ok", tables=tables)

@bp.post("/tools/nuke")
@login_required
@roles_required("admin")
def nuke():
    data = request.get_json(silent=True) or {}
    if (data.get("confirm") or "").strip() != "DELETE ALL":
        return jsonify(status="error", message='Konfirmasi salah. Ketik "DELETE ALL".'), 400

    with db.connect_db() as conn:
        tables = _list_public_tables(conn)
        if not tables:
            return jsonify(status="ok", truncated=0, tables=[])

        q = "TRUNCATE TABLE {} RESTART IDENTITY CASCADE;".format(", ".join(tables))
        with conn.cursor() as c:
            c.execute(q)
        conn.commit()

    return jsonify(status="ok", truncated=len(tables), tables=tables)

# -------- Simple background print test (does not replace existing flow) --------
_print_q = queue.Queue()
_print_results = {}
_print_thread_started = False


def _ensure_print_worker():
    global _print_thread_started
    if _print_thread_started:
        return

    def _worker():
        while True:
            job = _print_q.get()
            if job is None:
                _print_q.task_done()
                break
            job_id, html, printer_key, created_at = job
            try:
                job_ref = printing.print_html_receipt(html, printer_key=printer_key)
                _print_results[job_id] = {
                    "status": "done",
                    "ref": job_ref,
                    "finished_at": datetime.utcnow().isoformat() + "Z",
                }
            except Exception as e:
                _print_results[job_id] = {
                    "status": "error",
                    "error": str(e),
                    "finished_at": datetime.utcnow().isoformat() + "Z",
                }
            finally:
                _print_q.task_done()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    _print_thread_started = True

def _sample_receipt_html():
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <html>
      <head>
        <style>
          body {{ font-family: 'Courier New', monospace; margin: 6px; font-size: 14px; }}
          h2 {{ margin: 0 0 6px 0; font-size: 18px; }}
          .muted {{ color: #666; font-size: 12px; }}
          .box {{ border: 1px dashed #999; padding: 8px; border-radius: 6px; }}
        </style>
      </head>
      <body>
        <h2>TEST PRINT (Background)</h2>
        <div class="muted">Triggered from Admin Tools</div>
        <div class="box" style="margin-top:8px;">
          <div>Time: {ts}</div>
          <div>Table: SAMPLE-01</div>
          <div>PAX: 2</div>
          <div>Note: simple background print path</div>
        </div>
        <p style="margin-top:10px;">If this prints quickly and UI stays responsive, switch flows later.</p>
      </body>
    </html>
    """

@bp.get("/tools/print_test_hex")
@login_required
@roles_required("admin")
def print_test_hex():
    now = datetime.now()
    printed_at = now.strftime("%d-%m-%y %H:%M")
    header = {
        "table_number": "SAMPLE-01",
        "bill_label": "BILL",
        "pax": 2,
        "opened_at": printed_at,
        "printed_at": printed_at,
        "prepared_by": getattr(current_user, "full_name", None) or current_user.username,
        "guest_name": "Test Guest",
    }

    items = [
        {"name": "Nasi Goreng", "qty": 2, "unit_price": 25000, "line_total": 50000},
        {"name": "Es Teh Manis", "qty": 1, "unit_price": 8000, "line_total": 8000},
    ]

    subtotal = sum(it["line_total"] for it in items)
    totals = {
        "subtotal": subtotal,
        "discount_amount": 0,
        "discount_percent": 0,
        "packaging_fee": 0,
        "service": 0,
        "service_percent": 0,
        "tax": 0,
        "rounding": 0,
        "total": subtotal,
        "dp_applied": 0,
        "total_after_dp": subtotal,
    }

    payload = build_receipt_bytes(header, items, totals, title="TEST PRINT (BRIDGE)")
    return jsonify({"status": "ok", "hex": payload.hex()})

@bp.post("/tools/print_test")
@login_required
@roles_required("admin")
def print_test():
    """
    Enqueue a lightweight background print using server-side HTML->CUPS pipeline.
    Does NOT replace existing browser print; intended for trials.
    """
    _ensure_print_worker()
    data = request.get_json(silent=True) or {}
    job_id = uuid.uuid4().hex
    html = data.get("html") or _sample_receipt_html()
    printer_key = (data.get("printer") or "").strip() or None
    created_at = datetime.utcnow().isoformat() + "Z"
    _print_results[job_id] = {"status": "queued", "created_at": created_at}
    _print_q.put((job_id, html, printer_key, created_at))
    return jsonify({"status": "queued", "job_id": job_id})

@bp.get("/tools/print_status/<job_id>")
@login_required
@roles_required("admin")
def print_status(job_id):
    info = _print_results.get(job_id)
    if not info:
        return jsonify({"status": "unknown"}), 404
    return jsonify({"status": info.get("status"), "detail": info})
