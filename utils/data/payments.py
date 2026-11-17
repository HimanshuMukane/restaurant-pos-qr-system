from psycopg.rows import dict_row
from .core import connect_db
from .splits import normalize_group
from decimal import Decimal

def add_payment(_ignored, session_id, final_amount, payment_method, paid_at, discount_percent, discount_value, card_type):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO payments(
                session_id, amount, method, paid_at, cash_received, change_given,
                discount_percent, discount_amount, card_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session_id, final_amount, payment_method, paid_at, None, None,
              discount_percent, discount_value, card_type))

def insert_payment(
    _ignored,
    session_id,
    amount,
    method,
    paid_at,
    cash_received,
    change_given,
    discount_percent,
    discount_amount,
    tax,
    service,
    total_before_discount,
    card_type,
    bill_group=None,
    created_by_user_id=None,
    dp_applied_amount=0,
    is_dp=False,   # NEW
):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO payments (
                session_id, amount, method, paid_at,
                cash_received, change_given,
                discount_percent, discount_amount,
                tax, service, total_before_discount,
                card_type, bill_group, created_by_user_id,
                dp_applied_amount, is_dp
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            RETURNING id
        """, (
            session_id,
            amount,
            method,
            paid_at,
            cash_received if cash_received is not None else None,
            change_given if change_given is not None else 0,
            discount_percent,
            discount_amount,
            tax,
            service,
            total_before_discount,
            card_type,
            bill_group,
            created_by_user_id,
            dp_applied_amount,
            bool(is_dp),
        ))
        (pid,) = c.fetchone()
        return pid


def has_payments(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT COUNT(*) FROM payments WHERE session_id = %s", (session_id,))
        (n,) = c.fetchone()
        return (n or 0) > 0

def get_payment(_ignored, payment_id):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        return c.fetchone()

def get_refunded_total(_ignored, payment_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE is_refund = TRUE AND refund_of = %s", (payment_id,))
        (val,) = c.fetchone()
        return abs(val)

def insert_refund(_ignored, *, payment_id, amount, reason, user_id):
    from datetime import datetime
    now = datetime.now().isoformat()
    orig = get_payment(None, payment_id)
    if not orig:
        raise ValueError("Pembayaran tidak ditemukan")
    if orig["amount"] <= 0:
        raise ValueError("Tidak bisa refund dari baris non-penjualan")
    already = get_refunded_total(None, payment_id)
    if amount <= 0 or amount > (orig["amount"] - already):
        raise ValueError("Nilai refund tidak valid")

    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO payments(
                session_id, amount, method, paid_at,
                cash_received, change_given, discount_percent, discount_amount,
                tax, service, total_before_discount, card_type,
                created_by_user_id, bill_group, dp_applied_amount,
                is_refund, refund_of, refund_reason, refunded_by_user_id
            )
            VALUES (%s, %s, %s, %s,
                    NULL, NULL, 0, 0,
                    0, 0, 0, NULL,
                    %s, NULL, 0,
                    TRUE, %s, %s, %s)
        """, (
            orig["session_id"],
            -int(amount),
            orig["method"], now,
            user_id, payment_id, (reason or ""), user_id
        ))

def get_dp_used(_ignored, session_id):
    """
    Total DP that has been APPLIED to bills so far.

    We count only:
      - non-DP payments (is_dp = FALSE)
      - non-refund rows (is_refund = FALSE)
    because DP application happens on final payments, not on the DP payments themselves.
    """
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(dp_applied_amount), 0)
            FROM payments
            WHERE session_id = %s
              AND is_dp = FALSE
              AND is_refund = FALSE
        """, (session_id,))
        (val,) = c.fetchone()
        return int(val or 0)

def get_dp_amount(_ignored, session_id):
    """
    Total DP ever collected for this session, **net of DP refunds**.

    New model:
      - Start from sum(amount) where is_dp = TRUE AND is_refund = FALSE
        (all DP payments).
      - Then add any refund rows that target those DP payments
        (is_refund = TRUE AND refund_of = DP payment id, amounts are negative).

    Backward compatible:
      - If there are no DP-payment rows yet, fall back to sessions.dp_amount
        so old sessions keep working.
    """
    with connect_db() as conn, conn.cursor() as c:
        # 1) DP payments (as before)
        c.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total_dp,
                   COUNT(*) AS n_rows
            FROM payments
            WHERE session_id = %s
              AND is_dp = TRUE
              AND is_refund = FALSE
        """, (session_id,))
        total_dp, n_rows = c.fetchone()
        total_dp = int(total_dp or 0)
        n_rows   = int(n_rows or 0)

        # No DP payment rows → legacy fallback to sessions.dp_amount
        if n_rows == 0:
            c.execute("SELECT dp_amount FROM sessions WHERE id = %s", (session_id,))
            row = c.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

        # 2) DP refunds: negative rows that refund those DP payments
        c.execute("""
            SELECT COALESCE(SUM(p_ref.amount), 0)
            FROM payments AS p_ref
            WHERE p_ref.session_id = %s
              AND p_ref.is_refund = TRUE
              AND p_ref.refund_of IN (
                  SELECT id
                  FROM payments
                  WHERE session_id = %s
                    AND is_dp = TRUE
              )
        """, (session_id, session_id))
        (dp_refunds,) = c.fetchone()
        dp_refunds = int(dp_refunds or 0)   # usually <= 0

        # Net DP balance = DP payments (+) + DP refunds (-)
        return total_dp + dp_refunds



def get_dp_remaining_after(session_id: str, up_to_payment_id: int):
    """
    DP remaining after applying all payments up to a given payment_id.

    - dp_total comes from get_dp_amount (payments + legacy fallback).
    - dp_used_upto = sum(dp_applied_amount) on NON-DP, NON-refund payments
      with id <= up_to_payment_id.
    """
    dp_total = get_dp_amount(None, session_id) or 0

    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(dp_applied_amount), 0)
            FROM payments
            WHERE session_id = %s
              AND id <= %s
              AND is_dp = FALSE
              AND is_refund = FALSE
        """, (session_id, up_to_payment_id))
        (dp_used_upto,) = c.fetchone()

    return max(int(dp_total) - int(dp_used_upto or 0), 0)


def get_receipt_lines_by_group(session_id: str, group_label: str | None):
    grp = normalize_group(group_label)
    with connect_db() as conn, conn.cursor() as c:
        if grp is None:
            c.execute("""
                SELECT item_name, qty, price, total_price, note
                FROM order_items
                WHERE session_id=%s AND status='paid' AND bill_group IS NULL
                ORDER BY "timestamp", id
            """, (session_id,))
        else:
            c.execute("""
                SELECT item_name, qty, price, total_price, note
                FROM order_items
                WHERE session_id=%s AND status='paid' AND bill_group=%s
                ORDER BY "timestamp", id
            """, (session_id, grp))
        rows = c.fetchall()
    return [
        {
            "name": r[0],
            "qty": float(Decimal(str(r[1] or 0))),
            "unit_price": int(r[2] or 0),
            "line_total": int(r[3] or 0),
            "note": r[4] or None
        }
        for r in rows
    ]