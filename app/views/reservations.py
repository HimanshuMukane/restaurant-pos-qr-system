from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from ..authz import roles_required
from utils import db
from psycopg.rows import dict_row
from app.socketbus import (
    push_reservation_changed,
    push_reservation_changed_deferred,
    push_reservation_autoseated,
    push_session_created,
    broadcast,
)
from utils.services import reservations as svc_res
from utils.data import reservations as data_res
from utils.data.core import connect_db
from utils.data.splits import normalize_split_meta
from datetime import datetime
import re

bp = Blueprint("reservations", __name__)

# reservations.py
@bp.post("/add_reservation")
@login_required
@roles_required("admin", "cashier")
def add_reservation():
    try:
        uid = current_user.id
        data = request.get_json() or {}

        dp_amount = int(data.get("dp_amount") or 0)
        dp_method = (data.get("dp_method") or "").strip() or None

        if dp_amount <= 0:
            return jsonify({"status": "error", "message": "DP wajib > 0"}), 400
        if not dp_method:
            return jsonify({"status": "error", "message": "Metode DP wajib diisi"}), 400

        rid = db.insert_reservation(
            None,
            guest_name=data["guest_name"],
            phone=data.get("phone"),
            pax=int(data["pax"]),
            date=data["date"],
            time=data["time"],
            notes=data.get("notes", ""),
            dp_amount=dp_amount,
            dp_method=dp_method,
            created_by_user_id=uid
        )

        # Create (or reuse) the virtual session on table "RES:<rid>"
        sid = svc_res.ensure_reservation_session(None, rid, opened_by_user_id=uid)

        try:
            with connect_db() as conn, conn.cursor() as c:
                # set dp_amount, dp_method, dp_paid_at on the session
                c.execute(
                    """
                    UPDATE public.sessions
                       SET dp_amount = COALESCE(dp_amount, %s),
                           dp_method = %s,
                           dp_paid_at = COALESCE(dp_paid_at, NOW())
                     WHERE id = %s
                    """,
                    (dp_amount, dp_method, sid),
                )

                # create DP payment row if not already present
                c.execute(
                    """
                    INSERT INTO public.payments
                        (session_id, amount, method, paid_at,
                         cash_received, change_given,
                         discount_percent, discount_amount,
                         tax, service, total_before_discount,
                         card_type, created_by_user_id, bill_group,
                         dp_applied_amount, is_refund, refund_of,
                         refund_reason, refunded_by_user_id, is_dp)
                    SELECT
                        %s, %s, %s, NOW(),
                        NULL, 0,
                        0, 0,
                        0, 0, %s,
                        NULL, %s, NULL,
                        0, FALSE, NULL,
                        NULL, NULL, TRUE
                    WHERE NOT EXISTS (
                        SELECT 1 FROM public.payments p
                         WHERE p.session_id = %s AND p.is_dp = TRUE
                    )
                    """,
                    (
                        sid,
                        dp_amount,
                        dp_method,
                        dp_amount,
                        uid,
                        sid,
                    ),
                )

                conn.commit()
        except Exception:
            current_app.logger.exception(
                "add_reservation: failed to sync DP or insert DP payment for session %s",
                sid,
            )



        pseudo_table = svc_res.reservation_table_number(rid)
        from flask import url_for
        return jsonify({
            "status": "success",
            "reservation_id": rid,
            "session_id": sid,
            "table_number": pseudo_table,
            "redirect": url_for("sessions.view_session", table_number=pseudo_table, session_id=sid)
        })
    except Exception as e:
        current_app.logger.exception("add_reservation failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.post("/api/reservations/create_with_table")
@login_required
@roles_required("admin", "cashier", "waiter")
def create_reservation_with_table():
    data = request.get_json(silent=True) or {}
    wants_json = bool(request.is_json)
    if not data:
        data = request.form.to_dict()
        wants_json = False

    guest_name = (data.get("guest_name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    table_number = (data.get("table_number") or "").strip()
    date = (data.get("date") or "").strip()
    time_ = (data.get("time") or "").strip()
    if not time_:
        hh = (data.get("hour") or "").strip()
        mm = (data.get("minute") or "").strip()
        if hh and mm:
            time_ = f"{hh}:{mm}"

    def err(msg, code=400):
        if wants_json:
            return jsonify({"status": "error", "message": msg}), code
        flash(msg, "error")
        return redirect(url_for("reservations.reservations_lookup"))

    try:
        pax = max(int(data.get("pax") or 1), 1)
    except Exception:
        return err("PAX tidak valid.")

    try:
        dp_amount = int(data.get("dp_amount") or 0)
    except Exception:
        return err("DP tidak valid.")
    dp_method = (data.get("dp_method") or "").strip() or None

    if not guest_name:
        return err("Nama tamu wajib diisi.")
    if not table_number:
        return err("Nomor meja wajib diisi.")
    if not date or not time_:
        return err("Tanggal & jam reservasi wajib diisi.")
    # Accept HH:MM or HH:MM:SS and normalize to HH:MM
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date) or not re.match(r"^\d{2}:\d{2}(:\d{2})?$", time_):
        return err("Format tanggal/jam tidak valid.")
    if len(time_) >= 5:
        time_ = time_[:5]
    if dp_amount <= 0:
        return err("DP wajib diisi (> 0).")
    if not dp_method:
        return err("Metode DP wajib diisi.")

    tables = db.load_tables()
    valid_tables = {t["number"] for t in tables}
    if table_number not in valid_tables:
        return err("Nomor meja tidak dikenal.")

    try:
        rid = data_res.create_reservation_with_table(
            None,
            table_number=table_number,
            guest_name=guest_name,
            phone=phone,
            pax=pax,
            date=date,
            time=time_,
            notes=notes,
            dp_amount=dp_amount,
            dp_method=dp_method,
            created_by_user_id=current_user.id,
            status="confirmed",
        )
    except Exception:
        current_app.logger.exception("create_reservation_with_table failed")
        return err("Gagal membuat reservasi.", 500)

    ts_iso = svc_res._make_ts_iso(date, time_)
    push_reservation_changed_deferred(table_number, ts_iso)

    if wants_json:
        return jsonify({"status": "success", "reservation_id": rid})
    flash("Reservasi dibuat.", "success")
    return redirect(url_for("reservations.reservations_lookup"))

@bp.post("/api/reservations/<int:res_id>/ensure_session")
@login_required
@roles_required("admin","cashier","waiter")
def api_res_ensure_session(res_id):
    try:
        sid = svc_res.ensure_reservation_session(None, res_id, opened_by_user_id=current_user.id)
        pseudo_table = svc_res.reservation_table_number(res_id)
        from flask import url_for
        return jsonify({
            "status": "ok",
            "reservation_id": res_id,
            "session_id": sid,
            "table_number": pseudo_table,
            "redirect": url_for("sessions.view_session", table_number=pseudo_table, session_id=sid),
        })
    except Exception as e:
        current_app.logger.exception("ensure_session failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.get("/api/reservations/<int:res_id>")
@login_required
@roles_required("admin","cashier","waiter","viewer")
def api_get_reservation(res_id):
    from psycopg.rows import dict_row
    from utils.db import connect_db
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("""
            SELECT id, guest_name, phone, pax, date, time, notes,
                   COALESCE(dp_amount,0) AS dp_amount,
                   COALESCE(dp_method,'transfer') AS dp_method,
                   COALESCE(table_number,'') AS table_number,
                   COALESCE(status,'pending') AS status
            FROM public.reservations WHERE id=%s
        """, (res_id,))
        row = c.fetchone()
    if not row:
        return jsonify({"status":"not_found"}), 404

    item = dict(row)
    # coerce to JSON-friendly strings
    d = item.get("date")
    t = item.get("time")
    if d is not None:
        try: item["date"] = d.strftime("%Y-%m-%d")
        except Exception: item["date"] = str(d)
    if t is not None:
        try: item["time"] = t.strftime("%H:%M")
        except Exception: item["time"] = str(t)

    # ints/strings are already JSON-safe
    item["dp_amount"] = int(item.get("dp_amount") or 0)
    return jsonify({"status":"ok","item":item})

@bp.post("/api/reservations/<int:res_id>/cancel")
@login_required
@roles_required("admin","cashier","waiter")
def api_cancel_reservation(res_id):
    data = request.get_json(silent=True) or {}
    table_number = (data.get("table_number") or "").strip()

    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        if not table_number:
            c.execute("SELECT table_number FROM reservations WHERE id=%s", (res_id,))
            r = c.fetchone()
            if not r:
                return jsonify({"status":"not_found"}), 404
            table_number = str(r["table_number"])

        c.execute("UPDATE public.reservations SET status='cancelled' WHERE id=%s", (res_id,))
        if c.rowcount == 0:
            return jsonify({"status":"not_found"}), 404

    # Clear pink immediately
    push_reservation_changed(table_number, None)
    return jsonify({"status":"success"})


@bp.get("/api/reservations/<int:res_id>/preorder")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_list_preorder(res_id):
    items = db.list_reservation_items(None, res_id)
    return jsonify({"items": items})

@bp.post("/api/reservations/<int:res_id>/preorder")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_add_preorder(res_id):
    b = request.get_json() or {}
    try:
        db.add_reservation_item(None, res_id, item_name=b["item_name"], qty=int(b["qty"]), price=int(b["price"]), sauce=b.get("sauce"), note=b.get("note"), user_id=current_user.id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@bp.delete("/api/reservations/preorder/<int:item_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_del_preorder(item_id):
    try:
        db.delete_reservation_item(None, item_id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@bp.post("/assign_table")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def assign_table():
    data = request.get_json() or {}
    res_id = data.get("id")
    table_number = data.get("table_number")
    if not res_id or not table_number:
        return jsonify({"status": "error", "message": "ID dan nomor meja wajib diisi"}), 400
    conn = db.connect_db(None)
    c = conn.cursor()
    uid = current_user.id
    c.execute("UPDATE reservations SET table_number = %s, status = 'confirmed', confirmed_by_user_id=%s WHERE id = %s", (table_number, uid, res_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@bp.patch("/api/reservations/<int:res_id>")
@login_required
@roles_required("admin","cashier","waiter")
def api_update_reservation(res_id):
    b = request.get_json() or {}
    if not b.get("dp_method"):
        b["dp_method"] = "transfer"

    # 1) Update with your existing helper
    try:
        db.update_reservation(None, res_id,
            guest_name=b.get("guest_name"),
            phone=b.get("phone"),
            pax=int(b["pax"]) if b.get("pax") is not None else None,
            date=b.get("date"),
            time=b.get("time"),
            notes=b.get("notes"),
            dp_amount=int(b["dp_amount"]) if b.get("dp_amount") is not None else None,
            dp_method=b.get("dp_method"),
        )
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 400

    # 2) Re-read table_number + final date/time so we emit to the right tile
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute("SELECT table_number, date, time FROM reservations WHERE id=%s", (res_id,))
        row = c.fetchone()
        if not row:
            return jsonify({"status":"not_found"}), 404
        table_no = str(row["table_number"])
        # final date/time (after update)
        date_str = row["date"]
        time_val = row["time"]  # can be time or "HH:MM:SS"
        hhmm = time_val.strftime("%H:%M") if hasattr(time_val, "strftime") else str(time_val)[:5]

    ts_iso = svc_res._make_ts_iso(date_str, hhmm)
    # 3) Emit (safe variant is fine here; DB commit is done)
    push_reservation_changed(table_no, ts_iso)

    return jsonify({"status":"success"})

@bp.get("/reservations/lookup")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def reservations_lookup():
    q = (request.args.get("q") or "").strip()
    only_upcoming = (request.args.get("upcoming", "1") != "0")
    include_split_meta = (request.args.get("split_meta", "1") != "0")

    conn = db.connect_db(None)
    rows = []
    sess_rows = []
    try:
        with conn.cursor() as c:
            if q:
                # free text: matches name/phone/table, show recent + upcoming
                c.execute("""
                    SELECT r.id, r.guest_name, COALESCE(r.phone,''), r.pax,
                           CAST(r.date AS TEXT), to_char(r.time, 'HH24:MI'),
                           r.table_number, COALESCE(r.status,'confirmed'),
                           r.session_id, s.split_labels
                      FROM public.reservations r
                      LEFT JOIN public.sessions s ON s.id = r.session_id
                     WHERE (%s = '' OR r.guest_name ILIKE '%%' || %s || '%%'
                                     OR r.phone ILIKE '%%' || %s || '%%'
                                     OR CAST(r.table_number AS TEXT) = %s
                                     OR (%s AND COALESCE(s.split_labels,'') ILIKE '%%' || %s || '%%'))
                       AND (NOT %s OR r.date >= CURRENT_DATE)
                     ORDER BY r.date DESC, r.time DESC
                     LIMIT 100
                """, (q, q, q, q, include_split_meta, q, only_upcoming))
            else:
                # default: today and future, soonest first
                c.execute("""
                    SELECT r.id, r.guest_name, COALESCE(r.phone,''), r.pax,
                           CAST(r.date AS TEXT), to_char(r.time, 'HH24:MI'),
                           r.table_number, COALESCE(r.status,'confirmed'),
                           r.session_id, s.split_labels
                      FROM public.reservations r
                      LEFT JOIN public.sessions s ON s.id = r.session_id
                     WHERE r.date >= CURRENT_DATE
                     ORDER BY r.date ASC, r.time ASC
                     LIMIT 100
                """)
            rows = c.fetchall()

            # Active sessions (walk-ins) - keep query simple, filter in Python
            try:
                c.execute("""
                    SELECT s.id, s.table_number, COALESCE(s.guest_name,''), COALESCE(s.pax,1),
                           to_char(s.created_at, 'YYYY-MM-DD') AS d,
                           to_char(s.created_at, 'HH24:MI') AS t,
                           s.split_labels
                      FROM public.sessions s
                     WHERE s.status = 'active'
                     ORDER BY s.created_at DESC
                     LIMIT 200
                """)
                sess_rows = c.fetchall()
            except Exception:
                # fallback if split_labels column is missing or other error
                current_app.logger.exception("reservations_lookup: session query failed (with split_labels), retrying")
                try:
                    c.execute("""
                        SELECT s.id, s.table_number, COALESCE(s.guest_name,''), COALESCE(s.pax,1),
                               to_char(s.created_at, 'YYYY-MM-DD') AS d,
                               to_char(s.created_at, 'HH24:MI') AS t
                          FROM public.sessions s
                         WHERE s.status = 'active'
                         ORDER BY s.created_at DESC
                         LIMIT 200
                    """)
                    sess_rows = [(*r, None) for r in c.fetchall()]
                except Exception:
                    current_app.logger.exception("reservations_lookup: session query failed (fallback)")
                    sess_rows = []
    finally:
        try: conn.close()
        except Exception: pass

    def _split_meta_text(raw):
        if not raw:
            return ""
        try:
            import json as _json
            if isinstance(raw, str):
                raw = _json.loads(raw)
            meta = normalize_split_meta(raw)
        except Exception:
            return ""
        names = []
        for m in meta:
            nm = (m.get("name") or "").strip()
            key = (m.get("key") or "").strip()
            if nm:
                names.append(nm)
            elif key:
                names.append(key)
        return ", ".join(names)

    reservation_items = []
    for r in rows:
        split_meta = _split_meta_text(r[9] if len(r) > 9 else None)
        guest_name = r[1] or ""
        display_name = guest_name or split_meta or "—"
        search_name = f"{guest_name} {split_meta}".strip()
        reservation_items.append({
            "id": r[0], "guest_name": guest_name, "phone": r[2], "pax": int(r[3] or 0),
            "date": r[4], "time": r[5], "table_number": str(r[6] or ""),
            "status": r[7], "kind": "reservation",
            "session_id": r[8] or None,
            "split_meta": split_meta,
            "display_name": display_name,
            "search_name": search_name,
        })

    session_items = []
    res_session_ids = {r[8] for r in rows if len(r) > 8 and r[8]}
    q_l = (q or "").strip().lower()
    for r in sess_rows:
        sid, table_number, guest_name, pax, d, t, split_raw = r
        table_text = (str(table_number) if table_number is not None else "").strip()
        if not table_text:
            continue
        if table_text.upper().startswith("RES:"):
            continue
        split_meta_text = _split_meta_text(split_raw)
        if sid in res_session_ids:
            continue
        display_name = (
            (guest_name or "").strip()
            or split_meta_text
            or (f"Meja {table_text}" if table_text else "—")
        )
        search_name = f"{guest_name} {split_meta_text} {table_text}".strip()
        if q_l:
            hay = f"{search_name} {table_number}".lower()
            if q_l not in hay:
                continue
        session_items.append({
            "id": f"session:{sid}",
            "guest_name": guest_name,
            "phone": "",
            "pax": int(pax or 1),
            "date": d,
            "time": t,
            "table_number": table_text,
            "status": "active",
            "kind": "session",
            "session_id": sid,
            "split_meta": split_meta_text,
            "display_name": display_name,
            "search_name": search_name,
        })

    items = session_items + reservation_items

    tables = db.load_tables()
    table_numbers = [t.get("number") for t in tables if t.get("number")]

    return render_template(
        "reservations_lookup.html",
        items=items,
        q=q,
        upcoming=1 if only_upcoming else 0,
        show_cancelled=0,
        split_meta_on=1 if include_split_meta else 0,
        table_numbers=table_numbers,
        tables=tables,
    )
