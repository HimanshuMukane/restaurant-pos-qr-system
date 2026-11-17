from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..authz import roles_required
from utils import db
from utils.data.splits import normalize_split_meta, split_meta_labels, split_meta_map
from ..events import session_items_changed
from ..socketbus import _push_state
from datetime import datetime
import uuid
import json

bp = Blueprint("split", __name__, url_prefix="/split")

# -----------------------------
# Set bill group on one/many items
# -----------------------------
@bp.post("/set_bill_group")
@login_required
@roles_required("admin", "cashier", "waiter")
def set_bill_group():
    data = request.get_json(silent=True) or {}
    item_id  = data.get("item_id")
    item_ids = data.get("item_ids")
    group_in = data.get("group")
    bill_group = db.normalize_group(group_in)

    if item_id is None and item_ids is None:
        return jsonify({"status": "error", "message": "missing item_id or item_ids"}), 400

    try:
        target_session_id = None
        if item_ids:
            ids = [int(x) for x in item_ids]
            # find session_id from one id
            with db.connect_db(None) as conn, conn.cursor() as c:
                c.execute("SELECT session_id FROM order_items WHERE id=%s", (ids[0],))
                row = c.fetchone()
                if row: target_session_id = row[0]

            db.set_items_bill_group(None, ids, bill_group, current_user.id)
        else:
            oid = int(item_id)
            with db.connect_db(None) as conn, conn.cursor() as c:
                c.execute("SELECT session_id FROM order_items WHERE id=%s", (oid,))
                row = c.fetchone()
                if row: target_session_id = row[0]

            db.set_item_bill_group(None, oid, bill_group, current_user.id)

        if target_session_id:
            _push_state(str(target_session_id))

        return jsonify({"status": "success"})
    except Exception as e:
        current_app.logger.exception("set_bill_group failed")
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------
# Configure split labels (1..N)
# -----------------------------
@bp.post("/config/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def set_split_config(session_id):
    data = request.get_json(silent=True) or {}
    try:
        count = int(data.get("count") or 0)
    except Exception:
        count = 0

    if count <= 0 or count > 20:
        return jsonify({"status": "error", "message": "count must be 1..20"}), 400

    existing_raw = db.get_split_labels(None, session_id) or []
    existing_names = split_meta_map(existing_raw)
    labels = [str(i + 1) for i in range(count)]
    meta = [{"key": k, "name": existing_names.get(k, "")} for k in labels]
    try:
        db.set_split_labels(None, session_id, meta)
        # When splits are enabled, remove "main" by pushing ungrouped items to Split 1
        if labels:
            with db.connect_db(None) as conn, conn.cursor() as c:
                c.execute("""
                    UPDATE order_items
                       SET bill_group = %s, updated_by_user_id = %s
                     WHERE session_id = %s
                       AND (bill_group IS NULL OR TRIM(bill_group) = '' OR LOWER(TRIM(bill_group)) = 'main')
                """, (labels[0], current_user.id, session_id))
                conn.commit()
        _push_state(session_id)
        return jsonify({"status": "success", "labels": labels, "meta": meta})
    except Exception as e:
        current_app.logger.exception("set_split_config failed")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.delete("/config/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def clear_split_config(session_id):
    try:
        db.clear_split_labels(None, session_id)
        _push_state(session_id)
        return jsonify({"status": "success"})
    except Exception as e:
        current_app.logger.exception("clear_split_config failed")
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------
# Move qty from selected items into a destination group
# -----------------------------
@bp.post("/move")
@login_required
@roles_required("admin", "cashier", "waiter")
def split_move():
    data = request.get_json(silent=True) or {}
    session_id  = data.get("session_id")
    to_group_in = data.get("to_group")
    qty         = data.get("qty")
    source_ids  = data.get("source_ids") or []

    if not session_id:
        return jsonify(status="error", message="missing session_id"), 400
    try:
        move_qty = float(qty or 0)
    except Exception:
        move_qty = 0.0
    if move_qty <= 0:
        return jsonify(status="error", message="qty must be > 0"), 400
    if round(move_qty * 2) != move_qty * 2:
        return jsonify(status="error", message="qty must be in 0.5 steps"), 400
    try:
        source_ids = [int(x) for x in source_ids]
    except Exception:
        return jsonify(status="error", message="invalid source_ids"), 400
    if not source_ids:
        return jsonify(status="error", message="missing source_ids"), 400

    dest_group = db.normalize_group(to_group_in)  # '1','2',... or None (=main)

    try:
        # If a destination (non-main) is provided, validate it exists in split labels
        if dest_group is not None:
            raw_labels = db.get_split_labels(None, session_id) or []
            labels = split_meta_labels(raw_labels)
            if dest_group not in labels:
                return jsonify(status="error", message="invalid destination group"), 400

        with db.connect_db(None) as conn, conn.cursor() as c:
            placeholders = ",".join(["%s"] * len(source_ids))
            c.execute(f"""
                SELECT id, qty, bill_group, table_number
                  FROM order_items
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND id IN ({placeholders})
                 FOR UPDATE
            """, [session_id, *source_ids])
            rows = c.fetchall()

            if not rows:
                return jsonify(status="error", message="no matching items"), 404

            # Also capture table_number for realtime broadcast
            table_number = None
            total_available = 0.0
            for _id, q, _bg, tn in rows:
                total_available += float(q or 0)
                if table_number is None:
                    table_number = tn

            if move_qty - total_available > 1e-9:
                return jsonify(status="error", message="not enough quantity in selected items"), 400

            remaining = move_qty
            for rid, row_qty, _bg, _tn in rows:
                if remaining <= 1e-9:
                    break
                row_qty = float(row_qty or 0)
                take = min(row_qty, remaining)

                if take >= (row_qty - 1e-6):
                    # full move → just reassign group
                    c.execute("""
                        UPDATE order_items
                           SET bill_group = %s,
                               updated_by_user_id = %s
                         WHERE id = %s
                    """, (dest_group, current_user.id, rid))
                else:
                    # partial move → clone 'take' to dest row, reduce current row
                    # Insert clone with qty=take and recomputed total_price
                    c.execute("""
                        INSERT INTO order_items (
                            session_id, table_number, item_name,
                            qty, price, total_price,
                            sauce, note, status,
                            created_by_user_id, updated_by_user_id, bill_group
                        )
                        SELECT
                            session_id, table_number, item_name,
                            %s, price,
                            ROUND(%s * price)::int,
                            sauce, note, status,
                            %s, %s, %s
                          FROM order_items
                         WHERE id = %s
                    """, (take, take, current_user.id, current_user.id, dest_group, rid))

                    # Reduce source row qty & total_price
                    c.execute("""
                        UPDATE order_items
                           SET qty = qty - %s,
                               total_price = ROUND((qty - %s) * price)::int,
                               updated_by_user_id = %s
                         WHERE id = %s
                    """, (take, take, current_user.id, rid))
                    c.execute("""
                        DELETE FROM order_items
                         WHERE id = %s AND qty <= 0
                    """, (rid,))

                remaining -= take

            conn.commit()

        # Realtime notify dashboards/session views
        try:
            if table_number is None:
                # Fallback fetch if not present
                sess_min = db.get_session_by_id(None, session_id)
                if sess_min:
                    _sid, table_number, _ = sess_min
            if table_number:
                session_items_changed(table_number, session_id)
                _push_state(session_id)
        except Exception:
            pass

        return jsonify(status="ok")
    except Exception as e:
        current_app.logger.exception("split_move failed")
        return jsonify(status="error", message=str(e)), 500


# -----------------------------
# Move a whole split group to another table (as main)
# -----------------------------
@bp.post("/move_group_to_table")
@login_required
@roles_required("admin", "cashier", "waiter")
def move_group_to_table():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    group_in = data.get("group")
    to_table = (data.get("to_table") or "").strip()

    if not session_id or not to_table:
        return jsonify(status="error", message="session_id dan to_table wajib"), 400

    group_key = db.normalize_group(group_in)
    if not group_key:
        return jsonify(status="error", message="group tidak valid"), 400

    sess = db.get_session_by_id(None, session_id)
    if not sess:
        return jsonify(status="error", message="Sesi tidak ditemukan"), 404
    _sid, source_table, status = sess
    if status != "active":
        return jsonify(status="error", message="Sesi tidak aktif"), 409
    if to_table == source_table:
        return jsonify(status="error", message="Tujuan tidak boleh meja yang sama"), 400

    tables = db.load_tables()
    valid_tables = {t["number"] for t in tables}
    if to_table not in valid_tables:
        return jsonify(status="error", message="Nomor meja tidak dikenal"), 400

    raw_labels = db.get_split_labels(None, session_id) or []
    labels = split_meta_labels(raw_labels)
    if labels and group_key not in labels:
        return jsonify(status="error", message="Group tidak ditemukan"), 400

    group_name_map = split_meta_map(raw_labels)
    group_name = group_name_map.get(group_key, "")
    group_sql = group_key or "main"

    created_new = False
    target_session_id = None

    try:
        with db.connect_db(None) as conn, conn.cursor() as c:
            # target session by table (active, dine_in)
            c.execute("""
                SELECT id FROM sessions
                WHERE table_number = %s
                  AND status = 'active'
                  AND COALESCE(service_type, 'dine_in') <> 'takeaway'
                ORDER BY created_at DESC
                LIMIT 1
            """, (to_table,))
            row = c.fetchone()
            target_session_id = row[0] if row else None

            if target_session_id == session_id:
                return jsonify(status="error", message="Tujuan tidak boleh meja yang sama"), 400

            # Source group must exist
            c.execute("""
                SELECT COUNT(*)
                  FROM order_items
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group_sql))
            if (c.fetchone()[0] or 0) == 0:
                return jsonify(status="error", message="Tidak ada item di group ini"), 400

            # Source group must be unpaid (no paid items / payments)
            c.execute("""
                SELECT COUNT(*)
                  FROM order_items
                 WHERE session_id = %s
                   AND status = 'paid'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group_sql))
            if (c.fetchone()[0] or 0) > 0:
                return jsonify(status="error", message="Group ini sudah ada item dibayar"), 400

            c.execute("""
                SELECT COUNT(*)
                  FROM payments
                 WHERE session_id = %s
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group_sql))
            if (c.fetchone()[0] or 0) > 0:
                return jsonify(status="error", message="Group ini sudah ada pembayaran"), 400

            if target_session_id:
                # Target session is active; payments are allowed (will create a new split)
                pass
            else:
                # Create new session on empty table
                created_new = True
                target_session_id = str(uuid.uuid4())
                now_iso = datetime.now().isoformat()
                guest_name = group_name or f"Split {group_key}"
                note = f"Pindah dari meja {source_table}"
                c.execute("""
                    INSERT INTO sessions
                        (id, pax, table_number, created_at, guest_name,
                         dp_amount, note, status, opened_by_user_id)
                    VALUES
                        (%s, 1, %s, %s, %s,
                         0, %s, 'active', %s)
                """, (target_session_id, to_table, now_iso, guest_name, note, current_user.id))

            now_iso = datetime.now().isoformat()

            # If target has active session, ensure a NEW split group exists and use it
            dest_group = None
            if not created_new:
                c.execute("SELECT split_labels FROM sessions WHERE id=%s", (target_session_id,))
                row = c.fetchone()
                tgt_raw = row[0] if row else None
                try:
                    tgt_parsed = json.loads(tgt_raw) if tgt_raw else []
                except Exception:
                    tgt_parsed = []
                tgt_meta = normalize_split_meta(tgt_parsed)

                c.execute("""
                    SELECT DISTINCT COALESCE(NULLIF(TRIM(bill_group), ''), 'main')
                      FROM order_items
                     WHERE session_id = %s
                       AND status != 'cancelled'
                """, (target_session_id,))
                used_keys = set(m.get("key") for m in tgt_meta if m.get("key"))
                for (bg,) in c.fetchall() or []:
                    if bg and str(bg).isdigit():
                        used_keys.add(str(int(bg)))

                max_key = max((int(k) for k in used_keys if str(k).isdigit()), default=0)
                next_key = str(max_key + 1)
                if not tgt_meta:
                    base_key = "1"
                    if next_key == base_key:
                        next_key = "2"
                    tgt_meta = [{"key": base_key, "name": ""}, {"key": next_key, "name": "baru"}]
                    c.execute(
                        "UPDATE sessions SET split_labels = %s WHERE id = %s",
                        (json.dumps(tgt_meta), target_session_id),
                    )
                    # Move target MAIN items into split 1 to keep split board consistent
                    c.execute("""
                        UPDATE order_items
                           SET bill_group = %s,
                               updated_by_user_id = %s,
                               "timestamp" = %s
                         WHERE session_id = %s
                           AND status != 'cancelled'
                           AND (bill_group IS NULL OR TRIM(bill_group) = '' OR LOWER(TRIM(bill_group)) = 'main')
                    """, (base_key, current_user.id, now_iso, target_session_id))
                else:
                    tgt_meta.append({"key": next_key, "name": "baru"})
                    tgt_meta = sorted(tgt_meta, key=lambda x: int(x["key"]))
                    c.execute(
                        "UPDATE sessions SET split_labels = %s WHERE id = %s",
                        (json.dumps(tgt_meta), target_session_id),
                    )

                dest_group = next_key

            # Move items to target (as MAIN for new session, or as NEW split for active target)
            c.execute("""
                UPDATE order_items
                   SET session_id = %s,
                       table_number = %s,
                       bill_group = %s,
                       updated_by_user_id = %s,
                       "timestamp" = %s
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (target_session_id, to_table, dest_group, current_user.id, now_iso, session_id, group_sql))

            if (c.rowcount or 0) == 0:
                conn.rollback()
                return jsonify(status="error", message="Gagal memindahkan item"), 400

            # Remove split label if group now empty
            c.execute("""
                SELECT COUNT(*)
                  FROM order_items
                 WHERE session_id = %s
                   AND status != 'cancelled'
                   AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') = %s
            """, (session_id, group_sql))
            remaining = (c.fetchone()[0] or 0)
            if remaining == 0:
                meta = normalize_split_meta(raw_labels)
                meta = [m for m in meta if m.get("key") != group_key]
                if meta:
                    c.execute(
                        "UPDATE sessions SET split_labels = %s WHERE id = %s",
                        (json.dumps(meta), session_id),
                    )
                else:
                    # Only clear if no other non-main groups remain
                    c.execute("""
                        SELECT COUNT(*)
                          FROM order_items
                         WHERE session_id = %s
                           AND status != 'cancelled'
                           AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main') != 'main'
                    """, (session_id,))
                    if (c.fetchone()[0] or 0) == 0:
                        c.execute("UPDATE sessions SET split_labels = NULL WHERE id = %s", (session_id,))

            conn.commit()

    except Exception as e:
        current_app.logger.exception("move_group_to_table failed")
        return jsonify(status="error", message=str(e)), 500

    # Realtime update
    try:
        session_items_changed(source_table, session_id)
        _push_state(session_id)
        session_items_changed(to_table, target_session_id)
        _push_state(target_session_id)
        if created_new:
            from ..events import session_created
            session_created(to_table, target_session_id, pax=1, guest_name=(group_name or f"Split {group_key}"))
    except Exception:
        pass

    return jsonify(
        status="success",
        redirect=f"/table/{to_table}/{target_session_id}",
        created_new=created_new,
    )


# -----------------------------
# Rename split labels (meta)
# -----------------------------
@bp.post("/meta/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def set_split_meta(session_id):
    data = request.get_json(silent=True) or {}
    raw_labels = db.get_split_labels(None, session_id) or []
    meta = normalize_split_meta(raw_labels)
    if not meta:
        return jsonify({"status": "error", "message": "no split config"}), 400

    updates = {}
    if isinstance(data.get("labels"), list):
        for entry in data.get("labels") or []:
            if not isinstance(entry, dict):
                continue
            key = str(entry.get("key") or "").strip()
            if not key:
                continue
            updates[key] = str(entry.get("name") or "").strip()
    else:
        key = str(data.get("key") or "").strip()
        if key:
            updates[key] = str(data.get("name") or "").strip()

    if not updates:
        return jsonify({"status": "error", "message": "no updates"}), 400

    for m in meta:
        if m["key"] in updates:
            m["name"] = updates[m["key"]]

    try:
        db.set_split_labels(None, session_id, meta)
        _push_state(session_id)
        return jsonify({"status": "ok", "labels": split_meta_labels(meta), "meta": meta})
    except Exception as e:
        current_app.logger.exception("set_split_meta failed")
        return jsonify({"status": "error", "message": str(e)}), 500
