from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from psycopg.rows import dict_row
from .core import connect_db, UNPAID_STATUSES
import psycopg


def get_printables(_ignored, session_id):
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

def insert_order_item(
    _ignored,
    session_id,
    table_number,
    item_name,
    qty,
    price,
    sauce=None,
    note=None,
    created_by_user_id=None,
    bill_group=None,  # NEW
):
    qd = Decimal(str(qty)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    bg = (bill_group or "").strip()

    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            INSERT INTO public.order_items (
                session_id,
                table_number,
                item_name,
                qty,
                price,
                total_price,
                sauce,
                note,
                status,
                "timestamp",
                created_by_user_id,
                bill_group
            )
            VALUES (
                %s,                 -- session_id
                %s,                 -- table_number
                %s,                 -- item_name
                (%s)::NUMERIC(10,1),
                %s,                 -- price
                ROUND((%s)::NUMERIC(10,1) * %s)::INT,
                %s,                 -- sauce
                %s,                 -- note
                'new',
                NOW(),
                %s,                 -- created_by_user_id
                COALESCE(NULLIF(TRIM(%s), ''), 'main') -- bill_group
            )
            RETURNING id
        """, (
            session_id,
            table_number,
            item_name,
            str(qd), price, str(qd), price,
            sauce,
            note,
            created_by_user_id,
            bg,
        ))
        new_id = c.fetchone()[0]
        conn.commit()
        return new_id


def get_order_items_by_session(_ignored, session_id, bill_group=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT
                id, item_name, qty, price, total_price,
                sauce, note, status, "timestamp",
                bill_group,                            -- index 9
                COALESCE(void_qty, 0) AS void_qty     -- index 10
            FROM order_items
            WHERE session_id = %s
              AND status != 'cancelled'
              AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main')
                  = COALESCE(NULLIF(TRIM(%s), ''), 'main')
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
        c.execute("""
            SELECT id FROM order_items
            WHERE id = ANY(%s) AND status IN ('new','edited')
            ORDER BY id DESC
            LIMIT 1
        """, (item_ids,))
        row = c.fetchone()
        if not row:
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
                   timestamp = NOW()
             WHERE id = %s
        """, (note, updated_by_user_id, target_id))
        return (True, None) if c.rowcount else (False, "Item not found")

from decimal import Decimal, ROUND_HALF_UP

def update_order_item_qty(_ignored, item_id_or_ids, new_qty, updated_by_user_id=None):
    from psycopg.rows import dict_row as _dict_row

    # Normalize IDs list
    if isinstance(item_id_or_ids, list):
        ids = [int(x) for x in item_id_or_ids]
    else:
        ids = [int(item_id_or_ids)]

    # Coerce to 0.1 steps
    try:
        qd = Decimal(str(new_qty)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    except Exception:
        return False, "Invalid qty", None
    if qd < 0:
        return False, "Qty harus >= 0", None

    with connect_db() as conn, conn.cursor(row_factory=_dict_row) as c:
        # Lock the rows so we can atomically adjust voids/unprinted rows
        c.execute("""
            SELECT id, session_id, table_number, item_name,
                   qty, COALESCE(void_qty, 0) AS void_qty,
                   price, sauce, note, status, bill_group
              FROM order_items
             WHERE id = ANY(%s)
             ORDER BY id
             FOR UPDATE
        """, (ids,))
        rows = c.fetchall()
        if not rows:
            return False, "Item not found", None

        # Partition rows by status
        PRINTED_ST   = ("printed", "served", "paid")
        UNPRINTED_ST = ("new", "edited")  # you said edited is NOT printed

        printed_rows   = [r for r in rows if (r["status"] or "").lower() in PRINTED_ST]
        unprinted_rows = [r for r in rows if (r["status"] or "").lower() in UNPRINTED_ST]

        # Effective printed = max(qty - void_qty, 0) across printed_rows.
        # IMPORTANT: parenthesize the generator when providing a start value to sum().
        effective_printed = sum(
            (
                max(Decimal(str(r["qty"])) - Decimal(str(r.get("void_qty", 0))), Decimal('0.0'))
                for r in printed_rows
            ),
            Decimal('0.0')  # keep result as Decimal even if there are no printed rows
        ).quantize(Decimal('0.1'))


        # If target is below effective_printed, we must add void(s) to printed rows
        void_delta = (effective_printed - qd) if qd < effective_printed else Decimal('0.0')
        void_delta = void_delta.quantize(Decimal('0.1'))

        if void_delta > 0:
            # Apply voids to printed rows, newest first
            remaining = void_delta
            for r in sorted(printed_rows, key=lambda x: x["id"], reverse=True):
                if remaining <= 0:
                    break
                row_qty      = Decimal(str(r["qty"]))
                row_void_now = Decimal(str(r.get("void_qty", 0)))
                room = (row_qty - row_void_now)  # already Decimal
                if room <= 0:
                    continue
                take = remaining if remaining <= room else room
                if take > 0:
                    c.execute("""
                        UPDATE order_items
                           SET void_qty = (COALESCE(void_qty,0) + %s::NUMERIC(10,1)),
                               updated_by_user_id = %s,
                               updated_at = NOW()
                         WHERE id = %s
                    """, (str(take.quantize(Decimal('0.1'))), updated_by_user_id, r["id"]))
                    remaining = (remaining - take).quantize(Decimal('0.1'))
            # any tiny remainder < 0.1 is ignored due to quantization

        # Unprinted side should hold whatever remains to reach qd
        effective_printed_after = (effective_printed - void_delta).quantize(Decimal('0.1'))
        desired_unprinted = (qd - effective_printed_after)
        if desired_unprinted < 0:
            desired_unprinted = Decimal('0.0')
        desired_unprinted = desired_unprinted.quantize(Decimal('0.1'))

        unit_price = int(rows[0]["price"] or 0)
        # Preserve bill_group for any newly inserted remainder rows (split-safe).
        group_val = None
        for r in rows:
            bg = (r.get("bill_group") or "").strip()
            if bg:
                group_val = bg
                break

        if desired_unprinted == Decimal('0.0'):
            # Cancel any existing unprinted rows
            if unprinted_rows:
                c.execute("""
                    UPDATE order_items
                       SET status='cancelled',
                           qty=0,
                           total_price=0,
                           updated_by_user_id=%s,
                           updated_at=NOW()
                     WHERE id = ANY(%s)
                """, (updated_by_user_id, [r["id"] for r in unprinted_rows]))
            conn.commit()
            return True, None, {"void_delta": float(void_delta)}

        # Need some unprinted qty available
        if unprinted_rows:
            # Put entire desired_unprinted onto the first unprinted row, cancel the rest
            target = unprinted_rows[0]
            total = int((desired_unprinted * Decimal(unit_price)).to_integral_value(rounding=ROUND_HALF_UP))
            c.execute("""
                UPDATE order_items
                   SET qty = %s::NUMERIC(10,1),
                       total_price = %s,
                       status = 'edited',
                       updated_by_user_id = %s,
                       updated_at = NOW()
                 WHERE id = %s
            """, (str(desired_unprinted), total, updated_by_user_id, target["id"]))

            if len(unprinted_rows) > 1:
                rest_ids = [r["id"] for r in unprinted_rows[1:]]
                c.execute("""
                    UPDATE order_items
                       SET status='cancelled',
                           qty=0,
                           total_price=0,
                           updated_by_user_id=%s,
                           updated_at=NOW()
                     WHERE id = ANY(%s)
                """, (updated_by_user_id, rest_ids))
            conn.commit()
            return True, None, {"void_delta": float(void_delta)}

        # No unprinted rows exist; insert a new one for the remainder
        base = rows[0]
        total = int((desired_unprinted * Decimal(unit_price)).to_integral_value(rounding=ROUND_HALF_UP))
        c.execute("""
            INSERT INTO order_items
              (session_id, table_number, item_name, qty, price, total_price,
               sauce, note, status, "timestamp", created_by_user_id, void_qty, bill_group)
            VALUES
              (%s,%s,%s,%s::NUMERIC(10,1),%s,%s,
               %s,%s,'new',NOW(),%s, 0, %s)
        """, (base["session_id"], base["table_number"], base["item_name"],
              str(desired_unprinted), unit_price, total,
              base["sauce"], base["note"], updated_by_user_id, group_val))
        conn.commit()
        return True, None, {"void_delta": float(void_delta)}

def mark_items_paid(_ignored, session_id, bill_group=None):
    from .splits import normalize_split_meta
    with connect_db() as conn, conn.cursor() as c:
        group = (bill_group or "").strip()

        # If a split is active, treat "main" items as part of the first split.
        main_alias = False
        if group and group.lower() != "main":
            c.execute("SELECT split_labels FROM sessions WHERE id = %s", (session_id,))
            row = c.fetchone()
            raw = row[0] if row else None
            try:
                import json as _json
                parsed = _json.loads(raw) if raw else []
            except Exception:
                parsed = []
            meta = normalize_split_meta(parsed)
            first = meta[0]["key"] if meta else None
            if first and str(first) == group:
                main_alias = True

        if not group or group.lower() == "main":
            c.execute("""
                UPDATE order_items
                   SET status = 'paid'
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = 'main'
            """, (session_id,))
        elif main_alias:
            c.execute("""
                UPDATE order_items
                   SET status = 'paid'
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND (
                     COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
                     OR COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = 'main'
                   )
            """, (session_id, group))
        else:
            c.execute("""
                UPDATE order_items
                   SET status = 'paid'
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group))
        conn.commit()


def session_is_fully_paid(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT COUNT(*)
            FROM order_items
            WHERE session_id=%s
              AND status!='cancelled'
              AND status!='paid'
              AND (COALESCE(qty,0) - COALESCE(void_qty,0)) > 0
        """, (session_id,))
        (remaining,) = c.fetchone()
        return remaining == 0

def get_all_order_items_by_session(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT
                id, item_name, qty, price, total_price,
                sauce, note, status, "timestamp", bill_group,
                COALESCE(void_qty, 0) AS void_qty
            FROM order_items
            WHERE session_id = %s AND status != 'cancelled'
            ORDER BY "timestamp" ASC
        """, (session_id,))
        return c.fetchall()

def get_unpaid_open_items(_ignored, session_id):
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT id, item_name, qty, price, total_price, sauce, note, status, bill_group, "timestamp" AS timestamp
            FROM order_items
            WHERE session_id = %s
              AND status NOT IN ('cancelled','paid')
        """, (session_id,))
        return c.fetchall()

def consolidate_printed_lines(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
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
            c.execute("""
                UPDATE order_items
                   SET qty = %s::NUMERIC(10,1),
                       total_price = %s
                 WHERE id = %s
            """, (str(qty_sum), int(total_sum), keep_id))
            if delete_ids:
                c.execute("DELETE FROM order_items WHERE id = ANY(%s)", (delete_ids,))

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

PRINTED_ST  = ("printed", "served", "paid")
UNPRINTED_ST = ("new", "edited")

def _q(x) -> Decimal:
    return Decimal(str(x or 0)).quantize(Decimal("0.1"))

def build_combined_items_for_session(session_id: str):
    """
    Return one dict per logical line (name+price+sauce+note+group),
    with effective quantities (printed minus void + pending),
    and effective subtotal already computed.
    """
    rows = []
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT
                id, item_name, qty, price, total_price,
                COALESCE(sauce,'') AS sauce,
                COALESCE(note,'')  AS note,
                COALESCE(bill_group,'') AS bill_group,
                COALESCE(void_qty,0) AS void_qty,
                status
            FROM order_items
            WHERE session_id=%s AND status != 'cancelled'
            ORDER BY "timestamp", id
        """, (session_id,))
        rows = c.fetchall()

    # group by logical row
    groups = {}
    for r in rows:
        key = (
            (r["item_name"] or "").strip(),
            int(r["price"] or 0),
            (r["sauce"] or "").strip(),
            (r["note"] or "").strip(),
            (r["bill_group"] or "").strip() or "main",
        )
        g = groups.setdefault(key, {
            "ids": [],
            "item_name": key[0],
            "price": key[1],
            "sauce": key[2],
            "note": key[3],
            "bill_group": key[4],
            "printed_qty": Decimal("0.0"),
            "printed_void": Decimal("0.0"),
            "pending_qty": Decimal("0.0"),
            "any_printed": False,
        })
        g["ids"].append(int(r["id"]))
        q = _q(r["qty"])
        if r["status"] in PRINTED_ST:
            g["printed_qty"]  += q
            g["printed_void"] += _q(r.get("void_qty", 0))
            g["any_printed"]   = True
        elif r["status"] in UNPRINTED_ST:
            g["pending_qty"]  += q
        else:
            # other statuses shouldn't appear due to the WHERE, but just in case
            g["pending_qty"]  += Decimal("0.0")

    combined = []
    for key, g in groups.items():
        unit_price = int(g["price"])
        printed_effective = (g["printed_qty"] - g["printed_void"])
        if printed_effective < 0:
            printed_effective = Decimal("0.0")
        printed_effective = printed_effective.quantize(Decimal("0.1"))

        pending_qty = g["pending_qty"].quantize(Decimal("0.1"))
        qty_effective = (printed_effective + pending_qty).quantize(Decimal("0.1"))

        subtotal = int((qty_effective * Decimal(unit_price)).to_integral_value(rounding=ROUND_HALF_UP))

        # simple print state flags for your CSS
        if printed_effective > 0 and pending_qty > 0:
            print_state = "printed_partial"
        elif printed_effective > 0 and pending_qty == 0:
            print_state = "printed_all"
        else:
            print_state = "new"  # nothing printed yet

        combined.append({
            "ids": g["ids"],
            "item_name": g["item_name"],
            "price": unit_price,

            # expose BOTH the effective qty and the old qty field for compat
            "qty_effective": float(qty_effective),
            "printed_effective": float(printed_effective),
            "pending_qty": float(pending_qty),

            # for legacy code that still reads r.qty → give them the effective number
            "qty": float(qty_effective),

            # server-side effective money
            "subtotal": subtotal,

            "sauce": g["sauce"] or None,
            "note": g["note"] or None,
            "bill_group": g["bill_group"] or "main",

            # render helpers
            "print_state": print_state,
            "wasPrinted": g["any_printed"],
            "hasPending": (pending_qty > 0),
        })

    # keep a stable sort (by name then sauce/note); you can tweak as you like
    combined.sort(key=lambda r: (r["bill_group"], r["item_name"], r.get("sauce") or "", r.get("note") or "", r["price"]))
    return combined
