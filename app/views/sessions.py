from datetime import datetime
import re
import secrets
import os
from ..socketbus import push_reservation_changed_deferred  
from flask import (
    Blueprint, current_app, request, jsonify, redirect, url_for,
    render_template, flash
)
from flask_login import login_required, current_user

from functools import wraps
from psycopg.errors import NotNullViolation

from ..authz import roles_required
from ..helpers import fmt_dt
from ..events import (
    session_closed, table_moved,
    session_items_changed
)
from ..socketbus import _push_state, push_reservation_autoseated, _push_reservation_changed_safe
from utils import db
from utils.data.splits import normalize_split_meta, split_meta_labels
from utils.db import connect_db
from utils.data import reservations as data_res
from utils.services import reservations as svc_res
from app.socketbus import broadcast, push_session_created
from app.socketbus import (
    push_reservation_changed,
    push_reservation_changed_deferred,
    push_reservation_autoseated,
    push_session_created,
    broadcast,
)
from utils.services import reservations as svc_res  
from utils.data.core import connect_db
from utils.config_store import get_billing_config
bp = Blueprint("sessions", __name__)


# ---------------------------------------------------------------------------
# Locks
# ---------------------------------------------------------------------------

def requires_session_lock(get_sid_fn):
    def deco(fn):
        @wraps(fn)
        def _wrap(*args, **kwargs):
            sid = get_sid_fn(*args, **kwargs)
            if not db.user_holds_session_lock(None, sid, current_user.id):
                _, owner_name, _ = db.get_session_lock_owner(None, sid)
                msg = f"{owner_name or 'Pengguna lain'} sedang mengakses meja ini"
                if request.is_json:
                    return jsonify({"status": "error", "message": msg}), 409
                flash(msg, "error")
                return redirect(url_for("dashboard.dashboard"))
            return fn(*args, **kwargs)
        return _wrap
    return deco


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_takeaway_session_id():
    """Create a short, human-friendly ID (same pattern as /takeaway/)."""
    return datetime.utcnow().strftime("S%y%m%d%H%M%S") + "-" + secrets.token_hex(2)


def _compute_bill_total(session_id, group_label=None):
    """Compute subtotal+service+tax total for a session/group (used by the chooser)."""
    rows = db.get_all_order_items_by_session(None, session_id) or []
    def _norm_group(v):
        if v is None: return ""
        s = str(v).strip()
        return "" if s.lower() in ("", "null", "none") else s
    # filter by group if provided
    if group_label is not None:
        want = _norm_group(group_label)
        rows = [r for r in rows if _norm_group(r[9]) == want]

    # service type
    svc_type = db.get_session_service_type(None, session_id) or "dine_in"
    is_ta = (svc_type == "takeaway")
    billing_cfg = get_billing_config()
    service_pct_default = int(billing_cfg.get("service_percent", 5))
    tax_pct_default = int(billing_cfg.get("tax_percent", 10))
    tax_on_service = bool(billing_cfg.get("tax_on_service"))

    subtotal = 0
    for r in rows:
        status = (r[7] or "").lower()
        if status == "cancelled":
            continue
        qty = float(r[2] or 0)
        void = float(r[10] or 0) if len(r) > 10 else 0
        net_qty = max(0, qty - void)
        if net_qty <= 0:
            continue
        price = int(float(r[3] or 0))
        subtotal += int(round(net_qty * price))

    # Packaging fee is optional (even for takeaway); default summary excludes it.
    packaging = 0
    base = subtotal + packaging
    # Align with billing.js / receipt math: service 5% (dine-in only), tax 10% on base (no tax-on-service)
    service = 0 if is_ta else round(base * (service_pct_default / 100.0))
    tax_base = base + service if tax_on_service else base
    tax = round(tax_base * (tax_pct_default / 100.0))
    total = base + service + tax
    return {
        "service_type": "takeaway" if is_ta else "dine_in",
        "subtotal": int(subtotal),
        "packaging": int(packaging),
        "service": int(service),
        "tax": int(tax),
        "total": int(total),
    }


def _persist_session_dp_payment(session_id, dp_amount, dp_method):
    if dp_amount <= 0 or not dp_method:
        return
    try:
        with connect_db() as conn, conn.cursor() as c:
            c.execute(
                """
                UPDATE public.sessions
                   SET dp_method = %s,
                       dp_paid_at = NOW()
                 WHERE id = %s
                """,
                (dp_method, session_id),
            )
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
                VALUES
                    (%s, %s, %s, NOW(),
                     NULL, 0,
                     0, 0,
                     0, 0, %s,
                     NULL, %s, NULL,
                     0, FALSE, NULL,
                     NULL, NULL, TRUE)
                """,
                (
                    session_id,
                    dp_amount,
                    dp_method,
                    dp_amount,
                    current_user.id,
                ),
            )
            conn.commit()
    except Exception:
        current_app.logger.exception(
            "Failed to set dp_method/dp_paid_at or insert DP payment for session %s",
            session_id,
        )


def _notify_session_opened(table_number, session_id):
    ts_iso = None
    try:
        nxt = svc_res.get_next_for_table_today(None, table_number)
        ts_iso = svc_res._make_ts_iso(
            nxt.get("date"), nxt.get("time")
        ) if nxt else None
        push_reservation_changed_deferred(table_number, ts_iso)
    except Exception as e:
        current_app.logger.exception("failed to push reservation_changed: %s", e)

    push_session_created(table_number, session_id, ts_iso)
    return ts_iso


def _create_live_session_for_table(table_number, *, pax=1, guest_name=None, dp_amount=0, note=None, dp_method=None):
    session_id = db.create_session(
        None, table_number, pax, guest_name, dp_amount, note,
        opened_by_user_id=current_user.id
    )
    _persist_session_dp_payment(session_id, int(dp_amount or 0), dp_method)
    _notify_session_opened(table_number, session_id)
    return session_id


# ---------------------------------------------------------------------------
# Reservations -> seat now (POST)
# ---------------------------------------------------------------------------

@bp.post("/reservations/<int:reservation_id>/seat")
@login_required
@roles_required("admin", "cashier", "waiter")
def seat_reservation_now(reservation_id):
    # Load reservation: target table + possible existing session
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT table_number, session_id FROM public.reservations WHERE id=%s", (reservation_id,))
        row = c.fetchone()
        if not row:
            flash("Reservasi tidak ditemukan", "error")
            return redirect(url_for("dashboard.dashboard"))
        table_number, res_sid = (str(row[0]) if row[0] is not None else None), (row[1] or None)

    if not table_number:
        flash("Reservasi belum memiliki nomor meja", "error")
        return redirect(url_for("dashboard.dashboard"))

    # If we already created a reservation-backed session, use it.
    if res_sid:
        sid = res_sid

        # Import any leftover reservation_items (if you still use them)
        try:
            svc_res.transfer_preorders_to_session(None, reservation_id, sid, current_user.id)
        except Exception:
            current_app.logger.exception("Failed importing preorders for reservation %s", reservation_id)

        # If target table has an active session -> merge; else move the reservation session over.
        occupied = db.get_session_by_table(None, table_number)
        if occupied and occupied != sid:
            ok, msg = db.merge_sessions(None, sid, occupied, by_user_id=current_user.id)
            if not ok:
                flash(f"Gagal gabung sesi: {msg}", "error")
                return redirect(url_for("dashboard.dashboard"))
            sid = occupied  # merged into target
        else:
            try:
                db.move_session_table(None, sid, table_number, by_user_id=current_user.id)
            except Exception:
                current_app.logger.exception("move_session_table failed")
                flash("Gagal pindah sesi ke meja", "error")
                return redirect(url_for("dashboard.dashboard"))

        # Mark reservation as seated (idempotent)
        with connect_db() as conn, conn.cursor() as c:
            c.execute("""
                UPDATE public.reservations
                   SET status='seated', session_id=%s, seated_by_user_id=%s, table_number=%s
                 WHERE id=%s
            """, (sid, current_user.id, table_number, reservation_id))
            conn.commit()

    else:
        # Legacy path: if (for some reason) no virtual session exists, fall back to your old flow.
        sid = svc_res.seat_reservation_by_id(None, reservation_id, by_user_id=current_user.id)
        try:
            svc_res.transfer_preorders_to_session(None, reservation_id, sid, current_user.id)
        except Exception:
            current_app.logger.exception("Failed importing preorders for reservation %s", reservation_id)

    # NEW: sync DP from reservations -> sessions AND ensure a DP payment row exists
    try:
        with connect_db() as conn, conn.cursor() as c:
            # sync DP fields
            c.execute(
                """
                UPDATE public.sessions s
                   SET dp_amount = COALESCE(r.dp_amount, s.dp_amount),
                       dp_method = COALESCE(r.dp_method, s.dp_method),
                       dp_paid_at = COALESCE(
                           s.dp_paid_at,
                           CASE WHEN COALESCE(r.dp_amount,0) > 0 THEN NOW() ELSE NULL END
                       )
                  FROM public.reservations r
                 WHERE r.id = %s
                   AND s.id = %s
                """,
                (reservation_id, sid),
            )

            # create DP payment row if missing (covers legacy/open_reservation path)
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
                    %s, r.dp_amount, r.dp_method, NOW(),
                    NULL, 0,
                    0, 0,
                    0, 0, r.dp_amount,
                    NULL, %s, NULL,
                    0, FALSE, NULL,
                    NULL, NULL, TRUE
                  FROM public.reservations r
                 WHERE r.id = %s
                   AND COALESCE(r.dp_amount,0) > 0
                   AND NOT EXISTS (
                        SELECT 1 FROM public.payments p
                         WHERE p.session_id = %s AND p.is_dp = TRUE
                   )
                """,
                (
                    sid,
                    current_user.id,
                    reservation_id,
                    sid,
                ),
            )

            conn.commit()
    except Exception:
        current_app.logger.exception(
            "seat_reservation_now: failed to sync DP or insert DP payment for reservation %s / session %s",
            reservation_id,
            sid,
        )


    # Notify UIs
    push_reservation_autoseated(table_number, sid)
    push_reservation_changed(table_number, None)
    push_session_created(table_number, sid, None)

    return redirect(url_for("sessions.view_session", table_number=table_number, session_id=sid))




@bp.get("/api/housekeeping/reservations/auto-seat")
@login_required
@roles_required("admin", "cashier", "waiter")
def reservations_autoseat_tick():
    rows = svc_res.auto_seat_due_reservations_verbose(
        None,
        window_min=svc_res.AUTO_SEAT_MIN,
        opened_by_user_id=current_user.id
    )
    # emit for each newly seated reservation
    for row in rows:
        tn  = row.get("table_number")
        sid = row.get("session_id")
        tsi = row.get("ts_iso")
        if not tn or not sid: 
            continue
        payload = {"table_number": tn, "session_id": sid}
        if tsi: payload["ts_iso"] = tsi
        broadcast("reservations.autoseated", payload)
        broadcast("reservations.autoseated", payload, room=f"table:{tn}")
        push_session_created(tn, sid, tsi)

    return jsonify({"autoseated": len(rows)})

@bp.get("/api/reservations/future/<table_number>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_future_reservations(table_number):
    rows = db.list_future_reservations_for_table(None, table_number) or []
    out = []
    for r in rows:
        # Expect your helper returns dict-like rows; if it's tuples, map accordingly
        d = {
            "id": r.get("id") if isinstance(r, dict) else r[0],
            "guest_name": r.get("guest_name") if isinstance(r, dict) else r[1],
            "pax": r.get("pax") if isinstance(r, dict) else r[2],
            "date": str(r.get("date")) if isinstance(r, dict) else str(r[3]),
            "time": (r.get("time").strftime("%H:%M") if hasattr(r.get("time"), "strftime") else str(r.get("time"))[:5]) if isinstance(r, dict) else (
                    r[4].strftime("%H:%M") if hasattr(r[4], "strftime") else str(r[4])[:5]
            ),
            "phone": (r.get("phone") if isinstance(r, dict) else None) or "",
            "dp_amount": int((r.get("dp_amount") if isinstance(r, dict) else 0) or 0),
        }
        out.append(d)
    return jsonify({"status": "ok", "items": out})

@bp.get("/api/session/summary/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_session_summary(session_id):
    companion = (request.args.get("companion") or "").strip() or None
    split_labels = split_meta_labels(db.get_split_labels(None, session_id) or [])
    groups = []
    if split_labels:
        for lbl in split_labels:
            groups.append({"label": lbl, **_compute_bill_total(session_id, lbl)})
    else:
        groups.append({"label": "main", **_compute_bill_total(session_id, None)})

    companion_total = None
    if companion:
        try:
            companion_total = _compute_bill_total(companion, None)
        except Exception:
            companion_total = None

    # Ensure dine-in first if present
    def _sort_key(g):
        return 0 if g.get("service_type") == "dine_in" else 1
    groups = sorted(groups, key=_sort_key)

    return jsonify({"status": "ok", "groups": groups, "companion_total": companion_total})


@bp.post("/api/table/<table_number>/quick_open")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_quick_open_table(table_number):
    active_sid = db.get_session_by_table(None, table_number)
    if active_sid:
        return jsonify({
            "status": "ok",
            "session_id": active_sid,
            "redirect": url_for("sessions.view_session", table_number=table_number, session_id=active_sid),
        })

    lockout = svc_res.get_lockout_for_table(None, table_number)
    if lockout:
        return jsonify({
            "status": "needs_choice",
            "message": "Table has an upcoming reservation.",
            "redirect": url_for("sessions.view_table", table_number=table_number),
        }), 409

    session_id = _create_live_session_for_table(table_number, pax=1)
    return jsonify({
        "status": "ok",
        "session_id": session_id,
        "redirect": url_for("sessions.view_session", table_number=table_number, session_id=session_id),
    })

# ---------------------------------------------------------------------------
# Start or Reserve a table
# ---------------------------------------------------------------------------

@bp.route("/table/<table_number>", methods=["GET", "POST"])
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def view_table(table_number):
    active_sid = db.get_session_by_table(None, table_number)

    if request.method == "POST":
        kind = (request.form.get("kind") or "open_table").strip()

        # ----- A) Open a live session now -----
        if kind == "open_table":
            if active_sid:
                return redirect(
                    url_for("sessions.view_session",
                            table_number=table_number,
                            session_id=active_sid)
                )

            # Enforce lockout window if there is a reservation soon
            lockout = svc_res.get_lockout_for_table(None, table_number)
            if lockout:
                flash(
                    f"Meja terkunci: ada reservasi pada {lockout['date']} "
                    f"{lockout['time'].strftime('%H:%M')}. "
                    "Tidak bisa buka sesi biasa dalam 2 jam sebelum waktu reservasi. "
                    "Silakan buka/seat reservasi.",
                    "warning"
                )
                return redirect(url_for("sessions.view_table", table_number=table_number))

            # No lockout: open a normal live session
            pax        = int(request.form.get("pax", 1) or 1)
            guest_name = request.form.get("guest_name") or None
            dp_amount  = int(request.form.get("dp_amount") or 0)
            note       = request.form.get("note") or None
            dp_method  = (request.form.get("dp_method") or "").strip() or None

            # Basic validation for DP
            if dp_amount < 0:
                flash("DP tidak boleh minus.", "error")
                return redirect(url_for("sessions.view_table", table_number=table_number))
            if dp_amount > 0 and not dp_method:
                flash("Metode DP wajib diisi jika ada DP.", "error")
                return redirect(url_for("sessions.view_table", table_number=table_number))

            session_id = _create_live_session_for_table(
                table_number,
                pax=pax,
                guest_name=guest_name,
                dp_amount=dp_amount,
                note=note,
                dp_method=dp_method,
            )
            return redirect(
                url_for("sessions.view_session",
                        table_number=table_number,
                        session_id=session_id)
            )
        # ----- B) Create a reservation for this table -----
        elif kind == "open_reservation":
            guest_name = (request.form.get("guest_name") or "").strip()
            phone      = (request.form.get("phone") or "").strip() or None
            pax_raw    = (request.form.get("pax") or "1").strip()
            date_raw   = request.form.get("date")
            time_raw   = request.form.get("time")
            notes      = (request.form.get("note") or "").strip() or None
            dp_amount  = int(request.form.get("dp_amount") or 0)
            dp_method  = (request.form.get("dp_method") or "").strip() or None

            def _parse_date(val):
                if not val:
                    return None
                s = str(val).strip()
                if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                    return s
                m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
                if m:
                    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                return None

            def _parse_time(tval, hval, mval):
                if tval:
                    s = str(tval).strip()
                    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", s)
                    if m:
                        return f"{m.group(1).zfill(2)}:{m.group(2)}"
                hh = (str(hval or "")).strip()
                mm = (str(mval or "")).strip()
                if hh.isdigit() and mm.isdigit():
                    return f"{hh.zfill(2)}:{mm.zfill(2)}"
                return None

            date = _parse_date(date_raw) or datetime.now().date().isoformat()
            time_ = _parse_time(time_raw, request.form.get("hour"), request.form.get("minute"))

            def back(msg):
                flash(msg, "error")
                return redirect(url_for("sessions.view_table", table_number=table_number))

            # Basic validations
            if not guest_name:
                return back("Nama tamu wajib diisi.")
            try:
                pax = max(int(pax_raw), 1)
            except Exception:
                return back("PAX tidak valid.")
            if not date or not time_:
                return back("Tanggal & jam reservasi wajib diisi.")
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date) or not re.match(r"^\d{2}:\d{2}$", time_):
                return back("Format tanggal/jam tidak valid.")
            if dp_amount < 0:
                return back("DP tidak boleh minus.")

            # Insert reservation
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

            
            except NotNullViolation:
                return back("Nama tamu wajib diisi.")
            except Exception:
                current_app.logger.exception("Failed to create reservation")
                return back("Gagal membuat reservasi.")

            flash("Reservasi dibuat.", "success")

            # Hint floors to recolor (safe)
            ts_iso = svc_res._make_ts_iso(date, time_)
            push_reservation_changed_deferred(table_number, ts_iso)

            
            # Re-render chooser with updated lists
            next_res = svc_res.get_next_for_table_today(None, table_number)
            return render_template(
                "start_or_reserve.html",
                table_number=table_number,
                next_reservation=next_res,
                opening_hours=list(range(10, 24)),
                lockout=False,
                lockout_info=None,
                active_session_id=db.get_session_by_table(None, table_number),
                future_reservations=db.list_future_reservations_for_table(None, table_number),
            )

        # ----- C) Fallback: behave like open_table -----
        pax = int(request.form.get("pax", 1) or 1)
        guest_name = request.form.get("guest_name") or None
        dp_amount = int(request.form.get("dp_amount") or 0)
        note = request.form.get("note") or None
        dp_method = (request.form.get("dp_method") or "").strip() or None

        if dp_amount < 0:
            flash("DP tidak boleh minus.", "error")
            return redirect(url_for("sessions.view_table", table_number=table_number))
        if dp_amount > 0 and not dp_method:
            flash("Metode DP wajib diisi jika ada DP.", "error")
            return redirect(url_for("sessions.view_table", table_number=table_number))

        session_id = _create_live_session_for_table(
            table_number,
            pax=pax,
            guest_name=guest_name,
            dp_amount=dp_amount,
            note=note,
            dp_method=dp_method,
        )

        return redirect(url_for("sessions.view_session", table_number=table_number, session_id=session_id))


    # GET -> Always render chooser page
    next_res     = svc_res.get_next_for_table_today(None, table_number)
    lockout_info = svc_res.get_lockout_for_table(None, table_number)
    future_list  = db.list_future_reservations_for_table(None, table_number)

    return render_template(
        "start_or_reserve.html",
        table_number=table_number,
        active_session_id=active_sid,
        next_reservation=next_res,
        future_reservations=future_list,
        opening_hours=list(range(10, 24)),
        lockout=bool(lockout_info),
        lockout_info=lockout_info,
    )


@bp.post("/table/<table_number>/<session_id>/open_takeaway")
@login_required
@roles_required("admin", "cashier", "waiter")
@requires_session_lock(lambda table_number, session_id: session_id)
def open_takeaway_for_table(table_number, session_id):
    """Create (or reuse) a takeaway session that stays linked to this dine-in table."""
    base = db.get_session_by_id(None, session_id)
    if not base:
        return jsonify({"status": "error", "message": "Sesi tidak ditemukan"}), 404

    _, base_table, status = base
    if status != "active":
        return jsonify({"status": "error", "message": "Sesi sudah ditutup"}), 409

    # Trust DB table number if it differs from the URL
    table_number = base_table or table_number

    st = (db.get_session_service_type(None, session_id) or "dine_in")
    if st == "takeaway":
        return jsonify({"status": "error", "message": "Gunakan tombol ini dari sesi dine-in"}), 400

    existing = db.get_active_takeaway_for_table(None, table_number)
    if existing and existing.get("id"):
        return jsonify({
            "status": "ok",
            "session_id": existing["id"],
            "redirect": url_for("sessions.view_session", table_number=table_number, session_id=existing["id"])
        })

    payload     = request.get_json(silent=True) or {}
    guest_name  = (payload.get("guest_name") or "").strip()
    pickup_time = (payload.get("pickup_time") or "").strip() or None
    note        = (payload.get("note") or "").strip() or None

    # Fallback name so staff still see the table ref on the takeaway list
    if not guest_name:
        base_detail = db.get_session_detail(None, session_id)
        base_guest  = base_detail[1] if base_detail else None
        guest_name  = base_guest or f"Meja {table_number} (Take Away)"

    new_sid = _new_takeaway_session_id()

    try:
        with connect_db() as conn, conn.cursor() as c:
            c.execute("""
                INSERT INTO public.sessions
                    (id, pax, table_number, created_at,
                     guest_name, note, status,
                     service_type, pickup_time, opened_by_user_id)
                VALUES
                    (%s, 1, %s, NOW(),
                     %s, %s, 'active',
                     'takeaway', %s, %s)
            """, (
                new_sid,
                table_number,
                guest_name or None,
                note or None,
                pickup_time,
                current_user.id,
            ))
            conn.commit()
    except Exception:
        current_app.logger.exception("open_takeaway_for_table: failed to create TA session")
        return jsonify({"status": "error", "message": "Gagal membuat take away"}), 500

    try:
        broadcast("takeaway:list_changed", {"id": new_sid, "op": "create"})
    except Exception:
        current_app.logger.exception("open_takeaway_for_table: broadcast failed")

    return jsonify({
        "status": "ok",
        "session_id": new_sid,
        "redirect": url_for("sessions.view_session", table_number=table_number, session_id=new_sid)
    })


# ---------------------------------------------------------------------------
# View one session
# ---------------------------------------------------------------------------

@bp.get("/table/<table_number>/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def view_session(table_number, session_id):
    session = db.get_session_detail(None, session_id)
    if not session:
        return redirect(url_for("sessions.view_table", table_number=table_number))

    status = session[5]

    # Read-only view for non-active session if exact=1
    if status != "active" and request.args.get("exact") == "1":
        raw_items = db.get_all_order_items_by_session(None, session_id) or []

        def _num(x):
            try:
                return float(x or 0)
            except Exception:
                return 0.0

        order_rows = []
        for r in raw_items:
            gross_q = _num(r[2]); void_q = _num(r[10]); net_q = max(0.0, gross_q - void_q)
            order_rows.append({
                "id": r[0],
                "item_name": r[1],
                "qty": net_q,
                "unit_price": int(_num(r[3])),
                "note": r[6] or "",
                "status": (r[7] or "").lower(),
                "timestamp": str(r[8]),
                "bill_group": (r[9] or "main"),
            })

        group_subtotals = {}
        for rr in order_rows:
            g = rr.get("bill_group") or "main"
            group_subtotals[g] = group_subtotals.get(g, 0) + int(rr["unit_price"] * rr["qty"])

        group_status = {}
        for r in raw_items:
            g = (r[9] or "main")
            st = (r[7] or "").lower()
            s = group_status.setdefault(g, {"paid": 0, "unpaid": 0})
            if st == "paid":
                s["paid"] += 1
            elif st != "cancelled":
                s["unpaid"] += 1
        for g, s in group_status.items():
            s["all_paid"] = (s["unpaid"] == 0 and s["paid"] > 0)
        if "main" not in group_status:
            group_status["main"] = {"paid": 0, "unpaid": 0, "all_paid": False}

        raw_labels = db.get_split_labels(None, session_id) or []
        split_meta = normalize_split_meta(raw_labels)
        labels = [m["key"] for m in split_meta]

        dp_total = db.get_dp_amount(None, session_id) or 0
        dp_used  = db.get_dp_used(None, session_id) or 0
        dp_remaining = max(dp_total - dp_used, 0)

        conn_meta = db.connect_db(None)
        c_meta = conn_meta.cursor()
        try:
            c_meta.execute("SELECT service_type FROM public.sessions WHERE id=%s", (session_id,))
            row_meta = c_meta.fetchone()
        finally:
            conn_meta.close()
        service_type = (row_meta[0] if row_meta else "dine_in")
        is_takeaway = (service_type == "takeaway")

        tables = db.load_tables()
        active_map = db.get_active_sessions(None)

        return render_template(
            "table.html",
            table_number=table_number,
            session_id=session_id,
            session={"id": session_id},
            combined_items=order_rows,
            tables=tables,
            active_map=active_map,
            split_labels=labels,
            split_meta=split_meta,
            group_subtotals=group_subtotals,
            dp_remaining=dp_remaining,
            group_status=group_status,
            lock_nonce="",
            is_takeaway=is_takeaway,
            read_only=True,
            linked_takeaway=None,
            linked_dinein_id=None,
        )

    if status != "active":
        return redirect(url_for("sessions.view_table", table_number=table_number))

    # Acquire lock
    ok, owner_or_nonce = db.try_acquire_session_lock(None, session_id, current_user.id)
    if not ok:
        return render_template(
            "lock_error.html",
            table_number=table_number,
            session_id=session_id,
            owner_username=owner_or_nonce or "Pengguna lain",
        ), 409
    lock_nonce = owner_or_nonce

    pax, guest_name, dp_amount, note, created_at_raw, _, _ = session
    try:
        created_at_str = fmt_dt(created_at_raw, "%d-%m-%Y %H:%M")
    except Exception:
        created_at_str = str(created_at_raw)

    # Load the extra session meta once; this sits on the table-open hot path.
    conn_meta = db.connect_db(None)
    c_meta = conn_meta.cursor()
    c_meta.execute(
        """
        SELECT
            COALESCE(CAST(service_type AS TEXT), 'dine_in'),
            pickup_time,
            dp_method
        FROM public.sessions
        WHERE id=%s
        """,
        (session_id,),
    )
    row_meta = c_meta.fetchone()
    conn_meta.close()
    service_type, pickup_time_raw, dp_method = (row_meta if row_meta else ("dine_in", None, None))
    is_takeaway = (service_type == "takeaway")
    pickup_time_str = None
    if pickup_time_raw:
        try:
            pickup_time_str = fmt_dt(pickup_time_raw, "%d-%m-%Y %H:%M")
        except Exception:
            pickup_time_str = str(pickup_time_raw)

    session_data = {
        "id": session_id,
        "pax": pax,
        "guest_name": guest_name,
        "dp_amount": dp_amount,
        "note": note,
        "created_at": created_at_str,
        "service_type": service_type,
        "pickup_time": pickup_time_str,
        "dp_method": dp_method,
    }

    linked_takeaway = None
    linked_dinein_id = None
    try:
        if is_takeaway:
            # When viewing the takeaway session, surface the dine-in link (if any)
            linked_dinein_id = db.get_session_by_table(None, table_number)
        else:
            # When on dine-in, show an existing takeaway summary (if present)
            ta = db.get_active_takeaway_for_table(None, table_number)
            billing_cfg = get_billing_config()
            fee = int(billing_cfg.get("takeaway_fee_idr", 10000))
            tax_pct_default = int(billing_cfg.get("tax_percent", 10))
            if ta and ta.get("id") != session_id:
                subtotal = int(ta.get("subtotal") or 0)
                # Packaging is optional; show estimate without auto fee
                tax = round(subtotal * (tax_pct_default / 100.0))
                linked_takeaway = {
                    **ta,
                    "total_estimated": subtotal + tax,
                    "fee": fee,
                    "tax": tax,
                }
    except Exception:
        current_app.logger.exception("view_session: failed to load linked takeaway info")

    # Raw rows (no combining)
    raw_items = db.get_all_order_items_by_session(None, session_id)

    def _num(x):
        try:
            return float(x or 0)
        except Exception:
            return 0.0

    order_rows = []
    for r in raw_items:
        gross_q = _num(r[2])
        void_q  = _num(r[10])
        net_q   = max(0.0, gross_q - void_q)
        order_rows.append({
            "id": r[0],
            "ids": [r[0]] if r[0] is not None else [],
            "item_name": r[1],
            "qty": net_q,
            "net_qty": net_q,
            "gross_qty": gross_q,
            "void_qty": void_q,
            "unit_price": int(_num(r[3])),
            "price": int(_num(r[3])),
            "note": r[6] or "",
            "status": (r[7] or "").lower(),
            "timestamp": str(r[8]),
            "bill_group": (r[9] or "main"),
        })

    group_subtotals = {}
    for rr in order_rows:
        g = rr.get("bill_group") or "main"
        group_subtotals[g] = group_subtotals.get(g, 0) + int(rr["unit_price"] * rr["qty"])

    full_subtotal = sum(int(rr["unit_price"] * rr["qty"]) for rr in order_rows)

    dp_total = db.get_dp_amount(None, session_id) or 0
    dp_used = db.get_dp_used(None, session_id) or 0
    dp_remaining = max(dp_total - dp_used, 0)

    tables = db.load_tables()
    active_map = db.get_active_sessions(None)
    raw_labels = db.get_split_labels(None, session_id) or []
    split_meta = normalize_split_meta(raw_labels)
    labels = [m["key"] for m in split_meta]

    group_status = {}
    for r in raw_items:
        g = r[9] or "main"
        st = (r[7] or "").lower()
        s = group_status.setdefault(g, {"paid": 0, "unpaid": 0})
        if st == "paid":
            s["paid"] += 1
        elif st != "cancelled":
            s["unpaid"] += 1
    for g, s in group_status.items():
        s["all_paid"] = (s["unpaid"] == 0 and s["paid"] > 0)
    if "main" not in group_status:
        group_status["main"] = {"paid": 0, "unpaid": 0, "all_paid": False}
    for lbl in labels:
        group_status.setdefault(lbl, {"paid": 0, "unpaid": 0, "all_paid": False})

    return render_template(
        "table.html",
        table_number=table_number,
        session_id=session_id,
        session=session_data,
        combined_items=order_rows,
        tables=tables,
        active_map=active_map,
        split_labels=labels,
        split_meta=split_meta,
        group_subtotals=group_subtotals,
        full_subtotal=full_subtotal,
        dp_remaining=dp_remaining,
        group_status=group_status,
        lock_nonce=lock_nonce,
        is_takeaway=is_takeaway,
        linked_takeaway=linked_takeaway,
        linked_dinein_id=linked_dinein_id,
    )


# ---------------------------------------------------------------------------
# Session meta update (DP, pax, name, note, pickup_time)
# ---------------------------------------------------------------------------

@bp.post("/session/update/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def session_update(session_id):
    data = request.get_json(silent=True) or {}

    pax_raw        = data.get("pax", None)
    guest_name     = (data.get("guest_name") or "").strip()
    note           = (data.get("note") or "").strip()
    pickup_time    = (data.get("pickup_time") or "").strip() or None
    dp_raw         = data.get("dp_amount", None)
    dp_method_raw  = (data.get("dp_method") or "").strip()
    dp_method      = dp_method_raw or None

    # Normalize pax
    pax = None
    if pax_raw is not None:
        try:
            pax = max(int(pax_raw), 1)
        except Exception:
            return jsonify({"status": "error", "message": "PAX invalid"}), 400

    # Normalize DP amount
    dp_amount = None
    if dp_raw is not None:
        try:
            if isinstance(dp_raw, str):
                import re as _re
                m = _re.sub(r"[^\d]", "", dp_raw)
                dp_amount = int(m or "0")
            else:
                dp_amount = int(dp_raw)
            if dp_amount < 0:
                return jsonify({"status": "error", "message": "DP tidak boleh minus"}), 400
        except Exception:
            return jsonify({"status": "error", "message": "DP invalid"}), 400

    conn = db.connect_db(None)
    row = None
    eff_dp_method = None
    delta = 0

    try:
        with conn.cursor() as c:
            # Get current meta + current DP state
            c.execute("""
                SELECT id, pax, guest_name, note, pickup_time,
                       COALESCE(dp_amount,0)::int AS dp_amount,
                       COALESCE(dp_method,'')    AS dp_method
                  FROM public.sessions
                 WHERE id=%s
            """, (session_id,))
            row = c.fetchone()
            if not row:
                return jsonify({"status": "error", "message": "Session not found"}), 404

            old_dp_amount = int(row[5] or 0)
            old_dp_method = (row[6] or "").strip() or None

            sets, vals = [], []

            # Basic fields
            if pax is not None:
                sets.append("pax=%s")
                vals.append(pax)

            if guest_name != "":
                sets.append("guest_name=%s")
                vals.append(guest_name)
            else:
                sets.append("guest_name=NULL")

            if note != "":
                sets.append("note=%s")
                vals.append(note)
            else:
                sets.append("note=NULL")

            if pickup_time is not None:
                sets.append("pickup_time=%s")
                vals.append(pickup_time)

            # ------------- DP logic in sessions table -------------------
            eff_dp_method = old_dp_method
            delta = 0  # new_dp - old_dp

            if dp_amount is not None:
                delta = dp_amount - old_dp_amount  # + = tambah DP, - = refund DP

                if dp_amount > 0:
                    # Prefer newly sent method, fall back to old if any
                    eff_dp_method = dp_method or old_dp_method
                    if not eff_dp_method:
                        return jsonify({
                            "status": "error",
                            "message": "Metode DP wajib diisi jika ada DP."
                        }), 400
                else:
                    # DP cleared
                    eff_dp_method = None

                sets.append("dp_amount=%s")
                vals.append(dp_amount)

                sets.append("dp_method=%s")
                vals.append(eff_dp_method)

                if dp_amount > 0:
                    # If previously NULL, mark paid_at now; otherwise keep old timestamp
                    sets.append("dp_paid_at = COALESCE(dp_paid_at, NOW())")
                else:
                    sets.append("dp_paid_at = NULL")

            # Apply UPDATE if anything changed
            if sets:
                sets.append("updated_at=NOW()")
                q = "UPDATE public.sessions SET " + ", ".join(sets) + " WHERE id=%s"
                vals.append(session_id)
                c.execute(q, tuple(vals))

            # ------------- DP → payments table --------------------------

            # 1) Extra DP (delta > 0): insert DP payment row
            if dp_amount is not None and delta > 0:
                extra_dp = delta  # positive

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
                    VALUES
                        (%s, %s, %s, NOW(),
                         NULL, 0,
                         0, 0,
                         0, 0, %s,
                         NULL, %s, NULL,
                         0, FALSE, NULL,
                         NULL, NULL, TRUE)
                    """,
                    (
                        session_id,
                        extra_dp,              # amount = +500000, etc
                        eff_dp_method,         # e.g. 'cash', 'transfer'
                        extra_dp,              # total_before_discount = DP amount
                        getattr(current_user, "id", None),
                    ),
                )

            # 2) DP reduced (delta < 0): insert a REAL refund row like row 36
            if dp_amount is not None and delta < 0:
                refund_amount = -delta  # positive number, e.g. 500000

                # Try to link this refund to the latest DP payment row
                refund_of_id = None
                try:
                    c.execute("""
                        SELECT id
                          FROM public.payments
                         WHERE session_id = %s
                           AND is_dp = TRUE
                           AND is_refund = FALSE
                         ORDER BY paid_at DESC, id DESC
                         LIMIT 1
                    """, (session_id,))
                    src = c.fetchone()
                    if src:
                        refund_of_id = src[0]
                except Exception:
                    refund_of_id = None

                # Insert refund row:
                # amount = -refund_amount
                # method = 'refund'
                # total_before_discount = 0
                # is_dp = FALSE
                # is_refund = TRUE
                # refund_of = original DP payment id (if found)
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
                    VALUES
                        (%s, %s, %s, NOW(),
                         NULL, 0,
                         0, 0,
                         0, 0, 0,
                         NULL, %s, %s,
                         0, TRUE, %s,
                         %s, %s, FALSE)
                    """,
                    (
                        session_id,
                        -refund_amount,                  # amount NEGATIVE (e.g. -500000)
                        "refund",                        # method = 'refund'
                        getattr(current_user, "id", None),
                        "main",                          # bill_group = 'main'
                        refund_of_id,                    # link to DP payment (e.g. 34)
                        "Penyesuaian DP (edit sesi)",    # reason (optional)
                        getattr(current_user, "id", None),
                    ),
                )

        conn.commit()
    except Exception:
        current_app.logger.exception("session_update error")
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"status": "error", "message": "Server error"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

    out = {
        "pax": pax if pax is not None else (row[1] if row else None),
        "guest_name": guest_name if guest_name != "" else None,
        "note": note if note != "" else None,
        "pickup_time": pickup_time,
        "dp_amount": dp_amount if dp_amount is not None else None,
        "dp_method": eff_dp_method if dp_amount is not None else None,
    }

    # Live updates (unchanged)
    try:
        session_items_changed(table_number=None, session_id=session_id)
        _push_state(session_id)
    except Exception:
        pass

    return jsonify({"status": "success", "data": out})


# ---------------------------------------------------------------------------
# Light meta API (used by client)
# ---------------------------------------------------------------------------

@bp.get("/api/session_meta/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_session_meta(session_id):
    conn = db.connect_db(None)
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, table_number,
                       COALESCE(pax,1) AS pax,
                       COALESCE(guest_name,'') AS guest_name,
                       COALESCE(dp_amount,0) AS dp_amount,
                       COALESCE(note,'') AS note,
                       COALESCE(CAST(service_type AS TEXT), 'dine_in') AS service_type_txt,
                       COALESCE(to_char(pickup_time, 'YYYY-MM-DD"T"HH24:MI'),'') AS pickup_time
                  FROM public.sessions
                 WHERE id=%s
            """, (session_id,))
            r = c.fetchone()
            if not r:
                return jsonify({"status": "not_found"}), 404
            service_type_txt = r[6] or "dine_in"
            meta = {
                "session_id": r[0],
                "table_number": r[1],
                "pax": int(r[2]),
                "guest_name": r[3],
                "dp_amount": int(r[4] or 0),
                "note": r[5],
                "is_takeaway": (service_type_txt == "takeaway"),
                "pickup_time": r[7],
            }
            return jsonify({"status": "ok", "data": meta})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Locks heartbeat/release
# ---------------------------------------------------------------------------

@bp.post("/session_lock/<session_id>/heartbeat")
@login_required
def session_lock_heartbeat(session_id):
    data = request.get_json(silent=True) or {}
    nonce = (data.get("nonce") or "").strip()
    ok = db.heartbeat_session_lock(None, session_id, current_user.id, nonce)
    if not ok:
        ok, _ = db.try_acquire_session_lock(None, session_id, current_user.id)
    return (jsonify({"ok": ok}), 200) if ok else (jsonify({"ok": False}), 403)


@bp.post("/session_lock/<session_id>/release")
@login_required
def session_lock_release(session_id):
    data = request.get_json(silent=True) or {}
    nonce = (data.get("nonce") or "").strip()
    ok = db.release_session_lock(None, session_id, current_user.id, nonce)
    return jsonify({"ok": ok})


# ---------------------------------------------------------------------------
# Cancel / Merge / Move
# ---------------------------------------------------------------------------

@bp.post("/cancel_table/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def cancel_table(session_id):
    closed_time = datetime.now().isoformat()
    acting_uid = current_user.id
    svc_type = db.get_session_service_type(None, session_id)

    # 1) Close items + session
    conn = db.connect_db(None)
    try:
        with conn.cursor() as c:
            c.execute(
                "UPDATE public.order_items "
                "SET status='cancelled' "
                "WHERE session_id=%s AND status<>'cancelled'",
                (session_id,)
            )
            c.execute(
                "UPDATE public.sessions "
                "SET status='cancelled', closed_at=%s, closed_by_user_id=%s "
                "WHERE id=%s",
                (closed_time, acting_uid, session_id)
            )
        conn.commit()
    finally:
        conn.close()

    # 2) Signals + state
    table_number = None
    try:
        sess_min = db.get_session_by_id(None, session_id)
        if sess_min:
            _, table_number, _ = sess_min
            if (svc_type or "dine_in") != "takeaway":
                session_closed(table_number, session_id)
            _push_state(session_id)
    except Exception:
        current_app.logger.exception("cancel_table: post-close signals failed")

    # 3) Mirror to reservations (if this session belongs to one)
    try:
        from utils.data.core import connect_db as _connect
        with _connect() as conn2, conn2.cursor() as c2:
            c2.execute(
                "UPDATE public.reservations "
                "SET status='cancelled' "
                "WHERE session_id=%s",
                (session_id,)
            )
            changed = c2.rowcount or 0
            conn2.commit()
        if changed and table_number:
            from app.socketbus import push_reservation_changed
            push_reservation_changed(table_number, None)
    except Exception:
        current_app.logger.exception("cancel_table: failed to mirror reservation")

    # 4) Release lock if we own it
    try:
        owner_uid, _, _, nonce = db.get_session_lock_owner(None, session_id)
        if owner_uid == current_user.id and nonce:
            db.release_session_lock(None, session_id, current_user.id, nonce)
    except Exception:
        pass

    # 5) ALWAYS return a response
    if request.is_json or (request.headers.get("Accept") or "").lower().startswith("application/json"):
        return jsonify({"status": "success", "redirect": url_for("dashboard.dashboard")})
    return redirect(url_for("dashboard.dashboard"))




@bp.post("/merge_table")
@login_required
@roles_required("admin", "cashier", "waiter")
def merge_table():
    data = request.get_json() or {}
    from_session_id = (data.get("session_id") or "").strip()
    to_table = (data.get("to_table") or "").strip()
    if not from_session_id or not to_table:
        return jsonify({"status": "error", "message": "session_id dan to_table wajib"}), 400

    current = db.get_session_by_id(None, from_session_id)
    if not current:
        return jsonify({"status": "error", "message": "Sesi tidak ditemukan"}), 404
    _, current_table, status = current
    if status != "active":
        return jsonify({"status": "error", "message": "Sesi ini tidak aktif"}), 409
    if to_table == current_table:
        return jsonify({"status": "error", "message": "Tidak bisa gabung ke meja yang sama"}), 400

    target_session_id = db.get_session_by_table(None, to_table)
    if not target_session_id:
        return jsonify({"status": "error", "message": "Meja tujuan kosong — pilih meja yang ada sesi"}), 409

    def _has_payments_or_paid_items(sess_id):
        try:
            from utils.data.core import connect_db
            with connect_db() as conn, conn.cursor() as c:
                # Paid items always block
                c.execute(
                    "SELECT COUNT(*) FROM order_items WHERE session_id = %s AND status = 'paid'",
                    (sess_id,),
                )
                if (c.fetchone() or [0])[0] > 0:
                    return True

                # Ignore DP-only payments; those should not block merge
                c.execute(
                    "SELECT COALESCE(dp_amount, 0), COALESCE(dp_method, '') FROM sessions WHERE id = %s",
                    (sess_id,),
                )
                dp_row = c.fetchone() or [0, ""]
                dp_amount = int(dp_row[0] or 0)
                dp_method = (dp_row[1] or "").strip() or None

                c.execute(
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
                rows = c.fetchall() or []
                non_ref = [r for r in rows if not r[1]]
                if not non_ref:
                    return False

                if any(int(r[3] or 0) > 0 for r in non_ref):
                    return True

                non_dp_rows = [r for r in non_ref if not r[0]]
                if not non_dp_rows:
                    return False

                if dp_amount > 0 and all(int(r[3] or 0) == 0 for r in non_dp_rows):
                    total = sum(int(r[2] or 0) for r in non_dp_rows)
                    if dp_method:
                        if all(str(r[4] or "").strip() == dp_method for r in non_dp_rows) and total == dp_amount:
                            return False
                    else:
                        if total == dp_amount:
                            return False

                return any(int(r[2] or 0) > 0 for r in non_dp_rows)
        except Exception:
            # Fail safe: if unsure, treat as paid to prevent unsafe merge
            current_app.logger.exception("merge_table: failed to check payments for session %s", sess_id)
            return True

    src_has_payments = _has_payments_or_paid_items(from_session_id)
    tgt_has_payments = _has_payments_or_paid_items(target_session_id)

    # If the current session already has paid items/payments, merge the OTHER table into it
    # so paid history stays on the current session.
    reversed_merge = False
    if src_has_payments:
        if tgt_has_payments:
            return jsonify({
                "status": "error",
                "message": "Kedua sesi sudah memiliki pembayaran/paid item — tidak bisa gabung.",
            }), 400
        reversed_merge = True
        source_session_id = target_session_id
        target_session_id = from_session_id
        source_table = to_table
        target_table = current_table
    else:
        source_session_id = from_session_id
        target_session_id = target_session_id
        source_table = current_table
        target_table = to_table

    ok, res = db.merge_sessions(None, source_session_id, target_session_id, by_user_id=current_user.id)
    if not ok:
        return jsonify({"status": "error", "message": res}), 400

    try:
        from utils.data.core import connect_db
        with connect_db() as conn, conn.cursor() as c:
            c.execute("""
                UPDATE public.reservations
                   SET session_id=%s, table_number=%s
                 WHERE session_id=%s
            """, (target_session_id, target_table, source_session_id))
            conn.commit()
    except Exception:
        current_app.logger.exception("merge_table: failed to rebind reservation to target session")


    svc_type = db.get_session_service_type(None, source_session_id) or "dine_in"
    if svc_type != "takeaway":
        session_closed(source_table, source_session_id)
    _push_state(source_session_id)

    session_items_changed(target_table, target_session_id)
    _push_state(target_session_id)

    uid, _, _, nonce = db.get_session_lock_owner(None, source_session_id)
    if uid == current_user.id and nonce:
        db.release_session_lock(None, source_session_id, current_user.id, nonce)

    return jsonify({
        "status": "success",
        "redirect": url_for("sessions.view_session", table_number=target_table, session_id=target_session_id),
        "reversed": reversed_merge,
    })


@bp.post("/move_table")
@login_required
@roles_required("admin", "cashier", "waiter")
def move_table():
    data = request.get_json() or {}
    session_id = (data.get("session_id") or "").strip()
    to_table = (data.get("to_table") or "").strip()
    if not session_id or not to_table:
        return jsonify({"status": "error", "message": "session_id and to_table are required"}), 400

    current = db.get_session_by_id(None, session_id)
    if not current:
        return jsonify({"status": "error", "message": "session not found"}), 404

    _, current_table, status = current
    if status != "active":
        return jsonify({"status": "error", "message": "session is not active"}), 409
    if to_table == current_table:
        return jsonify({"status": "error", "message": "already on that table"}), 400

    tables = db.load_tables()
    valid_tables = {t["number"] for t in tables}
    if to_table not in valid_tables:
        return jsonify({"status": "error", "message": "table does not exist"}), 400

    occupied_session = db.get_session_by_table(None, to_table)
    if occupied_session and occupied_session != session_id:
        return jsonify({"status": "error", "message": "table is occupied"}), 409

    try:
        db.move_session_table(None, session_id, to_table, by_user_id=current_user.id)
        table_moved(current_table, to_table, session_id)
        _push_state(session_id)

        # NEW: keep reservation row in sync with the new table
        try:
            from utils.data.core import connect_db
            with connect_db() as conn, conn.cursor() as c:
                c.execute("UPDATE public.reservations SET table_number=%s WHERE session_id=%s", (to_table, session_id))
                changed = c.rowcount or 0
                conn.commit()
            if changed:
                from app.socketbus import push_reservation_changed
                # nudge both tiles: old clears pink, new updates
                push_reservation_changed(current_table, None)
                push_reservation_changed(to_table, None)
        except Exception:
            current_app.logger.exception("move_table: failed to sync reservation table_number")

        return jsonify({
            "status": "success",
            "redirect": url_for("sessions.view_session", table_number=to_table, session_id=session_id)
        })
    except Exception:
        return jsonify({"status": "error", "message": "failed to move table"}), 500


# Helpers for QR-origin detection --------------------------------------------
def _qr_creator_clauses(alias="oi"):
    """
    Build SQL snippets to detect items created by the QR service user.
    Matches by QR_USER_ID env (int) and/or username 'qr_service' (or QR_USERNAME override).
    Returns (clause_sql, params_list) where clause_sql is like "AND (...)" or "".
    """
    clauses = []
    params = []

    qr_uid_env = os.getenv("QR_USER_ID", "").strip()
    try:
        qr_uid = int(qr_uid_env) if qr_uid_env else None
    except ValueError:
        qr_uid = None
    if qr_uid:
        clauses.append(f"{alias}.created_by_user_id = %s")
        params.append(qr_uid)

    qr_uname = (os.getenv("QR_USERNAME") or "qr_service").strip()
    if qr_uname:
        clauses.append(
            f"EXISTS (SELECT 1 FROM public.users u WHERE u.id = {alias}.created_by_user_id AND LOWER(u.username) = LOWER(%s))"
        )
        params.append(qr_uname)

    if not clauses:
        return "", []
    return " AND (" + " OR ".join(clauses) + ")", params

# --- Quick flags for "unsent" items per floor -------------------------------
@bp.get("/api/table/<table_number>/unsent_flag")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_unsent_flag(table_number):
    conn = db.connect_db(None)
    qr_clause, qr_params = _qr_creator_clauses("oi")
    try:
        with conn.cursor() as c:
            c.execute(
                f"""
                SELECT
                  (
                    EXISTS (
                      SELECT 1
                        FROM public.sessions s
                        JOIN public.order_items oi ON oi.session_id = s.id
                       WHERE s.table_number = %s
                         AND COALESCE(s.status,'') = 'active'
                         AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                         AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                    )
                    OR
                    EXISTS (
                      SELECT 1
                        FROM qr.qr_orders qo
                       WHERE qo.table_number = %s
                         AND COALESCE(qo.status,'new') IN ('new','pending')
                         AND qo.sent_at IS NULL
                    )
                  ) AS has_unsent,
                  (
                    EXISTS (
                      SELECT 1
                        FROM public.sessions s
                        JOIN public.order_items oi ON oi.session_id = s.id
                       WHERE s.table_number = %s
                         AND COALESCE(s.status,'') = 'active'
                         AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                         AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                         {qr_clause}
                    )
                    OR
                    EXISTS (
                      SELECT 1
                        FROM qr.qr_orders qo
                       WHERE qo.table_number = %s
                         AND COALESCE(qo.status,'new') IN ('new','pending')
                         AND qo.sent_at IS NULL
                    )
                  ) AS has_qr_unsent
                """,
                [
                    str(table_number),
                    str(table_number),
                    str(table_number),
                    *qr_params,
                    str(table_number),
                ],
            )
            row = c.fetchone()
            has_unsent = bool(row[0])
            has_qr_unsent = bool(row[1])
        return jsonify({
            "status": "ok",
            "table_number": str(table_number),
            "has_unsent": has_unsent,
            "has_qr_unsent": has_qr_unsent,
        })
    finally:
        try:
            conn.close()
        except Exception:
            pass

@bp.get("/api/floor/<floor>/unsent_flags")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def api_unsent_flags(floor):
    """
    For a given floor, return {table_number: bool has_unsent}.
    A table is "unsent" if there exists any order_items that are:
      - session is active
      - qty - void_qty > 0
      - status NOT IN ('cancelled','printed','paid')
    OR any pending QR orders for that table (status 'new'/'pending', not sent).
    Uses floor_layouts.boxes JSON to enumerate tables on the floor.
    """
    conn = db.connect_db(None)
    qr_clause, qr_params = _qr_creator_clauses("oi")
    try:
        with conn.cursor() as c:
            c.execute(
                f"""
                WITH floor_tables AS (
                  SELECT jsonb_object_keys(fl.boxes)::text AS table_number
                  FROM public.floor_layouts fl
                  WHERE fl.floor = %s
                )
                SELECT
                  ft.table_number,
                  (
                    EXISTS (
                      SELECT 1
                        FROM public.sessions s
                        JOIN public.order_items oi ON oi.session_id = s.id
                       WHERE s.table_number = ft.table_number
                         AND COALESCE(s.status,'') = 'active'
                         AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                         AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                    )
                    OR
                    EXISTS (
                      SELECT 1
                        FROM qr.qr_orders qo
                       WHERE qo.table_number = ft.table_number
                         AND COALESCE(qo.status,'new') IN ('new','pending')
                         AND qo.sent_at IS NULL
                    )
                  ) AS has_unsent,
                  (
                    EXISTS (
                      SELECT 1
                        FROM public.sessions s
                        JOIN public.order_items oi ON oi.session_id = s.id
                       WHERE s.table_number = ft.table_number
                         AND COALESCE(s.status,'') = 'active'
                         AND (COALESCE(oi.qty,0) - COALESCE(oi.void_qty,0)) > 0
                         AND COALESCE(oi.status,'') NOT IN ('cancelled','printed','paid')
                         {qr_clause}
                    )
                    OR
                    EXISTS (
                      SELECT 1
                        FROM qr.qr_orders qo
                       WHERE qo.table_number = ft.table_number
                         AND COALESCE(qo.status,'new') IN ('new','pending')
                         AND qo.sent_at IS NULL
                    )
                  ) AS has_qr_unsent
                FROM floor_tables ft
                ORDER BY
                  (ft.table_number ~ '^[0-9]+$') DESC,
                  LPAD(ft.table_number, 6, '0') ASC;
                """,
                [str(floor), *qr_params],
            )
            rows = c.fetchall()
        return jsonify(
            {
                "status": "ok",
                "floor": str(floor),
                "flags": {r[0]: bool(r[1]) for r in rows},
                "qr_flags": {r[0]: bool(r[2]) for r in rows},
            }
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass
