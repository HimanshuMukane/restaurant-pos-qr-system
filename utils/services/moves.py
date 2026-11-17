import json
from datetime import datetime
from psycopg.rows import dict_row
from ..data.core import connect_db
from ..data.splits import normalize_split_meta

def move_session_table(_ignored, session_id, to_table, by_user_id=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            SELECT id FROM sessions
            WHERE table_number = %s AND status = 'active'
            LIMIT 1
        """, (to_table,))
        row = c.fetchone()
        if row:
            raise RuntimeError("Target table became occupied")

        c.execute("""
            UPDATE sessions
            SET table_number = %s
            WHERE id = %s AND status = 'active'
        """, (to_table, session_id))

        if c.rowcount == 0:
            raise RuntimeError("session not active")

        c.execute("""
            UPDATE order_items
            SET table_number = %s
            WHERE session_id = %s
        """, (to_table, session_id))

def merge_sessions(_ignored, source_session_id, target_session_id, by_user_id=None):
    now_iso = datetime.now().isoformat()
    with connect_db() as conn:
        with conn.cursor(row_factory=dict_row) as c:
            try:
                c.execute("SELECT id, table_number, status, dp_amount, dp_method, split_labels FROM sessions WHERE id = %s", (source_session_id,))
                src = c.fetchone()
                c.execute("SELECT id, table_number, status, dp_amount, dp_method, split_labels FROM sessions WHERE id = %s", (target_session_id,))
                tgt = c.fetchone()
                if not src or not tgt:
                    raise ValueError("Session tidak ditemukan")
                if (src["status"] != "active") or (tgt["status"] != "active"):
                    raise ValueError("Hanya bisa merge antara sesi yang masih aktif")

                def _has_non_dp_payments(cur, sess_id, dp_amount, dp_method):
                    cur.execute(
                        """
                        SELECT COALESCE(is_dp, FALSE) AS is_dp,
                               COALESCE(is_refund, FALSE) AS is_refund,
                               COALESCE(amount, 0) AS amount,
                               COALESCE(dp_applied_amount, 0) AS dp_applied_amount,
                               COALESCE(method, '') AS method
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

                    non_dp_rows = [r for r in non_ref if not r["is_dp"]]
                    if not non_dp_rows:
                        return False

                    dp_method = (dp_method or "").strip() or None

                    if dp_amount and all(int(r["dp_applied_amount"] or 0) == 0 for r in non_dp_rows):
                        total = sum(int(r["amount"] or 0) for r in non_dp_rows)
                        if dp_method:
                            if all(str(r["method"] or "").strip() == dp_method for r in non_dp_rows) and total == int(dp_amount):
                                return False
                        else:
                            if total == int(dp_amount):
                                return False

                    return any(int(r["amount"] or 0) > 0 for r in non_dp_rows)

                if _has_non_dp_payments(c, source_session_id, src["dp_amount"] or 0, src.get("dp_method")):
                    raise ValueError("Sesi sumber sudah memiliki pembayaran — selesaikan/void dulu sebelum merge")

                c.execute("SELECT COUNT(*) AS n FROM order_items WHERE session_id = %s AND status = 'paid'", (source_session_id,))
                if (c.fetchone()["n"] or 0) > 0:
                    raise ValueError("Ada item yang sudah dibayar di sesi sumber — tidak bisa merge")

                c.execute("""
                    SELECT id, item_name, qty, price, total_price, sauce, note, bill_group
                    FROM order_items
                    WHERE session_id = %s
                      AND status NOT IN ('cancelled','paid')
                """, (source_session_id,))
                src_items = c.fetchall()

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

                # --- If any split exists, remap SOURCE groups to avoid collisions ---
                def _norm_group_key(raw):
                    s = str(raw or "").strip()
                    if s == "" or s.lower() == "main":
                        return "main"
                    if s.isdigit():
                        return str(int(s))
                    return None

                remap = {}
                remapped_src_meta = list(src_meta)
                split_active = bool(src_meta or tgt_meta)
                if split_active:
                    tgt_keys = {m["key"] for m in tgt_meta if m.get("key")}
                    c.execute("""
                        SELECT DISTINCT bill_group
                        FROM order_items
                        WHERE session_id = %s
                          AND status NOT IN ('cancelled','paid')
                    """, (target_session_id,))
                    for (bg,) in c.fetchall() or []:
                        g = _norm_group_key(bg)
                        if g and g != "main":
                            tgt_keys.add(g)

                    max_key = max((int(k) for k in tgt_keys if str(k).isdigit()), default=0)
                    start = max_key + 1
                    if start < 10:
                        start = 10

                    src_groups = []
                    for m in src_meta:
                        k = _norm_group_key(m.get("key"))
                        if k and k not in src_groups:
                            src_groups.append(k)
                    for r in src_items:
                        k = _norm_group_key(r.get("bill_group"))
                        if k and k not in src_groups:
                            src_groups.append(k)

                    for g in src_groups:
                        remap[g] = str(start)
                        start += 1

                    remapped_src_meta = []
                    for m in src_meta:
                        old_key = _norm_group_key(m.get("key"))
                        new_key = remap.get(old_key)
                        if not new_key:
                            continue
                        remapped_src_meta.append({"key": new_key, "name": m.get("name") or ""})

                    if remap.get("main") and not any(x["key"] == remap["main"] for x in remapped_src_meta):
                        remapped_src_meta.append({"key": remap["main"], "name": ""})

                for r in src_items:
                    name  = r["item_name"]; price = r["price"]; sauce = r["sauce"]; note  = r["note"]; grp   = r["bill_group"]
                    if remap:
                        g_norm = _norm_group_key(grp)
                        if g_norm in remap:
                            grp = remap[g_norm]
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
                            SET session_id = %s, updated_by_user_id = %s, "timestamp" = %s, bill_group = %s
                            WHERE id = %s
                        """, (target_session_id, by_user_id, now_iso, grp, r["id"]))

                src_dp = src["dp_amount"] or 0
                tgt_dp = tgt["dp_amount"] or 0
                if src_dp:
                    c.execute("UPDATE sessions SET dp_amount = %s WHERE id = %s", (src_dp + tgt_dp, target_session_id))
                    c.execute("UPDATE sessions SET dp_amount = 0 WHERE id = %s", (source_session_id,))

                merged = {}
                for m in tgt_meta:
                    merged[m["key"]] = {"key": m["key"], "name": m.get("name") or ""}
                for m in remapped_src_meta:
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

                c.execute("""
                    UPDATE sessions
                    SET status='moved', closed_at=%s, closed_by_user_id=%s
                    WHERE id=%s
                """, (now_iso, by_user_id, source_session_id))

            except Exception as e:
                conn.rollback()
                return False, str(e)
        return True, {"target_table": tgt["table_number"]}
