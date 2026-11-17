from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..authz import roles_required
from ..helpers import qty_half_step
from utils import db
from utils.data.splits import split_meta_labels
from ..events import session_items_changed  
from ..socketbus import _push_state

bp = Blueprint("orders", __name__)

def normalize_group(v: str | None) -> str:
    s = (v or "").strip()
    # treat "", None, "default" as 'main'
    return "main" if not s or s.lower() == "default" else s


@bp.post("/add_order")
@login_required
@roles_required("admin", "cashier", "waiter")
def add_order():
    from decimal import Decimal, ROUND_HALF_UP

    data = request.get_json() or {}
    session_id = data.get("session_id")
    table_number = data.get("table_number")
    items = data.get("items", [])
    uid = current_user.id

    if not session_id or not table_number:
        return jsonify({"status": "error", "message": "Missing session/table"}), 400
    if not isinstance(items, list) or not items:
        return jsonify({"status": "error", "message": "No items provided"}), 400

    # validate & normalize inputs
    split_labels = split_meta_labels(db.get_split_labels(None, session_id) or [])
    default_group = split_labels[0] if split_labels else "main"
    clean = []
    for i, item in enumerate(items):
        if not all(k in item for k in ("item_name", "qty", "price")):
            return jsonify({"status": "error", "message": f"Item {i} missing fields"}), 400
        if not isinstance(item["item_name"], str):
            return jsonify({"status": "error", "message": f"Item {i} item_name must be string"}), 400
        try:
            qd = qty_half_step(item["qty"])  # Decimal or None on bad step
            price = int(item["price"])
        except Exception:
            return jsonify({"status": "error", "message": f"Item {i} qty/price invalid"}), 400
        if qd is None or price < 0:
            return jsonify({"status": "error", "message": f"Item {i} qty must be 0.5 steps"}), 400

        # Carry an optional station hint from client 'cat'/'category' into the stored note
        raw_note = (item.get("note") or "").strip()
        cat_hint = (item.get("cat") or item.get("category") or "").strip().lower()
        station_token = None
        if cat_hint in ("minuman", "minum", "bar"):
            station_token = "bar"
        elif cat_hint in ("makanan", "food", "kitchen"):
            station_token = "kitchen"

        if station_token:
            # prepend a small machine-only token so the printing router can honor explicit choice
            # e.g. '[[station:bar]] rest of note...'
            if raw_note:
                raw_note = f"[[station:{station_token}]] {raw_note}"
            else:
                raw_note = f"[[station:{station_token}]]"

        clean.append({
            "item_name": item["item_name"].strip(),
            "qty": float(qd),
            "price": price,
            "sauce": (item.get("sauce") or "").strip(),
            "note": raw_note,
            "bill_group": (
                default_group
                if normalize_group(item.get("bill_group")) == "main" and split_labels
                else normalize_group(item.get("bill_group"))
            ),
        })

    # Only merge into UNPRINTED items
    UNPRINTED_ST = ("new", "edited")

    try:
        # build lookup from existing UNPRINTED rows
        existing_rows = db.get_all_order_items_by_session(None, session_id)
        existing_map = {}
        for row in existing_rows:
            status = (row[7] or "").lower()
            if status not in UNPRINTED_ST:
                continue
            key = (
                (row[1] or "").strip(),               # item_name
                int(row[3] or 0),                     # price
                (row[5] or "").strip(),               # sauce
                (row[6] or "").strip(),               # note
                normalize_group(row[9] if len(row) > 9 else None),  # bill_group
            )
            existing_map[key] = row

        conn = db.connect_db(None)
        c = conn.cursor()
        try:
            for item in clean:
                key = (
                            item["item_name"],
                            item["price"],
                            item["sauce"],
                            item["note"],
                            normalize_group(item["bill_group"]),
                        )
                if key in existing_map:
                    # merge into UNPRINTED row
                    row        = existing_map[key]
                    item_id    = int(row[0])
                    old_qty    = Decimal(str(row[2] or 0))
                    add_qty    = Decimal(str(item["qty"]))
                    new_qty    = (old_qty + add_qty).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                    unit_price = int(row[3] or 0)
                    new_total  = int((new_qty * Decimal(unit_price)).to_integral_value(rounding=ROUND_HALF_UP))

                    c.execute("""
                        UPDATE order_items
                           SET qty = %s::NUMERIC(10,1),
                               total_price = %s,
                               status = 'edited',
                               updated_by_user_id = %s,
                               updated_at = NOW()
                         WHERE id = %s
                    """, (str(new_qty), new_total, uid, item_id))

                    # keep cache coherent if multiple items in one call
                    updated_row = list(row)
                    updated_row[2] = float(new_qty)
                    updated_row[4] = new_total
                    updated_row[7] = "edited"
                    existing_map[key] = tuple(updated_row)
                else:
                    db.insert_order_item(
                        None, session_id, table_number, item["item_name"], item["qty"], item["price"],
                        sauce=item.get("sauce"),
                        note=item.get("note"),
                        bill_group=normalize_group(item.get("bill_group")),
                        created_by_user_id=uid
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        try:
            session_items_changed(table_number, session_id)
            _push_state(session_id)  
        except Exception:
            current_app.logger.exception("add_order: session_items_changed failed (non-fatal)")


        return jsonify({"status": "success"})
    except Exception:
        current_app.logger.exception("add_order failed")
        return jsonify({"status": "error", "message": "Server error"}), 500


@bp.post("/edit_item")
@login_required
@roles_required("admin", "cashier", "waiter")
def edit_item():
    # Be tolerant if client ever sends bad JSON
    data = request.get_json(silent=True) or {}
    ids = data.get("item_ids") or []
    new_qty_raw = data.get("new_qty")

    # Normalize/validate ids
    try:
        ids = [int(i) for i in ids]
    except Exception:
        return jsonify({"status": "error", "message": "item_ids must be integers"}), 400
    if not ids or new_qty_raw is None:
        return jsonify({"status": "error", "message": "item_ids and new_qty required"}), 400

    qd = qty_half_step(new_qty_raw)
    if qd is None or qd < 0:
        return jsonify({"status": "error", "message": "new_qty must be 0 or 0.5 steps"}), 400

    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        # derive session & table for realtime emit (from the first id)
        c.execute("SELECT session_id, table_number FROM order_items WHERE id=%s", (ids[0],))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "item not found"}), 404
        session_id, table_number = row

        void_total = 0.0

        for oid in ids:
            try:
                ok, err, result = db.update_order_item_qty(
                    None, oid, float(qd), updated_by_user_id=current_user.id
                )
            except Exception:
                current_app.logger.exception("edit_item: helper crashed for oid=%s", oid)
                conn.rollback(); conn.close()
                return jsonify({"status": "error", "message": "internal error"}), 500

            if not ok:
                conn.rollback(); conn.close()
                return jsonify({"status": "error", "message": err or "failed to update"}), 400

            if result and isinstance(result, dict):
                try:
                    void_total += float(result.get("void_delta") or 0.0)
                except Exception:
                    pass

            # If new qty is 0, also mark the row as cancelled
            if float(qd) == 0.0:
                try:
                    c.execute("""
                        UPDATE order_items
                           SET status='cancelled',
                               updated_at=now()
                         WHERE id=%s
                    """, (oid,))
                except Exception:
                    current_app.logger.exception("edit_item: failed to set status=cancelled for oid=%s", oid)
                    conn.rollback(); conn.close()
                    return jsonify({"status": "error", "message": "internal error"}), 500

        # --- NEW: propagate bill_group of the edited rows to any NULL/'' siblings created by the helper ---
        # 1) Read the "source" signature(s) and their bill_group
        c.execute("""
            SELECT DISTINCT
                   COALESCE(NULLIF(TRIM(bill_group), ''), 'main') AS grp,
                   item_name,
                   price,
                   COALESCE(sauce,'') AS sauce,
                   COALESCE(note,'')  AS note
            FROM order_items
            WHERE id = ANY(%s)
        """, (ids,))
        signatures = c.fetchall() or []

        # 2) For each signature, set bill_group on rows in the SAME session
        #    that match the same name/price/sauce/note but have empty bill_group
        for grp, item_name, price, sauce, note in signatures:
            c.execute("""
                UPDATE order_items
                   SET bill_group = %s
                 WHERE session_id = %s
                   AND item_name  = %s
                   AND price      = %s
                   AND COALESCE(sauce,'') = %s
                   AND COALESCE(note,'')  = %s
                   AND (bill_group IS NULL OR TRIM(bill_group) = '')
            """, (grp or 'main', session_id, item_name, int(price), sauce, note))

        # (Optional hardening) also normalize any fully empty bill_group in this session to 'main'
        # c.execute("""
        #     UPDATE order_items
        #        SET bill_group = 'main'
        #      WHERE session_id = %s AND (bill_group IS NULL OR TRIM(bill_group) = '')
        # """, (session_id,))

        conn.commit()

    except Exception:
        current_app.logger.exception("edit_item: unexpected failure")
        try: conn.rollback()
        except Exception: pass
        return jsonify({"status": "error", "message": "internal error"}), 500
    finally:
        try: conn.close()
        except Exception: pass

    # Realtime notify — don't fail the request if it throws
    try:
        session_items_changed(table_number, session_id)
        _push_state(session_id)
    except Exception:
        current_app.logger.exception("edit_item: session_items_changed failed")

    return jsonify({"status": "success", "void_qty": round(void_total, 1)})



@bp.post("/edit_item_note")
@login_required
@roles_required("admin", "cashier", "waiter")
def edit_item_note():
    """Replace note for a set of items. If an item was printed, mark it 'edited' so it will reprint on next send."""
    data = request.get_json() or {}
    ids = data.get("item_ids") or []
    note = (data.get("note") or "").strip()

    if not ids:
        return jsonify({"status": "error", "message": "item_ids required"}), 400

    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        c.execute("SELECT session_id, table_number FROM order_items WHERE id=%s", (ids[0],))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "item not found"}), 404
        session_id, table_number = row

        # Update note; if row was printed, flip status to 'edited' so get_printables() will include it
        for oid in ids:
            c.execute("""
                UPDATE order_items
                SET note=%s,
                    updated_at=now(),
                    status=CASE WHEN status IN ('printed','paid') THEN 'edited' ELSE status END
                WHERE id=%s
            """, (note, oid))

        conn.commit()
    finally:
        conn.close()

    try:
        session_items_changed(table_number, session_id)
        _push_state(session_id)
    except Exception:
        pass

    return jsonify({"status": "success"})
