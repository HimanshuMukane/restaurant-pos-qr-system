from flask import Blueprint, render_template, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from utils import db
from ..socketbus import broadcast, _push_state
from datetime import datetime
import secrets

bp = Blueprint("takeaway", __name__, url_prefix="/takeaway")

def new_session_id():
    return datetime.utcnow().strftime("S%y%m%d%H%M%S") + "-" + secrets.token_hex(2)

@bp.get("/", strict_slashes=False)
@login_required
def index():
    conn = db.connect_db(None)
    c = conn.cursor()

    c.execute("""
        SELECT
            s.id,
            s.guest_name,
            s.pickup_time,
            s.note,
            s.created_at,
            COALESCE(sum_net.total, 0)::int AS total,
            COALESCE(s.dp_amount, 0)::int AS dp_amount,
            COALESCE(s.dp_method, '')::text AS dp_method
        FROM public.sessions s
        LEFT JOIN LATERAL (
            SELECT SUM((GREATEST(oi.qty - COALESCE(oi.void_qty,0),0) * oi.price)::int) AS total
            FROM order_items oi
            WHERE oi.session_id = s.id AND oi.status != 'cancelled'
        ) AS sum_net ON TRUE
        WHERE s.service_type = 'takeaway' AND s.closed_at IS NULL
        ORDER BY COALESCE(s.pickup_time, s.created_at)
    """)

    rows = [{
        "id": _id,
        "guest_name": guest_name,
        "pickup_time": pickup_time,
        "note": note,
        "created_at": created_at,
        "total": int(total or 0),
        "dp_amount": int(dp_amount or 0),
        "dp_method": dp_method,
    } for _id, guest_name, pickup_time, note, created_at, total, dp_amount, dp_method in c.fetchall()]

    conn.close()
    return render_template("takeaway_list.html", rows=rows)



@bp.post("/", strict_slashes=False)
@login_required
def create():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    if not name:
        abort(400, "name required")

    pickup_time = data.get("pickup_time") or None
    notes = data.get("notes") or None

    # NEW: DP amount + method
    dp_raw = data.get("dp_amount")
    try:
        dp_amount = int(dp_raw) if dp_raw not in (None, "", "null") else 0
    except (ValueError, TypeError):
        dp_amount = 0

    dp_method = (data.get("dp_method") or "").strip() or None
    if dp_amount < 0:
        abort(400, "invalid DP amount")
    if dp_amount > 0 and not dp_method:
        abort(400, "dp_method required when DP > 0")

    sid = new_session_id()

    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO public.sessions
                (id, pax, table_number, created_at,
                 guest_name, note, status,
                 service_type, pickup_time, opened_by_user_id,
                 dp_amount, dp_method, dp_paid_at)
            VALUES
                (%s, 1, 'TA', NOW(),
                 %s, %s, 'active',
                 'takeaway', %s, %s,
                 %s, %s, CASE WHEN %s > 0 THEN NOW() ELSE NULL END)
        """, (
            sid,
            name,
            notes,
            pickup_time,
            getattr(current_user, "id", None),
            dp_amount,
            dp_method,
            dp_amount,  # used in CASE WHEN %s > 0
        ))

        # NEW: record DP as a payment row
        if dp_amount > 0:
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
                    sid,
                    dp_amount,
                    dp_method,
                    dp_amount,
                    getattr(current_user, "id", None),
                ),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        abort(500, "failed to create takeaway session")
    conn.close()

    broadcast("takeaway:list_changed", {"id": sid, "op": "create"})
    return jsonify({"id": sid}), 201


@bp.patch("/<sid>")
@login_required
def update(sid):
    data = request.get_json(silent=True) or {}

    # Basic fields
    name        = (data.get("name") or "").strip() or None
    pickup_time = data.get("pickup_time") or None   # ISO string or None
    notes       = data.get("notes") or None

    # DP amount
    dp_raw = data.get("dp_amount")
    dp_amount = None
    if dp_raw is not None:
        try:
            dp_amount = int(dp_raw)
        except (ValueError, TypeError):
            abort(400, "invalid DP amount")

    # DP method (optional; will be required if DP > 0)
    dp_method = (data.get("dp_method") or "").strip() or None

    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        # Lock current session row and get existing DP info
        c.execute(
            """
            SELECT dp_amount, dp_method
              FROM public.sessions
             WHERE id=%s AND service_type='takeaway' AND closed_at IS NULL
            FOR UPDATE
            """,
            (sid,),
        )
        row = c.fetchone()
        if not row:
            conn.rollback()
            conn.close()
            abort(404, "takeaway not found")

        old_dp, old_method = row
        old_dp = int(old_dp or 0)

        # Decide new DP values
        if dp_amount is None:
            # No DP field in payload: keep existing
            new_dp_amount = old_dp
            new_dp_method = old_method
        else:
            new_dp_amount = dp_amount
            new_dp_method = dp_method

        # Validation
        if new_dp_amount < 0:
            conn.rollback()
            conn.close()
            abort(400, "invalid DP amount")

        if new_dp_amount > 0 and not new_dp_method:
            conn.rollback()
            conn.close()
            abort(400, "dp_method required when DP > 0")

        # Update session row
        c.execute(
            """
            UPDATE public.sessions
               SET guest_name  = COALESCE(%s, guest_name),
                   pickup_time = %s,
                   note        = %s,
                   dp_amount   = %s,
                   dp_method   = %s,
                   dp_paid_at  = CASE
                                   WHEN %s > 0 THEN COALESCE(dp_paid_at, NOW())
                                   ELSE NULL
                                 END
             WHERE id=%s AND service_type='takeaway'
            """,
            (
                name,
                pickup_time,
                notes,
                new_dp_amount,
                new_dp_method,
                new_dp_amount,
                sid,
            ),
        )

        # If we JUST added DP (previously 0), insert a DP payment row
        if old_dp <= 0 and new_dp_amount > 0:
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
                    sid,
                    new_dp_amount,
                    new_dp_method,
                    new_dp_amount,
                    getattr(current_user, "id", None),
                ),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        abort(500, "failed to update takeaway")
    conn.close()

    broadcast("takeaway:list_changed", {"id": sid, "op": "update"})
    return jsonify({"ok": True})


@bp.post("/close/<sid>")
@login_required
def close(sid):
    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE public.sessions
               SET closed_at = NOW(), status='closed'
             WHERE id=%s AND service_type='takeaway' AND closed_at IS NULL
        """, (sid,))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        abort(500, "failed to close takeaway")
    conn.close()

    broadcast("takeaway:list_changed", {"id": sid, "op": "close"})
    return jsonify({"ok": True})
