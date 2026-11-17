import uuid
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv  
import psycopg
from psycopg.rows import dict_row
from collections import defaultdict
from zoneinfo import ZoneInfo
from decimal import Decimal
from utils.data.splits import normalize_split_meta
from .config_store import get_billing_config

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

TZ = ZoneInfo("Asia/Jakarta")
UNPAID_STATUSES = ("new", "edited", "served", "printed")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it in your .env or environment.")

# -----------------------------
# Connection helper
# -----------------------------
def connect_db(_ignored=None):
    return psycopg.connect(DATABASE_URL)

# -----------------------------
# Utility
# -----------------------------

def get_printables(_ignored, session_id):
    """Items that should be printed now: status in ('new','edited'); not cancelled/paid."""
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT id, item_name, qty, price, sauce, note, status, bill_group
            FROM order_items
            WHERE session_id=%s
              AND status IN ('new','edited')
            ORDER BY "timestamp", id
        """, (session_id,))
        return c.fetchall()

def mark_items_printed(_ignored, item_ids, by_user_id=None):
    if not item_ids:
        return
    placeholders = ",".join(["%s"] * len(item_ids))
    params = list(item_ids)
    with connect_db() as conn, conn.cursor() as c:
        c.execute(f"""
            UPDATE order_items
               SET status='printed', updated_by_user_id=%s
             WHERE id IN ({placeholders})
        """, [by_user_id] + params)

def combine_items(orders):
    combined = {}
    for order in orders:
        for item in order["items"]:
            key = (item["name"], item["price"])
            if key in combined:
                combined[key]["qty"] += item["qty"]
            else:
                combined[key] = {
                    "name": item["name"],
                    "price": item["price"],
                    "qty": item["qty"],
                }
    return list(combined.values())

def compute_prebill(session_id:str, group_label:str | None) -> dict:
    with connect_db() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, table_number, pax, guest_name, created_at
                FROM sessions
                WHERE id = %s       
            """, (session_id,))
            row = c.fetchone()
            if not row:
                raise ValueError("Session not found")
            
            sess = {
                "id": row[0],
                "table_number": row[1],
                "pax": row[2],
                "guest_name": row[3],
                "created_at": row[4],
            }

            g = (group_label or "").strip().lower()
            want_main = (g in ("", "main"))

            sql = """
                SELECT id, item_name, qty, price, total_price, sauce, note, status, "timestamp", bill_group
                FROM order_items
                WHERE session_id = %s
                    AND status = ANY(%s)
            """
            params = [session_id, list(UNPAID_STATUSES)]
            if want_main:
                sql += "AND bill_group IS NULL"

            else:
                sql += "AND bill_group = %s"
                params.append(group_label)
            
            sql += "ORDER BY \"timestamp\", id"
            c.execute(sql,params)
            items = c.fetchall()

    
            bucket = defaultdict(lambda: {"qty": 0, "unit_price": 0, "line_total": 0, "name": "", "sauce": None, "note": None})
            for r in items:
                _id, name, qty, unit_price, _tp, sauce, note, _st, _ts, _grp = r
                qdec = Decimal(str(qty or 0)).quantize(Decimal('0.1'))
                key = (name, unit_price, sauce or None, note or None)
                b = bucket[key]
                b["name"] = name
                b["unit_price"] = int(unit_price or 0)
                b["qty"] = Decimal(str(b["qty"])) + qdec
                b["sauce"] = sauce or None
                b["note"] = note or None
                b["line_total"] += int(_tp or (int(unit_price or 0) * float(qdec)))

            lines = list(bucket.values())

            lines.sort(key=lambda x: (x["name"].lower(), x["unit_price"]))

            for x in lines:
                x["qty"] = float(Decimal(str(x["qty"])).quantize(Decimal('0.1')))

            subtotal = sum(int(x["line_total"]) for x in lines)
            discount_percent = 0  
            discount_amount = round(subtotal * (discount_percent / 100))
            after_discount = subtotal - discount_amount
            billing_cfg = get_billing_config()
            service_pct = int(billing_cfg.get("service_percent", 5))
            tax_pct = int(billing_cfg.get("tax_percent", 10))
            tax_on_service = bool(billing_cfg.get("tax_on_service"))
            service = round(after_discount * (service_pct / 100.0))
            tax_base = after_discount + service if tax_on_service else after_discount
            tax = round(tax_base * (tax_pct / 100.0))
            total = after_discount + service + tax

            dp_total = get_dp_amount(None, session_id) or 0
            dp_used = get_dp_used(None, session_id) or 0
            dp_remaining = max(dp_total - dp_used, 0)
        
    bill_label = ("MAIN" if want_main else str(group_label))

    return {
        "header": {
            "session_id": sess["id"],
            "table_number": sess["table_number"],
            "pax": sess["pax"],
            "guest_name": sess["guest_name"],
            "opened_at": sess["created_at"], 
            "bill_label": bill_label
        },
        "lines": lines,
        "summary": {
            "subtotal": subtotal,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "service": service,
            "tax": tax,
            "total": total
        },
        "dp_available": dp_remaining
    }

# -----------------------------
# Schema init (Postgres)
# -----------------------------
def init_db(_ignored=None, schema_file="schema.pg.sql"):
    """
    Initialize DB by executing schema.pg.sql.
    Prefer running via psql in deploy scripts, but this is handy for dev.
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with connect_db() as conn:
        with conn.cursor() as c:
            c.execute(schema_sql)
        # with-conn will commit on success

# -----------------------------
# Sessions
# -----------------------------
def get_all_sessions(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT table_number, id, created_at FROM sessions")
        return c.fetchall()  # list[tuple]

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
            WHERE table_number = %s AND status = 'active'
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
    """Map table_number -> guest_name for active sessions."""
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT table_number, COALESCE(guest_name,'')
            FROM sessions
            WHERE status = 'active'
        """)
        rows = c.fetchall()
        return {r[0]: (r[1] or "") for r in rows}

def get_active_sessions(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT table_number, id, created_at FROM sessions WHERE status = 'active'")
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
        return c.fetchone()  # (id, table_number, status) or None

def get_open_session_for_table(table_number: str):
    """Return (id, table_number, status) for the newest active session on a table, or None."""
    with connect_db() as conn, conn.cursor() as c:
        c.execute(
            """
            SELECT id, table_number, status
            FROM sessions
            WHERE table_number = %s AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (table_number,)
        )
        return c.fetchone()

def open_session(table_number: str, guest_name: str | None = None, opened_by_user_id: int | None = None,
                 pax: int = 1, note: str | None = None, dp_amount: int = 0) -> str:
    """Create an active session and return its id (string)."""
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


def resolve_menu_price(item_name, menu_json):
    """
    item_name can be "Gurame — Bakar" or "Teh Manis Dingin".
    Use dish price_override if present; else base price.
    """
    for cat, items in menu_json.items():
        for base_name, meta in items.items():
            if item_name == base_name or item_name.startswith(base_name + " — "):
                dish_part = None
                if " — " in item_name:
                    dish_part = item_name.split(" — ", 1)[1]

                # ignore unavailable items
                if not meta.get("available", True):
                    raise ValueError(f"Item not available: {item_name}")

                base_price = int(meta.get("price_per_kg", 0))

                if dish_part:
                    dishes = meta.get("dishes") or []
                    for d in dishes:
                        if isinstance(d, str):
                            if d == dish_part:
                                return base_price  # no override
                        else:
                            if d.get("name") == dish_part:
                                if d.get("available", True) is False:
                                    raise ValueError(f"Dish not available: {item_name}")
                                if d.get("price_override") is not None:
                                    return int(d["price_override"])
                                return base_price
                    # dish not found => treat as base
                    return base_price
                return base_price
    raise ValueError(f"Menu item not found: {item_name}")

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def _norm_qty_half_step(q) -> Decimal:
    """
    Normalize qty to Decimal with 1 decimal place, ROUND_HALF_UP,
    and only allow .0 or .5 steps (> 0).
    Raises ValueError if invalid.
    """
    try:
        qd = Decimal(str(q)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid qty")
    if qd <= 0 or (qd * 10) % 5 != 0:
        raise ValueError("Qty must be > 0 and in 0.5 steps")
    return qd

def upsert_order_item(
    db_path,
    session_id,
    item_name,
    qty,
    price,
    sauce=None,
    note=None,
    table_number=None,
    created_by_user_id=None,
):
    # normalize qty -> Decimal(0.1 steps)
    try:
        qd = Decimal(str(qty)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    except Exception:
        return None
    if qd <= 0:
        return None

    p = int(price or 0)

    with psycopg.connect(db_path) as conn:
        with conn.cursor() as c:
            # look for a compatible open row
            c.execute(
                """
                SELECT id, qty, price, status
                  FROM order_items
                 WHERE session_id = %s
                   AND item_name  = %s
                   AND COALESCE(sauce,'') = COALESCE(%s,'')
                   AND COALESCE(note,'')  = COALESCE(%s,'')
                   AND status NOT IN ('paid','cancelled')
                 ORDER BY id
                 LIMIT 1
                """,
                (session_id, item_name, sauce, note),
            )
            row = c.fetchone()

            if row:
                oid, old_qty, old_price, old_status = row

                # If the existing line has already been sent to kitchen (printed/served),
                # DO NOT merge — insert a fresh "new" row for the delta.
                if str(old_status) in ('printed', 'served'):
                    total = int((qd * p).to_integral_value(rounding=ROUND_HALF_UP))
                    c.execute(
                        """
                        INSERT INTO order_items
                            (session_id, table_number, item_name, qty, price, total_price,
                             sauce, note, status, timestamp, created_by_user_id)
                        VALUES
                            (%s, %s, %s, %s::NUMERIC(10,1), %s, %s,
                             %s, %s, 'new', NOW(), %s)
                        RETURNING id
                        """,
                        (session_id, table_number, item_name, str(qd), p, total,
                         sauce, note, created_by_user_id),
                    )
                    oid_new = c.fetchone()[0]
                    conn.commit()
                    return oid_new

                # Else the row is still "new" or "edited" — safe to merge & mark edited
                new_qty = (Decimal(str(old_qty)) + qd).quantize(Decimal('0.1'))
                new_total = int((new_qty * int(old_price)).to_integral_value(rounding=ROUND_HALF_UP))

                c.execute(
                    """
                    UPDATE order_items
                       SET qty = %s::NUMERIC(10,1),
                           total_price = %s,
                           status = CASE WHEN status='new' THEN 'new' ELSE 'edited' END
                     WHERE id = %s
                    """,
                    (str(new_qty), new_total, oid),
                )
                conn.commit()
                return oid

            # No match — insert brand new "new" row
            total = int((qd * p).to_integral_value(rounding=ROUND_HALF_UP))
            c.execute(
                """
                INSERT INTO order_items
                    (session_id, table_number, item_name, qty, price, total_price,
                     sauce, note, status, timestamp, created_by_user_id)
                VALUES
                    (%s, %s, %s, %s::NUMERIC(10,1), %s, %s,
                     %s, %s, 'new', NOW(), %s)
                RETURNING id
                """,
                (session_id, table_number, item_name, str(qd), p, total,
                 sauce, note, created_by_user_id),
            )
            oid = c.fetchone()[0]
            conn.commit()
            return oid

# -----------------------------
# Payments
# -----------------------------
def add_payment(_ignored, session_id, final_amount, payment_method, paid_at, discount_percent, discount_value, card_type):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO payments(
                session_id, amount, method, paid_at, cash_received, change_given,
                discount_percent, discount_amount, card_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session_id, final_amount, payment_method, paid_at, None, None,
              discount_percent, discount_value, card_type))

def insert_payment(_ignored, session_id, amount, method, paid_at, cash_received,
                   change_given, discount_percent, discount_amount, tax, service,
                   total_before_discount, card_type, bill_group=None, created_by_user_id=None, dp_applied_amount=0):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO payments (
                session_id, amount, method, paid_at,
                cash_received, change_given,
                discount_percent, discount_amount,
                tax, service, total_before_discount,
                card_type, bill_group, created_by_user_id,
                dp_applied_amount
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            session_id, amount, method, paid_at,
            cash_received if cash_received is not None else None,
            change_given if change_given is not None else 0,
            discount_percent, discount_amount, tax, service,
            total_before_discount, card_type, bill_group, created_by_user_id,
            dp_applied_amount
        ))
        (pid,) = c.fetchone()
        return pid

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

def get_dp_remaining_after(session_id: str, up_to_payment_id: int):
    dp_total = get_dp_amount(None, session_id) or 0
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(dp_applied_amount),0)
            FROM payments
            WHERE session_id=%s AND id <= %s AND is_refund = FALSE
        """, (session_id, up_to_payment_id))
        (dp_used_upto,) = c.fetchone()
    return max(int(dp_total) - int(dp_used_upto or 0), 0)

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
        # Assuming is_refund is BOOLEAN in PG schema
        c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE is_refund = TRUE AND refund_of = %s", (payment_id,))
        (val,) = c.fetchone()
        return abs(val)  # refunds are stored as negative amounts

def insert_refund(_ignored, *, payment_id, amount, reason, user_id):
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

# -----------------------------
# Order items
# -----------------------------
def insert_order_item(_ignored, session_id, table_number, item_name, qty, price, sauce=None, note=None, created_by_user_id=None):
    ts = datetime.now().isoformat()
    qd = Decimal(str(qty)).quantize(Decimal('0.1'))
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO order_items (
                session_id, table_number, item_name, qty, price, total_price,
                sauce, note, status, "timestamp", created_by_user_id
            )
            VALUES (
                %s, %s, %s,
                (%s)::NUMERIC(10,1),
                %s,
                ROUND((%s)::NUMERIC(10,1) * %s)::INT,
                %s, %s, 'new', %s, %s
            )
        """, (session_id, table_number, item_name, str(qd), price, str(qd), price, sauce, note, ts, created_by_user_id))

def get_order_items_by_session(_ignored, session_id, bill_group=None):
    with connect_db() as conn, conn.cursor() as c:
        if bill_group is None:
            c.execute("""
                SELECT id, item_name, qty, price, total_price, sauce, note, status, "timestamp"
                FROM order_items
                WHERE session_id = %s AND status != 'cancelled' AND bill_group IS NULL
                ORDER BY "timestamp" ASC
            """, (session_id,))
        else:
            c.execute("""
                SELECT id, item_name, qty, price, total_price, sauce, note, status, "timestamp"
                FROM order_items
                WHERE session_id = %s AND status != 'cancelled' AND bill_group = %s
                ORDER BY "timestamp" ASC
            """, (session_id, bill_group))
        return c.fetchall()

def cancel_order_item(_ignored, item_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            UPDATE order_items
            SET status = 'cancelled'
            WHERE id = %s
        """, (item_id,))

def update_order_item_note(_ignored, item_ids, note, updated_by_user_id=None):
    if not item_ids: 
        return False, "No items"
    with connect_db() as conn, conn.cursor() as c:
        # prefer an unprinted line if exists
        c.execute("""
            SELECT id FROM order_items
            WHERE id = ANY(%s) AND status IN ('new','edited')
            ORDER BY id DESC
            LIMIT 1
        """, (item_ids,))
        row = c.fetchone()
        if not row:
            # else the newest printed/served/paid row
            c.execute("""
              SELECT id FROM order_items
              WHERE id = ANY(%s)
              ORDER BY id DESC
              LIMIT 1
            """, (item_ids,))
            row = c.fetchone()
        if not row:
            return False, "Item not found"
        target_id = row[0]
        c.execute("""
            UPDATE order_items
               SET note = %s,
                   updated_by_user_id = %s,
                   -- do NOT change status here (only editing notes)
                   timestamp = NOW()
             WHERE id = %s
        """, (note, updated_by_user_id, target_id))
        return (True, None) if c.rowcount else (False, "Item not found")

def update_order_item_qty(_ignored, item_id_or_ids, new_qty, updated_by_user_id=None):
    """
    Group-aware edit:
    - Accepts single id or list of ids from the grouped row.
    - Keeps already printed/served/paid rows intact.
    - Sets the unprinted portion so that (printed_qty + unprinted_qty) == desired new_qty.
    - If desired < printed_qty -> error (you'd need a kitchen void flow).
    - If desired == printed_qty -> cancels any unprinted rows (so nothing left to print).
    """
    # normalize ids
    if isinstance(item_id_or_ids, list):
        ids = [int(x) for x in item_id_or_ids]
    else:
        ids = [int(item_id_or_ids)]

    # normalize qty
    try:
        qd = Decimal(str(new_qty)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    except Exception:
        return False, "Invalid qty"

    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        # lock rows so concurrent edits won't race
        c.execute("""
            SELECT id, session_id, table_number, item_name, qty, price, sauce, note, status
            FROM order_items
            WHERE id = ANY(%s)
            ORDER BY id
            FOR UPDATE
        """, (ids,))
        rows = c.fetchall()
        if not rows:
            return False, "Item not found"

        printed_qty = sum(Decimal(str(r["qty"])) for r in rows
                          if r["status"] in ("printed","served","paid"))
        unprinted   = [r for r in rows if r["status"] in ("new","edited")]

        # block "below printed"
        if qd < 0:
            return False, "Qty harus >= 0"
        if qd < printed_qty:
            return False, f"Sudah dikirim {printed_qty}, minimal {printed_qty}"

        # handle zero (cancel unprinted only)
        if qd == 0:
            if printed_qty > 0:
                # can't zero out below printed
                return False, f"Sudah dikirim {printed_qty}, minimal {printed_qty}"
            if unprinted:
                c.execute("""
                    UPDATE order_items
                       SET status='cancelled', qty=0, total_price=0, updated_by_user_id=%s
                     WHERE id = ANY(%s)
                """, (updated_by_user_id, [r["id"] for r in unprinted]))
            return True, None

        desired_unprinted = (qd - printed_qty).quantize(Decimal('0.1'))

        # if nothing left to print, cancel any unprinted lines
        if desired_unprinted == 0:
            if unprinted:
                c.execute("""
                    UPDATE order_items
                       SET status='cancelled', qty=0, total_price=0, updated_by_user_id=%s
                     WHERE id = ANY(%s)
                """, (updated_by_user_id, [r["id"] for r in unprinted]))
            return True, None

        # ensure exactly one unprinted row equals desired_unprinted
        unit_price = int(rows[0]["price"] or 0)

        if unprinted:
            target = unprinted[0]
            total = int((desired_unprinted * unit_price).to_integral_value(rounding=ROUND_HALF_UP))
            c.execute("""
                UPDATE order_items
                   SET qty = %s::NUMERIC(10,1),
                       total_price = %s,
                       status='edited',
                       updated_by_user_id=%s
                 WHERE id = %s
            """, (str(desired_unprinted), total, updated_by_user_id, target["id"]))

            if len(unprinted) > 1:
                rest_ids = [r["id"] for r in unprinted[1:]]
                c.execute("""
                    UPDATE order_items
                       SET status='cancelled', qty=0, total_price=0, updated_by_user_id=%s
                     WHERE id = ANY(%s)
                """, (updated_by_user_id, rest_ids))
            return True, None

        # no unprinted row exists → insert a fresh one for the delta
        base = rows[0]
        total = int((desired_unprinted * unit_price).to_integral_value(rounding=ROUND_HALF_UP))
        c.execute("""
            INSERT INTO order_items
              (session_id, table_number, item_name, qty, price, total_price,
               sauce, note, status, "timestamp", created_by_user_id)
            VALUES
              (%s,%s,%s,%s::NUMERIC(10,1),%s,%s,
               %s,%s,'new',NOW(),%s)
        """, (base["session_id"], base["table_number"], base["item_name"],
              str(desired_unprinted), unit_price, total,
              base["sauce"], base["note"], updated_by_user_id))
        return True, None

def mark_items_paid(_ignored, session_id, bill_group=None):
    group = (bill_group or "").strip()
    with connect_db() as conn, conn.cursor() as c:
        main_alias = False
        if group and group.lower() != "main":
            c.execute("SELECT split_labels FROM sessions WHERE id = %s", (session_id,))
            row = c.fetchone()
            raw = row[0] if row else None
            try:
                parsed = json.loads(raw) if raw else []
            except Exception:
                parsed = []
            meta = normalize_split_meta(parsed)
            first = meta[0]["key"] if meta else None
            if first and str(first) == group:
                main_alias = True

        if not group or group.lower() == "main":
            c.execute("""
                UPDATE order_items
                SET status='paid'
                WHERE session_id=%s
                  AND status!='cancelled'
                  AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = 'main'
            """, (session_id,))
        elif main_alias:
            c.execute("""
                UPDATE order_items
                SET status='paid'
                WHERE session_id=%s
                  AND status!='cancelled'
                  AND (
                    COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
                    OR COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = 'main'
                  )
            """, (session_id, group))
        else:
            c.execute("""
                UPDATE order_items
                SET status='paid'
                WHERE session_id=%s
                  AND status!='cancelled'
                  AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group))

def session_is_fully_paid(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COUNT(*)
            FROM order_items
            WHERE session_id=%s
              AND status!='cancelled'
              AND status!='paid'
        """, (session_id,))
        (remaining,) = c.fetchone()
        return remaining == 0

def get_all_order_items_by_session(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT
                id, item_name, qty, price, total_price,
                sauce, note, status, "timestamp", bill_group
            FROM order_items
            WHERE session_id = %s AND status != 'cancelled'
            ORDER BY "timestamp" ASC
        """, (session_id,))
        return c.fetchall()

# -----------------------------
# Split labels / bill groups
# -----------------------------
def normalize_group(value):
    if value is None:
        return None
    g = str(value).strip()
    if g == "" or g.lower() == "main":
        return None
    return g if g.isdigit() else None

def get_split_labels(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT split_labels FROM sessions WHERE id=%s", (session_id,))
        row = c.fetchone()
        if not row or row[0] is None:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

def set_split_labels(_ignored, session_id, labels):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("UPDATE sessions SET split_labels=%s WHERE id=%s", (json.dumps(labels), session_id,))

def clear_split_labels(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("UPDATE order_items SET bill_group=NULL WHERE session_id=%s", (session_id,))
        c.execute("UPDATE sessions SET split_labels=NULL WHERE id=%s", (session_id,))

def set_item_bill_group(_ignored, item_id, bill_group, by_user_id=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            UPDATE order_items
            SET bill_group = %s, updated_by_user_id = %s
            WHERE id = %s
        """, (bill_group, by_user_id, item_id))

def set_items_bill_group(_ignored, item_ids, bill_group, by_user_id=None):
    if not item_ids:
        return
    placeholders = ",".join(["%s"] * len(item_ids))
    params = [bill_group, by_user_id] + list(item_ids)
    with connect_db() as conn, conn.cursor() as c:
        c.execute(f"""
            UPDATE order_items
            SET bill_group = %s, updated_by_user_id = %s
            WHERE id IN ({placeholders})
        """, params)

# -----------------------------
# Analytics / indexes
# -----------------------------
def ensure_analytics_indexes(_ignored=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_paid_at ON payments(paid_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(method)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_ts ON order_items("timestamp")')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_status ON order_items(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_order_items_item ON order_items(item_name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_closed_at ON sessions(closed_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_reservations_date_time ON reservations(date, time)')

# -----------------------------
# Deposits (DP)
# -----------------------------
def get_dp_used(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COALESCE(SUM(dp_applied_amount),0)
            FROM payments
            WHERE session_id=%s
        """, (session_id,))
        (val,) = c.fetchone()
        return val or 0

def get_dp_amount(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT dp_amount FROM sessions WHERE id = %s", (session_id,))
        row = c.fetchone()
        return row[0] if row else 0

# -----------------------------
# Unpaid / merging helpers
# -----------------------------
def get_unpaid_open_items(_ignored, session_id):
    """Items that can be merged (skip cancelled/paid). Returns list[dict]."""
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT id, item_name, qty, price, total_price, sauce, note, status, bill_group, "timestamp" AS timestamp
            FROM order_items
            WHERE session_id = %s
              AND status NOT IN ('cancelled','paid')
        """, (session_id,))
        return c.fetchall()

def sessions_active_status(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT status FROM sessions WHERE id = %s", (session_id,))
        row = c.fetchone()
        return row[0] if row else None

def merge_sessions(_ignored, source_session_id, target_session_id, by_user_id=None):
    """
    Merge all OPEN (not cancelled/paid) items from source into target.
    - Combines identical lines (item_name, price, sauce, note, bill_group).
    - Carries over DP and union of split labels.
    - Closes the source session.
    Constraints:
    - Both sessions must exist and be 'active'.
    - Source must have NO payments and NO paid items.
    """
    now_iso = datetime.now().isoformat()

    with connect_db() as conn:
        with conn.cursor(row_factory=dict_row) as c:
            try:
                c.execute("SELECT id, table_number, status, dp_amount, split_labels FROM sessions WHERE id = %s", (source_session_id,))
                src = c.fetchone()
                c.execute("SELECT id, table_number, status, dp_amount, split_labels FROM sessions WHERE id = %s", (target_session_id,))
                tgt = c.fetchone()
                if not src or not tgt:
                    raise ValueError("Session tidak ditemukan")
                if (src["status"] != "active") or (tgt["status"] != "active"):
                    raise ValueError("Hanya bisa merge antara sesi yang masih aktif")

                def _has_non_dp_payments(cur, sess_id, dp_amount):
                    cur.execute(
                        """
                        SELECT COALESCE(is_dp, FALSE) AS is_dp,
                               COALESCE(is_refund, FALSE) AS is_refund,
                               COALESCE(amount, 0) AS amount,
                               COALESCE(dp_applied_amount, 0) AS dp_applied_amount
                          FROM payments
                         WHERE session_id = %s
                        """,
                        (sess_id,),
                    )
                    rows = cur.fetchall() or []
                    non_ref = [r for r in rows if not r["is_refund"]]
                    if not non_ref:
                        return False
                    if any(int(r["dp_applied_amount"] or 0) > 0 for r in non_ref):
                        return True

                    def _is_dp_like(row):
                        if row["is_dp"]:
                            return True
                        return dp_amount and int(row["amount"] or 0) == int(dp_amount) and int(row["dp_applied_amount"] or 0) == 0

                    if all(_is_dp_like(r) for r in non_ref):
                        return False
                    return any((not r["is_dp"]) and int(r["amount"] or 0) > 0 for r in non_ref)

                # Source has any paid items?
                c.execute("SELECT COUNT(*) AS n FROM order_items WHERE session_id = %s AND status = 'paid'", (source_session_id,))
                if (c.fetchone()["n"] or 0) > 0:
                    raise ValueError("Ada item yang sudah dibayar di sesi sumber — tidak bisa merge")

                # Source has any non-DP payments?
                if _has_non_dp_payments(c, source_session_id, src["dp_amount"] or 0):
                    raise ValueError("Sesi sumber sudah memiliki pembayaran — selesaikan/void dulu sebelum merge")

                # Fetch open items from source
                c.execute("""
                    SELECT id, item_name, qty, price, total_price, sauce, note, bill_group
                    FROM order_items
                    WHERE session_id = %s
                      AND status NOT IN ('cancelled','paid')
                """, (source_session_id,))
                src_items = c.fetchall()

                # For each source item → try to find matching target row to combine
                for r in src_items:
                    name  = r["item_name"]
                    price = r["price"]
                    sauce = r["sauce"]
                    note  = r["note"]
                    grp   = r["bill_group"]

                    c.execute("""
                        SELECT id, qty, total_price
                        FROM order_items
                        WHERE session_id = %s
                          AND status NOT IN ('cancelled','paid')
                          AND item_name = %s
                          AND price = %s
                          AND COALESCE(sauce, '') = COALESCE(%s, '')
                          AND COALESCE(note,  '') = COALESCE(%s, '')
                          AND COALESCE(bill_group,'') = COALESCE(%s, '')
                        LIMIT 1
                    """, (target_session_id, name, price, sauce, note, grp))
                    match = c.fetchone()

                    if match:
                        new_qty = (match["qty"] or 0) + (r["qty"] or 0)
                        new_total = (match["total_price"] or 0) + (r["total_price"] or 0)
                        c.execute("""
                            UPDATE order_items
                            SET qty = %s, total_price = %s, updated_by_user_id = %s, "timestamp" = %s
                            WHERE id = %s
                        """, (new_qty, new_total, by_user_id, now_iso, match["id"]))
                        c.execute("DELETE FROM order_items WHERE id = %s", (r["id"],))
                    else:
                        c.execute("""
                            UPDATE order_items
                            SET session_id = %s, updated_by_user_id = %s, "timestamp" = %s
                            WHERE id = %s
                        """, (target_session_id, by_user_id, now_iso, r["id"]))

                # Merge DP
                src_dp = src["dp_amount"] or 0
                tgt_dp = tgt["dp_amount"] or 0
                if src_dp:
                    c.execute("UPDATE sessions SET dp_amount = %s WHERE id = %s", (src_dp + tgt_dp, target_session_id))
                    c.execute("UPDATE sessions SET dp_amount = 0 WHERE id = %s", (source_session_id,))

                # Merge split labels (union)
                def _load_meta(raw):
                    if not raw:
                        return []
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = []
                    return normalize_split_meta(parsed)

                src_meta = _load_meta(src["split_labels"])
                tgt_meta = _load_meta(tgt["split_labels"])

                merged = {}
                for m in tgt_meta:
                    merged[m["key"]] = {"key": m["key"], "name": m.get("name") or ""}
                for m in src_meta:
                    key = m["key"]
                    if key in merged:
                        if not merged[key].get("name") and m.get("name"):
                            merged[key]["name"] = m.get("name") or ""
                    else:
                        merged[key] = {"key": key, "name": m.get("name") or ""}

                union = sorted(merged.values(), key=lambda x: int(x["key"]))
                c.execute(
                    "UPDATE sessions SET split_labels = %s WHERE id = %s",
                    (json.dumps(union) if union else None, target_session_id),
                )

                # Close the source session
                c.execute("""
                    UPDATE sessions
                    SET status='closed', closed_at=%s, closed_by_user_id=%s
                    WHERE id=%s
                """, (now_iso, by_user_id, source_session_id))

            except Exception as e:
                conn.rollback()
                return False, str(e)

        # with-conn will commit here if no rollback happened above
        return True, {"target_table": tgt["table_number"]}

# -----------------------------
# Reservations
# -----------------------------
def insert_reservation(_ignored, *, guest_name, phone, pax, date, time, notes, dp_amount, dp_method, created_by_user_id):
    now = datetime.now().isoformat()
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO reservations(
                guest_name, phone, pax, date, time, notes, status,
                table_number, session_id, created_at, created_by_user_id,
                dp_amount, dp_method, dp_paid_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,'pending', NULL, NULL, %s, %s, %s, %s, %s)
        """, (guest_name, phone, pax, date, time, notes, now, created_by_user_id,
              dp_amount, dp_method, now if dp_amount > 0 else None))

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

def seat_reservation(_ignored, reservation_id, table_number, *, pax, guest_name, note, by_user_id):
    """
    Create a session at table_number, transfer DP, copy preorder items to order_items, mark reservation seated.
    """
    now = datetime.now().isoformat()
    session_id = str(uuid.uuid4())

    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        # ensure table is free
        c.execute("""
            SELECT id FROM sessions
            WHERE table_number = %s AND status = 'active'
            LIMIT 1
        """, (table_number,))
        if c.fetchone():
            raise ValueError("Meja sedang terpakai")

        # create session
        c.execute("""
            INSERT INTO sessions(id, pax, table_number, created_at, guest_name, dp_amount, note, status, opened_by_user_id)
            VALUES(%s,%s,%s,%s,%s,0,%s,'active',%s)
        """, (session_id, pax, table_number, now, guest_name, note, by_user_id))

        # fetch reservation
        c.execute("SELECT * FROM reservations WHERE id=%s", (reservation_id,))
        r = c.fetchone()
        if not r:
            raise ValueError("Reservasi tidak ditemukan")

        # transfer DP
        dp = r.get("dp_amount") or 0
        if dp > 0:
            c.execute("UPDATE sessions SET dp_amount = %s WHERE id = %s", (dp, session_id))

        # copy preorder items
        c.execute("SELECT * FROM reservation_items WHERE reservation_id=%s", (reservation_id,))
        items = c.fetchall()
        for it in items:
            c.execute("""
                INSERT INTO order_items(session_id, table_number, item_name, qty, price, total_price, sauce, note, status, "timestamp", created_by_user_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'new',%s,%s)
            """, (
                session_id, table_number, it["item_name"], it["qty"], it["price"],
                (it["qty"] * it["price"]), it["sauce"], it["note"], now, by_user_id
            ))

        # link reservation -> session
        c.execute("""
            UPDATE reservations
            SET status='seated', session_id=%s, seated_by_user_id=%s, table_number=%s
            WHERE id=%s
        """, (session_id, by_user_id, table_number, reservation_id))

    return session_id

# -----------------------------
# Moves
# -----------------------------
def move_session_table(_ignored, session_id, to_table, by_user_id=None):
    with connect_db() as conn, conn.cursor() as c:
        # check target still free inside transaction
        c.execute("""
            SELECT id FROM sessions
            WHERE table_number = %s AND status = 'active'
            LIMIT 1
        """, (to_table,))
        row = c.fetchone()
        if row:
            raise RuntimeError("Target table became occupied")

        # update session table_number
        c.execute("""
            UPDATE sessions
            SET table_number = %s
            WHERE id = %s AND status = 'active'
        """, (to_table, session_id))

        if c.rowcount == 0:
            raise RuntimeError("session not active")

        # keep order_items denormalized column in sync
        c.execute("""
            UPDATE order_items
            SET table_number = %s
            WHERE session_id = %s
        """, (to_table, session_id))

# -----------------------------
# Reservations listing (time filter)
# -----------------------------
def get_upcoming_reservations(_ignored=None):
    """
    If reservations.date/time are TEXT ('YYYY-MM-DD' / 'HH:MM'):
      uses to_timestamp(date || ' ' || time, 'YYYY-MM-DD HH24:MI')
    If you store DATE and TIME types instead, a tighter filter is:
      WHERE (date + time) >= now()
    """
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT id, guest_name, phone, pax, date, time, notes,
                   status, table_number, session_id
            FROM reservations
            WHERE to_timestamp(date || ' ' || time, 'YYYY-MM-DD HH24:MI') >= (now() AT TIME ZONE 'Asia/Jakarta')
            ORDER BY to_timestamp(date || ' ' || time, 'YYYY-MM-DD HH24:MI') ASC
        """)
        return c.fetchall()
    
# -----------------------------
# Tables
# -----------------------------
def load_tables(json_path="static/tables.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def group_order_items(order_items):
    """
    order_items: list of tuples
      (id, name, qty, price, total_price, sauce, note, status, timestamp, bill_group)

    Returns list of dicts with:
      item_name, sauce, note, qty, price, total_price, bill_group, ids, all_paid,
      qty_printed, qty_unprinted, print_state
    """
    grouped = {}
    for item in order_items:
        item_id, name, qty, price, total_price, sauce, note, status, timestamp, bill_group = item

        key = (name, sauce, note, bill_group)
        if key not in grouped:
            grouped[key] = {
                "item_name": name,
                "sauce": sauce,
                "note": note,
                "qty": Decimal('0.0'),
                "price": price,
                "total_price": 0,
                "bill_group": bill_group,
                "ids": [],
                "all_paid": (status == "paid"),
                "qty_printed": Decimal('0.0'),
                "qty_unprinted": Decimal('0.0'),
            }

        g = grouped[key]
        qd = Decimal(str(qty or 0))
        g["qty"] += qd
        g["total_price"] += int(total_price or 0)
        g["ids"].append(item_id)
        g["all_paid"] = g["all_paid"] and (status == "paid")

        if status in ("printed", "served", "paid"):
            g["qty_printed"] += qd
        elif status in ("new", "edited"):
            g["qty_unprinted"] += qd
        # (cancelled rows are filtered before we get here)

    out = []
    for g in grouped.values():
        if g["qty_unprinted"] == 0 and g["qty_printed"] > 0:
            g["print_state"] = "printed_all"
        elif g["qty_unprinted"] > 0 and g["qty_printed"] > 0:
            g["print_state"] = "printed_partial"
        else:
            g["print_state"] = "unprinted"
        # cast totals/qty for templating convenience
        g["qty"] = float(g["qty"])
        g["qty_printed"] = float(g["qty_printed"])
        g["qty_unprinted"] = float(g["qty_unprinted"])
        out.append(g)

    return out

def consolidate_printed_lines(_ignored, session_id):
    """
    Merge rows that are already printed/served and share the same key
    (item_name, price, sauce, note, bill_group) into a single row.
    Keeps the lowest id as the keeper, sums qty & total_price, deletes the rest.
    """
    with connect_db() as conn, conn.cursor() as c:
        # find groups with >1 printed/served rows
        c.execute("""
            SELECT
              item_name,
              price,
              COALESCE(sauce,'')  AS sauce_key,
              COALESCE(note,'')   AS note_key,
              COALESCE(bill_group,'') AS grp_key,
              ARRAY_AGG(id ORDER BY id)            AS ids,
              SUM(qty)::NUMERIC(10,1)              AS qty_sum,
              SUM(total_price)::INT                AS total_sum
            FROM order_items
            WHERE session_id=%s
              AND status IN ('printed','served')
            GROUP BY item_name, price, COALESCE(sauce,''), COALESCE(note,''), COALESCE(bill_group,'')
            HAVING COUNT(*) > 1
        """, (session_id,))
        groups = c.fetchall()

        for (item_name, price, sauce_key, note_key, grp_key, ids, qty_sum, total_sum) in groups:
            keep_id = ids[0]
            delete_ids = ids[1:]
            # update keeper with sums
            c.execute("""
                UPDATE order_items
                   SET qty = %s::NUMERIC(10,1),
                       total_price = %s
                 WHERE id = %s
            """, (str(qty_sum), int(total_sum), keep_id))
            # remove duplicates
            if delete_ids:
                c.execute("DELETE FROM order_items WHERE id = ANY(%s)", (delete_ids,))
