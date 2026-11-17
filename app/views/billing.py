from flask import Blueprint, request, render_template, jsonify, url_for, abort,current_app
from flask_login import login_required, current_user
from ..authz import roles_required
from ..helpers import pct_round_half_up, menu_unit_for_label
from utils import db
from datetime import datetime
from utils.services import printing
from utils.services.escpos_receipt import build_receipt_bytes_from_ctx
from utils.config_store import get_billing_config
from ..socketbus import broadcast, _push_state
from ..events import session_closed
from collections import OrderedDict

bp = Blueprint("billing", __name__)

def _rounding_step_idr() -> int:
    try:
        return int(get_billing_config().get("rounding_step_idr", 100))
    except Exception:
        return 100

def _ceil_to_step(n: int, step: int) -> int:
    try:
        n = int(n or 0)
    except Exception:
        n = 0
    if step <= 0:
        return n
    return ((n + step - 1) // step) * step

def _takeaway_fee_idr() -> int:
    """Flat fee for Take Away, overridable via config TAKEAWAY_FEE_IDR."""
    try:
        return int(get_billing_config().get("takeaway_fee_idr", 10000))
    except Exception:
        return 10000

def collapse_ignore_notes(lines):
    """
    Merge items by (name, unit_price), ignoring notes.
    Sums qty and line_total. Notes are discarded.
    """
    bucket = OrderedDict()
    for l in lines:
        name = (l.get("name") or "").strip()
        rate = int(l.get("unit_price") or 0)
        unit = (l.get("unit") or "").strip()
        key  = (name.lower(), rate, unit.lower())
        if key not in bucket:
            bucket[key] = {
                "name": name,
                "qty": float(l.get("qty") or 0.0),
                "unit_price": rate,
                "line_total": int(l.get("line_total") or 0),
                "note": None,   # explicitly drop notes for receipt
                "unit": unit or None,
            }
        else:
            b = bucket[key]
            b["qty"]        = float(b["qty"]) + float(l.get("qty") or 0.0)
            b["line_total"] = int(b["line_total"]) + int(l.get("line_total") or 0)
    # normalize types
    out = []
    for _, row in bucket.items():
        row["qty"] = float(row["qty"])
        row["unit_price"] = int(row["unit_price"])
        row["line_total"] = int(row["line_total"])
        out.append(row)
    return out

@bp.get("/print/preview/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def print_preview(session_id):
    # ---------- read params ----------
    raw_multi  = request.args.getlist("group")
    raw_single = request.args.get("group")
    dbg        = (request.args.get("debug") or "").strip().lower()
    aggregate  = (request.args.get("aggregate") or "").strip().lower() in ("1","true","yes","all")
    combine_sections = (request.args.get("combine") or "").strip().lower() in ("1","true","yes")
    companion_id = (request.args.get("companion") or "").strip() or None

    def _norm_one(v: object) -> str:
        if v is None: return ""
        s = str(v).strip()
        if s == "" or s.lower() in ("null", "none"): return ""
        return s

    groups: list[str] = []
    if raw_multi:
        exploded = []
        for g in raw_multi:
            exploded += [p.strip() for p in str(g).split(",")]
        groups = [_norm_one(x) for x in exploded if _norm_one(x)]
    elif raw_single:
        groups = [_norm_one(x) for x in str(raw_single).split(",") if _norm_one(x)]

    # Discounts / DP flags
    try:
        discount_percent_in = int(request.args.get("discount_percent") or 0)
    except Exception:
        discount_percent_in = 0
    try:
        discount_amount_in = int(request.args.get("discount_amount") or 0)
    except Exception:
        discount_amount_in = 0
    discount_percent_in = max(0, min(discount_percent_in, 100))
    discount_amount_in = max(discount_amount_in, 0)
    apply_dp_flag = (request.args.get("apply_dp", "0") or "0").lower() in ("1", "true", "yes", "on")
    try:
        dp_amount_in = int(request.args.get("dp_amount") or 0)
    except Exception:
        dp_amount_in = 0
    dp_amount_in = max(0, dp_amount_in)
    if dp_amount_in > 0:
        apply_dp_flag = True

    packaging_selected = (request.args.get("packaging", "0") or "0").lower() in ("1","true","yes","on")

    billing_cfg = get_billing_config()
    tax_pct_default = int(billing_cfg.get("tax_percent", 10))
    service_pct_default = int(billing_cfg.get("service_percent", 5))
    tax_on_service = bool(billing_cfg.get("tax_on_service"))

    # ---------- session lookups ----------
    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min: abort(404)
    _, table_number, _ = sess_min

    service_type_main = db.get_session_service_type(None, session_id) or "dine_in"
    printed_at_now    = datetime.now().strftime("%d-%m-%y %H:%M")

    companion_type = None
    include_companion = combine_sections or bool(request.args.get("companion"))
    if include_companion:
        try:
            if not companion_id:
                for row in db.list_active_sessions_for_table(None, table_number) or []:
                    sid_other = row.get("id")
                    st_other  = (row.get("service_type") or "dine_in")
                    if sid_other == session_id:
                        continue
                    if st_other != service_type_main:
                        companion_id = sid_other
                        companion_type = st_other
                        break
            else:
                companion_type = db.get_session_service_type(None, companion_id) or None
        except Exception:
            current_app.logger.exception("print_preview: failed to probe companion session")
    else:
        companion_id = None

    force_all = aggregate or dbg in ("1", "true", "all")

    def _grp_from_row(v) -> str:
        return _norm_one(v)

    def build_block(target_session_id, *, use_discounts=True, use_dp=False, force_all_override=None, packaging_on=None, dp_amount_override=None):
        sess = db.get_session_detail(None, target_session_id)
        if not sess: abort(404)
        pax, guest_name, _dp_amount, _note, created_at_raw, _status, *_ = sess

        conn_st = db.connect_db(None)
        c_st = conn_st.cursor()
        try:
            c_st.execute("SELECT service_type FROM public.sessions WHERE id=%s", (target_session_id,))
            row_st = c_st.fetchone()
        finally:
            conn_st.close()
        is_takeaway = bool(row_st and row_st[0] == "takeaway")
        service_pct = 0 if is_takeaway else service_pct_default
        service_type = row_st[0] if row_st and row_st[0] else "dine_in"

        raw_items = db.get_all_order_items_by_session(None, target_session_id)
        present_groups = sorted({_grp_from_row(r[9]) for r in raw_items if _grp_from_row(r[9])})
        split_active = len(present_groups) > 0

        local_force_all = force_all if force_all_override is None else force_all_override
        local_groups = groups if force_all_override is None else []

        filtered = raw_items
        if not local_force_all and local_groups:
            gset = set(local_groups)
            glower = {g.lower() for g in gset}
            want_main = ("main" in glower)

            def _matches(row) -> bool:
                g = _grp_from_row(row[9])
                if g == "" and want_main:
                    return True
                return g in gset

            filtered = [r for r in raw_items if _matches(r)]

        source_rows = raw_items if local_force_all else filtered

        lines = []
        for r in source_rows:
            status = (r[7] or "").strip().lower()
            if status == "cancelled":
                continue
            raw_qty = float(r[2])
            unit = int(r[3])
            voided = float(r[10] if len(r) > 10 and r[10] is not None else 0)
            qty_net = max(raw_qty - voided, 0.0)
            if qty_net <= 0:
                continue
            line_total = int(round(qty_net * unit))
            unit_label = None
            unit_raw = menu_unit_for_label(r[1])
            if unit_raw and unit_raw.strip().lower() == "ons":
                unit_label = "ons"
            lines.append(
                {
                    "name": r[1],
                    "qty": qty_net,
                    "unit_price": unit,
                    "line_total": line_total,
                    "note": (r[6] or None),
                    "unit": unit_label,
                }
            )

        lines = collapse_ignore_notes(lines)

        should_aggregate = local_force_all or (local_groups and len(local_groups) > 1)
        if should_aggregate:
            from collections import OrderedDict

            bucket = OrderedDict()
            for l in lines:
                key = (
                    (l["name"] or "").strip().lower(),
                    int(l["unit_price"]),
                    (l["note"] or "").strip().lower(),
                    (l.get("unit") or "").strip().lower(),
                )
                if key not in bucket:
                    bucket[key] = {
                        "name": l["name"],
                        "qty": float(l["qty"]),
                        "unit_price": int(l["unit_price"]),
                        "line_total": int(l["line_total"]),
                        "note": l["note"],
                        "unit": l.get("unit") or None,
                    }
                else:
                    b = bucket[key]
                    b["qty"] = float(b["qty"]) + float(l["qty"])
                    b["line_total"] = int(b["line_total"]) + int(l["line_total"])
            lines = list(bucket.values())

        subtotal = sum(l["line_total"] for l in lines)

        # discounts
        local_disc_amt = discount_amount_in if use_discounts else 0
        local_disc_pct = discount_percent_in if use_discounts else 0
        if local_disc_amt > 0:
            discount_amount = min(local_disc_amt, subtotal)
            discount_pct_used = int(round((discount_amount / subtotal) * 100)) if subtotal > 0 else 0
        elif local_disc_pct > 0:
            discount_pct_used = local_disc_pct
            discount_amount = pct_round_half_up(subtotal, discount_pct_used)
        else:
            discount_amount = 0
            discount_pct_used = 0

        fee = _takeaway_fee_idr()
        apply_packaging_flag = packaging_on if packaging_on is not None else packaging_selected
        packaging_fee = fee if apply_packaging_flag else 0

        after_discount = subtotal - discount_amount
        base = after_discount + packaging_fee
        service = round(base * (service_pct / 100.0))
        tax_base = base + service if tax_on_service else base
        tax = round(tax_base * (tax_pct_default / 100.0))
        gross = base + service + tax

        total_unrounded = int(gross)
        total_rounded = _ceil_to_step(total_unrounded, _rounding_step_idr())
        rounding_down = total_rounded - total_unrounded
        total = total_rounded

        dp_total = db.get_dp_amount(None, target_session_id) or 0
        dp_used = db.get_dp_used(None, target_session_id) or 0
        dp_remaining = max(dp_total - dp_used, 0)
        can_apply_dp = (not split_active) or (not should_aggregate and local_groups and len(local_groups) == 1)
        if use_dp and apply_dp_flag and can_apply_dp:
            if dp_amount_override is not None:
                dp_applied = min(dp_remaining, total, int(dp_amount_override or 0))
            else:
                dp_applied = min(dp_remaining, total)
        else:
            dp_applied = 0
        dp_remaining = dp_remaining - dp_applied

        opened_at_fmt = datetime.fromisoformat(str(created_at_raw)).strftime("%d-%m-%y %H:%M") if created_at_raw else "-"
        cashier_name = getattr(current_user, "full_name", None) or current_user.username

        if local_force_all:
            bill_label = "ALL"
        elif local_groups and len(local_groups) == 1:
            bill_label = "BILL" if local_groups[0].lower() == "main" else local_groups[0]
        elif local_groups and len(local_groups) > 1:
            bill_label = "ALL"
        else:
            bill_label = "ALL" if split_active else "BILL"

        header = {
            "table_number": table_number,
            "bill_label": bill_label,
            "pax": pax,
            "opened_at_fmt": opened_at_fmt,
            "printed_at": printed_at_now,
            "prepared_by": cashier_name,
            "guest_name": guest_name or "",
        }

        return {
            "header": header,
            "lines": lines,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "discount_percent": discount_pct_used,
            "service": service,
            "tax": tax,
            "tax_percent": tax_pct_default,
            "total": total,
            "dp_applied": dp_applied,
            "dp_remaining": dp_remaining,
            "is_final": False,
            "service_percent": service_pct,
            "packaging_fee": packaging_fee,
            "rounding_down": rounding_down,
            "service_type": service_type,
        }

    blocks = []
    # main session uses UI toggles
    blocks.append(
        build_block(
            session_id,
            use_discounts=True,
            use_dp=True,
            force_all_override=None,
            packaging_on=packaging_selected,
            dp_amount_override=(dp_amount_in if dp_amount_in > 0 else None),
        )
    )

    if companion_id:
        blocks.append(
            build_block(
                companion_id,
                use_discounts=False,
                use_dp=True,
                force_all_override=True,  # always print full companion
                packaging_on=None,
                dp_amount_override=None,
            )
        )

    # Ensure dine-in prints first
    blocks.sort(key=lambda b: (0 if (b.get("service_type") or "") != "takeaway" else 1))

    combined_totals = None
    if combine_sections and len(blocks) > 1:
        dine_blocks = [b for b in blocks if (b.get("service_type") or "") != "takeaway"]
        ta_blocks   = [b for b in blocks if (b.get("service_type") or "") == "takeaway"]

        dine_sub = sum((b.get("subtotal") or 0) - (b.get("discount_amount") or 0) for b in dine_blocks)
        dine_service = round(dine_sub * (service_pct_default / 100.0))
        ta_sub = sum((b.get("subtotal") or 0) for b in ta_blocks)
        ta_pkg = sum((b.get("packaging_fee") or 0) for b in ta_blocks)

        tax_base = dine_sub + ta_sub + ta_pkg
        if tax_on_service:
            tax_base += dine_service
        tax = round(tax_base * (tax_pct_default / 100.0))
        total = tax_base + tax

        dp_pool = sum((b.get("dp_applied") or 0) + (b.get("dp_remaining") or 0) for b in blocks)
        dp_applied = min(dp_pool, total)
        combined_totals = {
            "subtotal_dine": int(dine_sub),
            "subtotal_takeaway": int(ta_sub),
            "packaging": int(ta_pkg),
            "service": int(dine_service),
            "tax": int(tax),
            "service_percent": service_pct_default,
            "tax_percent": tax_pct_default,
            "total": int(total),
            "dp_applied": int(dp_applied),
            "after_dp": int(total - dp_applied),
        }

    primary = blocks[0]
    ctx = {
        **primary,
        "blocks": blocks,
        "combine_sections": combine_sections and len(blocks) > 1,
        "combined_totals": combined_totals,
    }
    return render_template("receipt.html", **ctx)


ALLOWED_METHODS = {"cash", "qris", "debit", "credit", "card", "transfer"}

@bp.post("/billing/mark_billing/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def mark_billing(session_id):
    conn = db.connect_db(None)
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE sessions
            SET billing_started_at = COALESCE(billing_started_at, NOW())
            WHERE id = %s AND status = 'active'
        """, (session_id,))
        affected = c.rowcount or 0
        conn.commit()
    finally:
        conn.close()

    # Optional: quick debug if nothing updated
    if affected == 0:
        # Check what the row looks like
        try:
            conn2 = db.connect_db(None); c2 = conn2.cursor()
            c2.execute("SELECT id, status, billing_started_at FROM sessions WHERE id=%s", (session_id,))
            row = c2.fetchone()
        finally:
            conn2.close()
        return jsonify({
            "status": "ok",
            "updated": 0,
            "reason": "no_match_or_not_active",
            "session_probe": (row if row else None)
        })

    # Broadcast so other dashboards flip blue in realtime
    try:
        sess_min = db.get_session_by_id(None, session_id)
        if sess_min:
            _, table_number, _ = sess_min
            svc_type = db.get_session_service_type(None, session_id) or "dine_in"
            if svc_type != "takeaway":
                from ..socketbus import broadcast
                broadcast("session_billing", {
                    "session_id": session_id,
                    "table_number": table_number,
                    "billing": True,
                    "service_type": svc_type,
                })
    except Exception:
        pass

    return jsonify({"status": "ok", "updated": affected})

@bp.post("/close_bill/<session_id>")
@login_required
@roles_required("admin", "cashier")
def close_bill(session_id):
    try:
        data = request.get_json() or {}
        group_in = data.get("group") or request.args.get("group")
        group_norm = db.normalize_group(group_in)
        apply_dp = bool(data.get("apply_dp"))
        dp_amount_raw = data.get("dp_amount", None)
        dp_amount_req = None
        dp_amount_provided = False
        if dp_amount_raw is not None and str(dp_amount_raw).strip() != "":
            try:
                dp_amount_req = int(dp_amount_raw)
            except Exception:
                return jsonify({"status": "error", "message": "invalid dp_amount"}), 400
            if dp_amount_req < 0:
                return jsonify({"status": "error", "message": "invalid dp_amount"}), 400
            dp_amount_provided = True
            if dp_amount_req > 0:
                apply_dp = True
        uid = current_user.id

        try:
            discount_percent = int(data.get("discount_percent") or 0)
        except Exception:
            discount_percent = 0
        discount_percent = max(0, min(discount_percent, 100))

        try:
            discount_amount_in = int(data.get("discount_amount") or 0)
        except Exception:
            discount_amount_in = 0
        discount_amount_in = max(discount_amount_in, 0)

        payment_method = (data.get("payment_method") or "").lower().strip()
        if payment_method not in ALLOWED_METHODS:
            return jsonify({"status": "error", "message": "invalid payment method"}), 400

        raw_card_type = (data.get("card_type") or "").strip() or None
        card_type = raw_card_type if payment_method in ("debit", "credit", "card") else None

        items = db.get_order_items_by_session(None, session_id, bill_group=group_norm)
        if not items:
            return jsonify({"status": "error", "message": "no items to close for this bill group"}), 400

        def _num(x):
            try: return float(x or 0)
            except: return 0.0

        # subtotal from NET qty (qty - void_qty)
        subtotal = 0
        for it in items:
            qty        = _num(it[2])
            unit_price = int(_num(it[3]))
            voided     = _num(it[10]) if len(it) > 10 else 0.0
            qty_net    = max(qty - voided, 0.0)
            subtotal  += int(round(qty_net * unit_price))

        if discount_amount_in > 0:
            discount_amount = min(discount_amount_in, subtotal)
            # keep percent field coherent for records (rounded to nearest int)
            discount_percent = int(round((discount_amount / subtotal) * 100)) if subtotal > 0 else 0
        else:
            discount_amount = pct_round_half_up(subtotal, discount_percent)

        after_discount = subtotal - discount_amount

        # service_type (for takeaway service=0%)
        conn_st = db.connect_db(None)
        c_st = conn_st.cursor()
        try:
            c_st.execute("SELECT service_type FROM public.sessions WHERE id=%s", (session_id,))
            row_st = c_st.fetchone()
        finally:
            conn_st.close()
        is_takeaway_session = bool(row_st and row_st[0] == "takeaway")
        billing_cfg = get_billing_config()
        service_pct_default = int(billing_cfg.get("service_percent", 5))
        tax_pct_default = int(billing_cfg.get("tax_percent", 10))
        tax_on_service = bool(billing_cfg.get("tax_on_service"))
        service_pct = 0 if (row_st and row_st[0] == "takeaway") else service_pct_default

        fee = _takeaway_fee_idr()

        # Take Away + Dine-in: optional manual packaging fee
        apply_packaging_fee = bool(data.get("apply_packaging_fee"))
        packaging_fee = fee if apply_packaging_fee else 0

        base = after_discount + packaging_fee

        service = pct_round_half_up(base, service_pct)
        tax_base = base + service if tax_on_service else base
        tax     = pct_round_half_up(tax_base, tax_pct_default)
        gross   = base + service + tax

        dp_total       = db.get_dp_amount(None, session_id) or 0
        dp_used        = db.get_dp_used(None, session_id) or 0
        dp_remaining   = max(int(dp_total) - int(dp_used), 0)
        if apply_dp:
            if dp_amount_provided:
                dp_applied_now = min(dp_remaining, gross, int(dp_amount_req or 0))
            else:
                dp_applied_now = min(dp_remaining, gross)
        else:
            dp_applied_now = 0

        final_amount_raw = gross - dp_applied_now
        final_amount = _ceil_to_step(final_amount_raw, _rounding_step_idr())
        rounding_down = final_amount - final_amount_raw  # positive diff due to rounding

        change_given = 0
        cash_received = None
        if payment_method == "cash":
            try:
                cash_received = int(data.get("cash_received"))
            except Exception:
                return jsonify({"status": "error", "message": "invalid cash amount"}), 400
            if cash_received < final_amount:
                return jsonify({"status": "error", "message": "insufficient cash"}), 400
            change_given = cash_received - final_amount

        paid_at = datetime.now().isoformat(timespec="seconds")

        payment_id = db.insert_payment(
            None,
            session_id=session_id,
            amount=final_amount,
            method=payment_method,
            paid_at=paid_at,
            cash_received=cash_received,
            change_given=change_given,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            tax=tax,
            service=service,
            total_before_discount=subtotal + packaging_fee,
            card_type=card_type,
            bill_group=group_norm,
            created_by_user_id=uid,
            dp_applied_amount=dp_applied_now,
            is_dp=False,  
        )

        if not payment_id:
            return jsonify({"status": "error", "message": "payment insert failed"}), 500

        db.mark_items_paid(None, session_id, bill_group=group_norm)
        _push_state(session_id)

        fully_paid = db.session_is_fully_paid(None, session_id)
        if fully_paid:
            db.close_session(None, session_id, closed_by_user_id=uid)
            sess_min = db.get_session_by_id(None, session_id)
            if sess_min:
                _, table_number_closed, _ = sess_min
                if not is_takeaway_session:
                    session_closed(table_number_closed, session_id)
            _push_state(session_id)

            # NEW: mirror to reservations
            try:
                from utils.data.core import connect_db
                with connect_db() as conn, conn.cursor() as c:
                    c.execute("""
                        UPDATE public.reservations
                           SET status='finished'
                         WHERE session_id=%s
                           AND COALESCE(status,'') <> 'cancelled'
                    """, (session_id,))
                    conn.commit()
                if sess_min:
                    from app.socketbus import push_reservation_changed
                    push_reservation_changed(table_number_closed, None)
            except Exception:
                current_app.logger.exception("close_bill: failed to mark reservation finished")

        print_url = url_for(
            "billing.print_final_receipt",
            session_id=session_id,
            group=(group_norm or "main"),
            payment_id=payment_id,
            _external=False
        )
        return jsonify({"status": "success", "fully_paid": fully_paid, "payment_id": payment_id, "print_url": print_url})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.get("/receipt/final/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def print_final_receipt(session_id):
    from datetime import datetime
    from flask import abort

    # 1) Start from querystring group, normalize it
    group_in   = request.args.get("group", "main")
    group_norm = db.normalize_group(group_in)  # <-- use your db helper

    payment_id = request.args.get("payment_id", type=int)
    if not payment_id:
        abort(400, "payment_id required")

    # 2) Load payment, then override group from payment if set
    pay = db.get_payment(None, payment_id)
    if not pay:
        abort(404, "payment not found")

    if pay.get("bill_group") is not None:
        group_norm = db.normalize_group(pay.get("bill_group"))

    # 3) Load session header
    header_db = db.get_session_header(session_id)
    if not header_db:
        abort(404, "session not found")

    # --- Build NET itemized lines from order_items (qty - void_qty) ---
    items = db.get_order_items_by_session(None, session_id, bill_group=group_norm) or []

    def _f(x):
        try: return float(x or 0)
        except: return 0.0

    def _i(x):
        try: return int(x or 0)
        except: return 0

    raw_lines = []
    for it in items:
        # tuple:
        # 0 id, 1 item_name, 2 qty, 3 price, 4 total_price, 5 sauce, 6 note,
        # 7 status, 8 timestamp, 9 bill_group, 10 void_qty
        name = (it[1] or '').strip()
        qty  = _f(it[2])
        rate = _i(it[3])
        note = (it[6] or None)
        void = _f(it[10]) if len(it) > 10 else 0.0

        qty_net = max(qty - void, 0.0)
        if qty_net <= 0:
            continue

        unit_label = None
        unit_raw = menu_unit_for_label(name)
        if unit_raw and unit_raw.strip().lower() == "ons":
            unit_label = "ons"
        raw_lines.append({
            "name":       name,
            "qty":        qty_net,
            "unit_price": rate,
            "line_total": int(round(qty_net * rate)),
            "note":       note,
            "unit":       unit_label,
        })

    # Collapse by (name, unit_price), ignore notes for the printed receipt
    net_lines = collapse_ignore_notes(raw_lines)

    # --- Totals from recorded payment ---
    subtotal         = int(pay.get("total_before_discount") or 0)
    discount_amount  = int(pay.get("discount_amount") or 0)
    discount_percent = int(pay.get("discount_percent") or 0)
    service          = int(pay.get("service") or 0)
    tax              = int(pay.get("tax") or 0)
    dp_applied       = int(pay.get("dp_applied_amount") or 0)

    # "total" shown on the receipt as gross actually collected (net + DP used)
    total            = int(pay.get("amount") or 0) + dp_applied

    try:
        paid_at_dt = datetime.fromisoformat(str(pay["paid_at"]))
    except Exception:
        paid_at_dt = datetime.now()

    printed_at   = datetime.now().strftime("%d-%m-%y %H:%M")
    cashier_name = getattr(current_user, "full_name", None) or current_user.username

    def payment_label(method, card_type):
        names = {"cash": "Cash", "qris": "QRIS", "debit": "Debit", "credit": "Credit", "card": "Card", "transfer": "Transfer"}
        base = names.get((method or "").lower(), (method or ""))
        if (method in ("debit", "credit", "card")) and card_type:
            base = f"{base} ({card_type})"
        return base

    # Label: "BILL" for main; group label for split; "ALL" otherwise
    if not group_norm or group_norm.lower() in ("main", "null", "none", ""):
        bill_label = "BILL"
    else:
        bill_label = group_norm or "ALL"

    # items net total (without fee)
    items_subtotal = sum(int(l["line_total"]) for l in net_lines)
    # payment subtotal already includes fee
    packaging_fee = max(subtotal - items_subtotal, 0)

    calculated_gross = (subtotal - discount_amount) + service + tax
    total = int(pay.get("amount") or 0) + int(pay.get("dp_applied_amount") or 0)  
    rounding_down = max(total - calculated_gross, 0)

    ctx = {
        "title": "Paid Bill",
        "is_final": True,
        "header": {
            "table_number": header_db.get("table_number"),
            "bill_label": bill_label,
            "pax": header_db.get("pax"),
            "opened_at_fmt": datetime.fromisoformat(str(header_db["opened_at"])).strftime("%d-%m-%y %H:%M") if header_db.get("opened_at") else "-",
            "printed_at": printed_at,
            "closed_at_fmt": paid_at_dt.strftime("%d-%m-%y %H:%M"),
            "prepared_by": cashier_name,
            "guest_name": header_db.get("guest_name"),
        },
        "lines": net_lines,
        "subtotal": subtotal,
        "packaging_fee": packaging_fee,
        "discount_amount": discount_amount,
        "discount_percent": discount_percent,
        "service": service,
        "tax": tax,
        "total": total,
        "dp_applied": dp_applied,
        "dp_remaining": db.get_dp_remaining_after(session_id, up_to_payment_id=payment_id),
        "payment": {
            "method_label": payment_label(pay.get("method"), pay.get("card_type")),
            "paid_amount": int(pay.get("cash_received") or (pay.get("amount") or 0)),
            "change": int(pay.get("change_given") or 0),
        },
        "rounding_down": rounding_down,          
    }

    autoprint = (request.args.get("autoprint") or "").lower() in ("1","true","yes")
    return render_template("receipt.html", autoprint=autoprint, **ctx)

@bp.get("/admin/transactions")
@login_required
@roles_required("admin", "cashier")
def transactions_page():
    return render_template("transactions.html", active_tab="transactions")

def _collapse_ignore_notes(raw_lines):
    """Merge identical items by (name, unit_price), ignore note when printing."""
    merged = {}
    for l in raw_lines:
        unit = (l.get("unit") or "").strip()
        key = (l["name"], l["unit_price"], unit)
        if key not in merged:
            merged[key] = {
                "name": l["name"],
                "qty": 0.0,
                "unit_price": l["unit_price"],
                "line_total": 0,
                "unit": unit or None,
            }
        merged[key]["qty"] += float(l["qty"] or 0)
        merged[key]["line_total"] = int(round(merged[key]["qty"] * merged[key]["unit_price"]))
    # keep input order stable-ish
    return [ {**v} for _, v in merged.items() ]

def _user_display_name(user_id):
    if not user_id:
        return None
    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(NULLIF(TRIM(full_name),''), username) FROM public.users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        return (row[0] if row else None)
    finally:
        conn.close()

def _payment_label(method, card_type):
    names = {"cash":"Cash","qris":"QRIS","debit":"Debit","credit":"Credit","card":"Card","transfer":"Transfer"}
    base  = names.get((method or "").lower(), (method or ""))
    if (method in ("debit","credit","card")) and card_type:
        base = f"{base} ({card_type})"
    return base

@bp.get("/receipt/reprint/<int:payment_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def reprint_final_receipt(payment_id: int):
    # --- Load the authoritative payment row ---
    pay = db.get_payment(None, payment_id)
    if not pay:
        abort(404, "payment not found")

    session_id = pay.get("session_id")
    if not session_id:
        abort(400, "payment has no session_id")

    group_norm = db.normalize_group(pay.get("bill_group") or "main")

    # --- Header / session basics ---
    header_db = db.get_session_header(session_id)
    if not header_db:
        abort(404, "session not found")

    # --- Pull order_items (skip cancelled; use qty - void_qty) ---
    conn = db.connect_db(None)
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT item_name, qty, price, note, COALESCE(void_qty, 0) AS void_qty, status
            FROM public.order_items
            WHERE session_id = %s
            AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main')
                = COALESCE(NULLIF(TRIM(%s), ''), 'main')   -- <<< coalesce RHS too
            AND status <> 'cancelled'
        """, (session_id, group_norm))
        rows = cur.fetchall()
    finally:
        conn.close()

    def _f(x):
        try: return float(x or 0)
        except: return 0.0
    def _i(x):
        try: return int(x or 0)
        except: return 0

    raw_lines = []
    for name, qty, price, note, void_qty, status in rows:
        qty_net = max(_f(qty) - _f(void_qty), 0.0)
        if qty_net <= 0:
            continue
        rate = _i(price)
        unit_label = None
        unit_raw = menu_unit_for_label(name)
        if unit_raw and unit_raw.strip().lower() == "ons":
            unit_label = "ons"
        raw_lines.append({
            "name": name.strip() if name else "",
            "qty": qty_net,
            "unit_price": rate,
            "line_total": int(round(qty_net * rate)),
            "note": note or None,
            "unit": unit_label,
        })

    # collapse by (name, unit_price) for printing
    net_lines = _collapse_ignore_notes(raw_lines)

    # --- Totals come from the recorded payment (authoritative) ---
    subtotal         = int(pay.get("total_before_discount") or 0)
    discount_amount  = int(pay.get("discount_amount") or 0)
    discount_percent = int(pay.get("discount_percent") or 0)
    service          = int(pay.get("service") or 0)
    tax              = int(pay.get("tax") or 0)
    total            = int(pay.get("amount") or 0) + int(pay.get("dp_applied_amount") or 0)
    dp_applied       = int(pay.get("dp_applied_amount") or 0)

    calculated_gross = (subtotal - discount_amount) + service + tax
    rounding_down = max(total - calculated_gross, 0)

    # DP remaining at the time of this payment (if you have this helper)
    dp_remaining = db.get_dp_remaining_after(session_id, up_to_payment_id=payment_id)

    # Printed/closed timestamps & cashier
    try:
        paid_at_dt = datetime.fromisoformat(str(pay["paid_at"]))
    except Exception:
        paid_at_dt = datetime.now()
    printed_at   = datetime.now().strftime("%d-%m-%y %H:%M")

    # Prefer the ORIGINAL cashier from payment row; fallback to current_user
    cashier_name = (
        _user_display_name(pay.get("created_by_user_id")) or
        getattr(current_user, "full_name", None) or
        current_user.username
    )

    # Label: "BILL" for main; otherwise group label
    bill_label = "BILL" if not group_norm or group_norm.lower() in ("main","null","none","") else group_norm

    items_subtotal = sum(int(l["line_total"]) for l in net_lines)
    packaging_fee = max(subtotal - items_subtotal, 0)

    ctx = {
        "title": "Paid Bill",
        "is_final": True,
        "header": {
            "table_number": header_db["table_number"],
            "bill_label": bill_label,
            "pax": header_db["pax"],
            "opened_at_fmt": datetime.fromisoformat(str(header_db["opened_at"])).strftime("%d-%m-%y %H:%M") if header_db.get("opened_at") else "-",
            "printed_at": printed_at,
            "closed_at_fmt": paid_at_dt.strftime("%d-%m-%y %H:%M"),
            "prepared_by": cashier_name,
            "guest_name": header_db["guest_name"],
        },
        "lines": net_lines,
        "subtotal": subtotal,
        "packaging_fee": packaging_fee,
        "discount_amount": discount_amount,
        "discount_percent": discount_percent,
        "service": service,
        "tax": tax,
        "total": total,
        "dp_applied": dp_applied,
        "dp_remaining": dp_remaining,
        "payment": {
            "method_label": _payment_label(pay.get("method"), pay.get("card_type")),
            "paid_amount": int(pay.get("cash_received") or (pay.get("amount") or 0)),
            "change": int(pay.get("change_given") or 0),
        },
        "rounding_down": rounding_down,
    }

    autoprint = (request.args.get("autoprint") or "").lower() in ("1","true","yes")
    return render_template("receipt.html", autoprint=autoprint, **ctx)


@bp.get("/api/print/paid_hex/<int:payment_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_paid_receipt_hex(payment_id: int):
    pay = db.get_payment(None, payment_id)
    if not pay:
        return jsonify({"status": "error", "message": "payment not found"}), 404

    session_id = pay.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "payment has no session"}), 400

    group_norm = db.normalize_group(pay.get("bill_group") or "main")

    header_db = db.get_session_header(session_id)
    if not header_db:
        return jsonify({"status": "error", "message": "session not found"}), 404

    conn = db.connect_db(None)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT item_name, qty, price, note, COALESCE(void_qty, 0) AS void_qty, status
            FROM public.order_items
            WHERE session_id = %s
            AND COALESCE(NULLIF(TRIM(bill_group), ''), 'main')
                = COALESCE(NULLIF(TRIM(%s), ''), 'main')
            AND status <> 'cancelled'
        """, (session_id, group_norm))
        rows = cur.fetchall()
    finally:
        conn.close()

    def _f(x):
        try:
            return float(x or 0)
        except Exception:
            return 0.0

    def _i(x):
        try:
            return int(x or 0)
        except Exception:
            return 0

    raw_lines = []
    for name, qty, price, note, void_qty, _status in rows:
        qty_net = max(_f(qty) - _f(void_qty), 0.0)
        if qty_net <= 0:
            continue
        rate = _i(price)
        unit_label = None
        unit_raw = menu_unit_for_label(name)
        if unit_raw and unit_raw.strip().lower() == "ons":
            unit_label = "ons"
        raw_lines.append({
            "name": (name or "").strip(),
            "qty": qty_net,
            "unit_price": rate,
            "line_total": int(round(qty_net * rate)),
            "note": note or None,
            "unit": unit_label,
        })

    net_lines = _collapse_ignore_notes(raw_lines)

    subtotal = int(pay.get("total_before_discount") or 0)
    discount_amount = int(pay.get("discount_amount") or 0)
    discount_percent = int(pay.get("discount_percent") or 0)
    service = int(pay.get("service") or 0)
    tax = int(pay.get("tax") or 0)
    total = int(pay.get("amount") or 0) + int(pay.get("dp_applied_amount") or 0)
    dp_applied = int(pay.get("dp_applied_amount") or 0)

    calculated_gross = (subtotal - discount_amount) + service + tax
    rounding_down = max(total - calculated_gross, 0)

    dp_remaining = db.get_dp_remaining_after(session_id, up_to_payment_id=payment_id)

    try:
        paid_at_dt = datetime.fromisoformat(str(pay["paid_at"]))
    except Exception:
        paid_at_dt = datetime.now()
    printed_at = datetime.now().strftime("%d-%m-%y %H:%M")

    cashier_name = (
        _user_display_name(pay.get("created_by_user_id")) or
        getattr(current_user, "full_name", None) or
        current_user.username
    )

    bill_label = "BILL" if not group_norm or group_norm.lower() in ("main", "null", "none", "") else group_norm

    items_subtotal = sum(int(l["line_total"]) for l in net_lines)
    packaging_fee = max(subtotal - items_subtotal, 0)

    ctx = {
        "title": "Paid Bill",
        "is_final": True,
        "header": {
            "table_number": header_db["table_number"],
            "bill_label": bill_label,
            "pax": header_db["pax"],
            "opened_at_fmt": datetime.fromisoformat(str(header_db["opened_at"])).strftime("%d-%m-%y %H:%M") if header_db.get("opened_at") else "-",
            "printed_at": printed_at,
            "closed_at_fmt": paid_at_dt.strftime("%d-%m-%y %H:%M"),
            "prepared_by": cashier_name,
            "guest_name": header_db["guest_name"],
        },
        "lines": net_lines,
        "subtotal": subtotal,
        "packaging_fee": packaging_fee,
        "discount_amount": discount_amount,
        "discount_percent": discount_percent,
        "service": service,
        "tax": tax,
        "total": total,
        "dp_applied": dp_applied,
        "dp_remaining": dp_remaining,
        "payment": {
            "method_label": _payment_label(pay.get("method"), pay.get("card_type")),
            "paid_amount": int(pay.get("cash_received") or (pay.get("amount") or 0)),
            "change": int(pay.get("change_given") or 0),
        },
        "rounding_down": rounding_down,
    }

    payload = build_receipt_bytes_from_ctx(ctx)
    return jsonify({"status": "ok", "hex": payload.hex()})
