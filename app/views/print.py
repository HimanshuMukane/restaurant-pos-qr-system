import io
import json
import os
import time
from utils.services.raw_escpos import is_drink
from collections import OrderedDict
from datetime import datetime

from flask import (
    Blueprint, Response, render_template, render_template_string,
    request, jsonify, abort, current_app
)
from flask_login import login_required, current_user
from decimal import Decimal
from numbers import Number
from ..authz import roles_required
from ..helpers import (
    qr_bytes, qr_png_b64, station_for_item, fmt_now, find_category_for_item,
    split_item_and_dish, printer_override_for_label, pct_round_half_up,
    build_qr_order_url, get_qr_session_mode, menu_unit_for_label
)
from utils import db
from utils.services.escpos_receipt import build_receipt_bytes_from_ctx
from utils.services.escpos_checker import build_checker_bytes, build_admin_checker_bytes
from utils.services.escpos_qr import build_qr_ticket_bytes
from utils.services.raw_escpos import build_kitchen_ticket
from utils.services import printing
from utils.data.splits import normalize_group, split_meta_map
from ..events import session_items_changed
from urllib.parse import urlencode
from ..socketbus import _push_state
from utils.config_store import get_billing_config

bp =  Blueprint("print", __name__)

# ---------- Backend switch ----------

PER_ITEM_SPEC = os.getenv("PER_ITEM_STATIONS", "*,-expediter")

def _parse_per_item_spec(spec: str):
    toks = [t.strip().lower() for t in (spec or "").split(",") if t.strip()]
    all_flag  = any(t == "*" for t in toks)
    excludes  = {t[1:] for t in toks if t.startswith(("-", "!")) and len(t) > 1}
    includes  = {t for t in toks if t not in ("*",) and not t.startswith(("-", "!"))}
    return all_flag, includes, excludes

_PERITEM_ALL, _PERITEM_INCL, _PERITEM_EXCL = _parse_per_item_spec(PER_ITEM_SPEC)

def is_per_item_station(station: str) -> bool:
    s = (station or "").strip().lower()
    if not s:
        return False
    if _PERITEM_ALL:
        # all stations, except explicit exclusions
        return s not in _PERITEM_EXCL
    # otherwise, only explicit inclusions
    return s in _PERITEM_INCL

def _backend_value() -> str:
    v = (os.getenv("PRINT_BACKEND", "") or "").strip().lower()
    if v:
        return v
    try:
        v = (current_app.config.get("PRINT_BACKEND") or "").strip().lower()
    except Exception:
        v = ""
    return v


def _mock_on() -> bool:
    return _backend_value() == "mock" or (os.getenv("MOCK_PRINTING") == "1")

def _raw_on() -> bool:
    return _backend_value() == "raw"

def _demo_mode() -> bool:
    try:
        return bool(current_app.config.get("DEMO_MODE"))
    except Exception:
        return False


try:
    from utils.services.raw_escpos import print_kitchen_raw
except Exception:
    print_kitchen_raw = None


def _raw_enabled() -> bool:
    if _mock_on():
        return False
    on = bool(_raw_on() and print_kitchen_raw is not None)
    if _raw_on() and print_kitchen_raw is None:
        current_app.logger.error(
            "[PRINT] PRINT_BACKEND=raw, but utils.services.raw_escpos could not be imported. "
            "Falling back to HTML->CUPS path."
        )
    try:
        current_app.logger.info(
            "[PRINT] backend=%s mock=%s raw_enabled=%s",
            _backend_value(), _mock_on(), on
        )
    except Exception:
        pass
    return on


    
# ---------- ESC/POS receipt hex ----------
def _takeaway_fee_idr() -> int:
    try:
        return int(get_billing_config().get("takeaway_fee_idr", 10000))
    except Exception:
        return 10000


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


def _norm_group(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s == "" or s.lower() in ("null", "none"):
        return ""
    return s


def _parse_groups() -> list[str]:
    raw_multi = request.args.getlist("group")
    raw_single = request.args.get("group")
    parts = []
    if raw_multi:
        for g in raw_multi:
            parts.extend(str(g).split(","))
    elif raw_single:
        parts.extend(str(raw_single).split(","))
    return [_norm_group(p) for p in parts if _norm_group(p)]


def _build_receipt_hex(session_id: str) -> str:
    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        raise ValueError("session_not_found")
    _, table_number, _ = sess_min

    groups = _parse_groups()
    aggregate = (request.args.get("aggregate") or "").strip().lower() in ("1", "true", "yes", "all")
    if any(g.lower() in ("all", "semua") for g in groups):
        aggregate = True

    combine_sections = (request.args.get("combine") or "").strip().lower() in ("1", "true", "yes")
    companion_id = (request.args.get("companion") or "").strip() or None

    try:
        discount_percent_in = int(request.args.get("discount_percent") or 0)
    except Exception:
        discount_percent_in = 0
    try:
        discount_amount_in = int(request.args.get("discount_amount") or 0)
    except Exception:
        discount_amount_in = 0
    discount_percent_in = max(0, min(discount_percent_in, 100))
    discount_amount_in = max(0, discount_amount_in)
    apply_dp_flag = (request.args.get("apply_dp", "0") or "0").lower() in ("1", "true", "yes", "on")
    try:
        dp_amount_in = int(request.args.get("dp_amount") or 0)
    except Exception:
        dp_amount_in = 0
    dp_amount_in = max(0, dp_amount_in)
    if dp_amount_in > 0:
        apply_dp_flag = True
    packaging_selected = (request.args.get("packaging") or "0").strip().lower() in ("1", "true", "yes", "on")

    billing_cfg = get_billing_config()
    tax_pct_default = int(billing_cfg.get("tax_percent", 10))
    service_pct_default = int(billing_cfg.get("service_percent", 5))
    tax_on_service = bool(billing_cfg.get("tax_on_service"))

    printed_at_now = datetime.now().strftime("%d-%m-%y %H:%M")
    cashier_name = getattr(current_user, "full_name", None) or current_user.username

    service_type_main = db.get_session_service_type(None, session_id) or "dine_in"

    include_companion = combine_sections or bool(request.args.get("companion"))
    if include_companion:
        try:
            if not companion_id:
                for row in db.list_active_sessions_for_table(None, table_number) or []:
                    sid_other = row.get("id")
                    st_other = (row.get("service_type") or "dine_in")
                    if sid_other == session_id:
                        continue
                    if st_other != service_type_main:
                        companion_id = sid_other
                        break
        except Exception:
            pass
    else:
        companion_id = None

    force_all = aggregate

    def _grp_from_row(v) -> str:
        return _norm_group(v)

    def collapse_ignore_notes(lines):
        bucket = OrderedDict()
        for l in lines:
            name = (l.get("name") or "").strip()
            rate = int(l.get("unit_price") or 0)
            unit = (l.get("unit") or "").strip()
            key = (name.lower(), rate, unit.lower())
            if key not in bucket:
                bucket[key] = {
                    "name": name,
                    "qty": float(l.get("qty") or 0.0),
                    "unit_price": rate,
                    "line_total": int(l.get("line_total") or 0),
                    "note": None,
                    "unit": unit or None,
                }
            else:
                b = bucket[key]
                b["qty"] = float(b["qty"]) + float(l.get("qty") or 0.0)
                b["line_total"] = int(b["line_total"]) + int(l.get("line_total") or 0)
        out = []
        for _, row in bucket.items():
            row["qty"] = float(row["qty"])
            row["unit_price"] = int(row["unit_price"])
            row["line_total"] = int(row["line_total"])
            out.append(row)
        return out

    def build_block(target_session_id, *, use_discounts=True, use_dp=False, force_all_override=None, packaging_on=None, dp_amount_override=None):
        sess = db.get_session_detail(None, target_session_id)
        if not sess:
            raise ValueError("session_not_found")
        pax, guest_name, _dp_amount, _note, created_at_raw, _status, _closed_at = sess

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
            raw_qty = float(r[2] or 0)
            unit = int(r[3] or 0)
            voided = float(r[10] if len(r) > 10 and r[10] is not None else 0)
            qty_net = max(raw_qty - voided, 0.0)
            if qty_net <= 0:
                continue
            line_total = int(round(qty_net * unit))
            unit_label = None
            unit_raw = menu_unit_for_label(r[1])
            if unit_raw and unit_raw.strip().lower() == "ons":
                unit_label = "ons"
            lines.append({
                "name": r[1],
                "qty": qty_net,
                "unit_price": unit,
                "line_total": line_total,
                "note": (r[6] or None),
                "unit": unit_label,
            })

        lines = collapse_ignore_notes(lines)

        should_aggregate = local_force_all or (local_groups and len(local_groups) > 1)
        if should_aggregate:
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

        try:
            opened_at_fmt = datetime.fromisoformat(str(created_at_raw)).strftime("%d-%m-%y %H:%M")
        except Exception:
            try:
                opened_at_fmt = created_at_raw.strftime("%d-%m-%y %H:%M")
            except Exception:
                opened_at_fmt = "-"

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
                force_all_override=True,
                packaging_on=None,
                dp_amount_override=None,
            )
        )

    if not any(b.get("lines") for b in blocks):
        raise ValueError("no_items")

    blocks.sort(key=lambda b: (0 if (b.get("service_type") or "") != "takeaway" else 1))

    combined_totals = None
    if combine_sections and len(blocks) > 1:
        dine_blocks = [b for b in blocks if (b.get("service_type") or "") != "takeaway"]
        ta_blocks = [b for b in blocks if (b.get("service_type") or "") == "takeaway"]

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
        "is_final": False,
    }

    payload = build_receipt_bytes_from_ctx(ctx)
    return payload.hex()


@bp.get("/api/print/get-hex/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_print_hex(session_id):
    try:
        hex_payload = _build_receipt_hex(session_id)
    except ValueError as e:
        code = str(e)
        if code == "session_not_found":
            return jsonify({"status": "error", "message": "session not found"}), 404
        if code == "no_items":
            return jsonify({"status": "error", "message": "no items to print"}), 400
        return jsonify({"status": "error", "message": "failed to build receipt"}), 500
    return jsonify({"status": "ok", "hex": hex_payload})


def _build_kitchen_hex(session_id: str, ids=None, *, title: str, is_void: bool):
    ids = ids or []
    rows = db.get_printables(None, session_id)
    if ids:
        try:
            with db.connect_db(None) as conn, conn.cursor() as c:
                c.execute("""
                    SELECT id, item_name, qty, NULL as price, sauce, note, status, bill_group
                      FROM order_items
                     WHERE session_id = %s
                       AND id = ANY(%s)
                       AND status IN ('new','edited')
                     ORDER BY "timestamp", id
                """, (session_id, ids))
                rows = c.fetchall() or []
        except Exception:
            pass

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        raise ValueError("session_not_found")
    _sid, table_number, _ = sess_min

    meta = _session_meta_for_checker(session_id)
    cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
    split_map = _split_map_for_session(session_id)
    split_label = _split_label_from_rows(rows, split_map)
    header = _build_kitchen_header(
        meta,
        table_number,
        title=title,
        is_void=is_void,
        split_label=split_label,
        prepared_by=cashier_name,
        printed_at=f"Dicetak: {fmt_now()}",
    )

    items = []
    for r in (rows or []):
        try:
            name = (r[1] or "").strip()
            qty = float(r[2] or 0)
            note = (r[5] if len(r) > 5 else "") or ""
        except Exception:
            continue
        if not name or qty == 0:
            continue
        items.append({"name": name, "qty": qty, "note": note})

    if not items:
        raise ValueError("no_items")

    width = int(os.getenv("KITCHEN_COLS", "32"))
    payload = build_kitchen_ticket(header, items, width=width)
    return payload.hex()


@bp.get("/api/print/checker_hex/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_checker_hex(session_id):
    include_cancelled = request.args.get("include_cancelled", "1") != "0"
    collapse_voids = request.args.get("collapse_voids", "1") != "0"
    printed_only = request.args.get("printed_only", "1") != "0"

    groups = _parse_groups()
    rows = _fetch_all_order_rows(session_id)
    rows = _filter_rows_by_groups(rows, groups)
    split_label = _split_label_for_checker(session_id, groups, rows)
    items = _build_checker_items(
        rows,
        include_cancelled=include_cancelled,
        collapse_voids=collapse_voids,
        printed_only=printed_only,
    )

    meta = _session_meta_for_checker(session_id)
    header = {
        "table_number": meta.get("table_label") or meta.get("table_number"),
        "printed_at": fmt_now(),
        "title": "CHECKER",
        "guest_name": meta.get("guest_name"),
        "pax": meta.get("pax"),
    }
    if split_label:
        header["split_label"] = split_label

    payload = build_checker_bytes(header, items)
    return jsonify({"status": "ok", "hex": payload.hex()})


@bp.get("/api/print/admin_checker_hex/<session_id>")
@login_required
@roles_required("admin")
def api_admin_checker_hex(session_id):
    printed_only = request.args.get("printed_only", "1") != "0"
    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        return jsonify({"status": "error", "message": "session not found"}), 404

    groups = _parse_groups()
    rows = _fetch_admin_checker_rows(session_id)
    rows = _filter_rows_by_groups(rows, groups)
    payload_data = _build_admin_checker_payload(rows, printed_only=printed_only)
    split_label = _split_label_for_checker(session_id, groups, rows)

    meta = _session_meta_for_checker(session_id)
    header = {
        "table_number": meta.get("table_label") or meta.get("table_number"),
        "printed_at": fmt_now(),
        "title": "ADMIN CHECKER",
        "guest_name": meta.get("guest_name"),
        "pax": meta.get("pax"),
    }
    if split_label:
        header["split_label"] = split_label

    payload = build_admin_checker_bytes(
        header,
        payload_data.get("sections") or [],
        payload_data.get("details") or [],
    )
    return jsonify({"status": "ok", "hex": payload.hex()})


@bp.get("/api/print/qr_checker_hex/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_qr_checker_hex(session_id):
    only_unprinted = request.args.get("unprinted", "1") != "0"
    rows = _fetch_qr_order_rows(session_id, only_unprinted=only_unprinted)
    items = _build_checker_items(
        rows,
        include_cancelled=True,
        collapse_voids=True,
        printed_only=False,
    )

    meta = _session_meta_for_checker(session_id)
    header = {
        "table_number": meta.get("table_label") or meta.get("table_number"),
        "printed_at": fmt_now(),
        "title": "QR CHECK" + (" (UNSENT)" if only_unprinted else ""),
        "guest_name": meta.get("guest_name"),
        "pax": meta.get("pax"),
    }

    payload = build_checker_bytes(header, items)
    return jsonify({"status": "ok", "hex": payload.hex()})


@bp.get("/api/print/kitchen_hex/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_kitchen_hex(session_id):
    ids_param = request.args.get("ids") or request.args.get("item_ids") or ""
    id_list = []
    if ids_param:
        try:
            parts = re.split(r"[,\s]+", ids_param)
            id_list = [int(p) for p in parts if str(p).strip().isdigit()]
        except Exception:
            id_list = []
    try:
        hex_payload = _build_kitchen_hex(session_id, id_list, title="KITCHEN TICKET", is_void=False)
    except ValueError as e:
        code = str(e)
        if code == "session_not_found":
            return jsonify({"status": "error", "message": "session not found"}), 404
        if code == "no_items":
            return jsonify({"status": "error", "message": "no items to print"}), 400
        return jsonify({"status": "error", "message": "failed to build kitchen ticket"}), 500
    return jsonify({"status": "ok", "hex": hex_payload})


@bp.get("/api/print/void_hex/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_void_hex(session_id):
    name = (request.args.get("name") or "").strip()
    try:
        qty = float(request.args.get("qty") or "0")
    except Exception:
        qty = 0.0
    note = (request.args.get("note") or "").strip()
    if not name or qty <= 0:
        return jsonify({"status": "error", "message": "name & qty required"}), 400

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        return jsonify({"status": "error", "message": "session not found"}), 404

    meta = _session_meta_for_checker(session_id)
    cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
    header = _build_kitchen_header(
        meta,
        meta.get("table_number"),
        title="VOID TICKET",
        is_void=True,
        prepared_by=cashier_name,
        printed_at=f"Dicetak: {fmt_now()}",
    )
    items = [{"name": name, "qty": -abs(qty), "note": note}]
    width = int(os.getenv("KITCHEN_COLS", "32"))
    payload = build_kitchen_ticket(header, items, width=width)
    return jsonify({"status": "ok", "hex": payload.hex()})


@bp.get("/api/print/qr_hex/<table>/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def api_qr_hex(table, session_id):
    cfg = current_app.config
    qr_url = build_qr_order_url(table, session_id)
    brand_name = cfg.get("BRAND_NAME", "Demo Restaurant")
    wifi_ssid = cfg.get("GUEST_WIFI_SSID", "Demo Restaurant")
    wifi_pass = cfg.get("GUEST_WIFI_PASS", "demo-wifi-pass")
    issued_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    png = qr_bytes(qr_url)
    ticket_sid = table if get_qr_session_mode() == "table" else session_id
    payload = build_qr_ticket_bytes(
        table=table,
        session_id=ticket_sid,
        qr_url=qr_url,
        qr_png_bytes=png,
        brand_name=brand_name,
        wifi_ssid=wifi_ssid,
        wifi_pass=wifi_pass,
        issued_at=issued_at,
    )
    return jsonify({"status": "ok", "hex": payload.hex()})


# ---------- Printer map + defaults ----------
def _is_plain_rice_item(it: dict) -> bool:
    """
    Detect plain 'Nasi Putih...' that should not go to MASAK station.
    It should only be printed on the EXPEDITER ticket.
    """
    try:
        name = (it.get("name") or "").strip().lower()
    except Exception:
        return False
    # Matches 'nasi putih', 'nasi putih refill', etc.
    return name.startswith("nasi putih")

def _read_printer_map():
    """
    Resolve PRINTER_KEY_MAP from Flask config or env.
    Accepts dict or JSON string. Safe fallback to {}.
    """
    raw = current_app.config.get("PRINTER_KEY_MAP")
    if raw is None:
        raw = os.getenv("PRINTER_KEY_MAP")  # e.g. {"expediter":"kitchen","cumi":"squid",...}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}

def _default_printer_id() -> str:
    """
    Fallback logical printer id (must exist in static/printers.json).
    """
    return (
        current_app.config.get("DEFAULT_KITCHEN_PRINTER")
        or os.getenv("DEFAULT_KITCHEN_PRINTER")
        or "kitchen"
    )
def is_bar_station(st: str) -> bool:
    return (st or "").strip().lower() == "bar"


# ---------- Printer routing helpers ----------
def _require_test_token():
    expected = (os.getenv("TEST_PRINT_TOKEN") or "").strip()
    supplied = (
        request.args.get("token")
        or (request.get_json(silent=True) or {}).get("token")
        or request.headers.get("X-Debug-Token")
        or ""
    )
    if not expected:
        return False, "test token not configured"
    if supplied != expected:
        return False, "unauthorized"
    return True, None

# --- Public, token-guarded route_debug (no login needed) ---
# ---- Ad-hoc print test: send arbitrary items to real printers (token-guarded) ----
@bp.route("/print/kitchen/route_print", methods=["POST"])
def route_print_public():
    """
    Token-guarded. Actually PRINTS a fake order using routing:
      - One consolidated EXPEDITER ticket (all lines)
      - One ticket per station (bucketed by routing)
    Body JSON:
    {
      "token": "abc123",         # must match TEST_PRINT_TOKEN (or pass ?token=...)
      "table": "18",             # used for header + bar 1F/2F routing
      "print_expediter": true,   # default true
      "print_stations": true,    # default true
      "items": [
        {"name":"gurame bakar","qty":1,"note":"TEST, DIEMIN AJA DITEMPAT"},
        {"name":"baronang asam pedas","qty":1,"note":"..."},
        {"name":"cumi asam pedas","qty":1,"note":"..."},
        {"name":"teh tawar","qty":1,"note":"..."}
      ]
    }
    """
    ok, err = _require_test_token()
    if not ok:
        return jsonify({"status": "error", "message": err}), 403

    data = request.get_json(silent=True) or {}
    table = (data.get("table") or "TEST").strip()
    print_expediter = bool(data.get("print_expediter", True))
    print_stations  = bool(data.get("print_stations", True))

    raw_items = data.get("items") or []
    # normalize input
    items = []
    for it in raw_items:
        if isinstance(it, str):
            items.append({"name": it, "qty": 1.0, "note": ""})
        elif isinstance(it, dict):
            nm = (it.get("name") or "").strip()
            if not nm:
                continue
            try:
                q = float(it.get("qty") or 1)
            except Exception:
                q = 1.0
            nt = (it.get("note") or "").strip()
            items.append({"name": nm, "qty": q, "note": nt})
    if not items:
        return jsonify({"status":"error","message":"no items"}), 400

    # bucket by station (uses _station_for which now includes category)
    buckets = {}
    for it in items:
        st = _station_for(it["name"])
        buckets.setdefault(st, []).append({"name": it["name"], "qty": it["qty"], "note": it["note"]})

    results, errors = [], []
    now = fmt_now()

    # 1) EXPEDITER consolidated (skip drinks)
    if print_expediter:
        try:
            header = {"table_number": table, "printed_at": now, "title": "KITCHEN TICKET", "is_void": False}
            exp_items = [it for it in items if not is_drink(it)]
            if exp_items:
                job = _print_ticket_for_station("expediter", table, header, exp_items)
                results.append({"station": "expediter", "job": job, "count": len(exp_items)})
        except Exception as e:
            current_app.logger.exception("route_print expediter error")
            errors.append(f"expediter: {e}")

    # 2) Per-station tickets (per-item where configured)
    if print_stations:
        for st, lines in buckets.items():
            try:
                header = {"table_number": table, "printed_at": now, "title": f"KITCHEN — {st.upper()}", "is_void": False}

                # --- NEW: bar = one grouped slip of drinks ---
                if is_bar_station(st):
                    drink_lines = [it for it in lines if is_drink(it)]
                    if drink_lines:
                        job = _print_ticket_for_station(st, table, header, drink_lines)
                        results.append({"station": st, "job": job, "count": len(drink_lines)})
                    continue

                # original behavior for non-bar
                if is_per_item_station(st):
                    for it in lines:
                        job = _print_ticket_for_station(st, table, header, [it])
                        results.append({"station": st, "job": job, "count": 1})
                else:
                    job = _print_ticket_for_station(st, table, header, lines)
                    results.append({"station": st, "job": job, "count": len(lines)})
            except Exception as e:
                current_app.logger.exception("route_print station '%s' error", st)
                errors.append(f"{st}: {e}")


    status = "success" if not errors else ("partial_success" if results else "error")
    return jsonify({"status": status, "router": ROUTER_NAME, "buckets": buckets, "results": results, "errors": errors})


@bp.route("/print/kitchen/route_debug", methods=["POST"])
def route_debug_public():
    """
    Token-guarded routing debug (no auth). Pass ?token=... or JSON {"token": "..."}.
    Body accepts either strings or {name, note} objects:
      {
        "items": [
          "gurame bakar",
          {"name":"teh tawar","note":"..."}
        ]
      }
    """
    ok, err = _require_test_token()
    if not ok:
        return jsonify({"status": "error", "message": err}), 403

    data = request.get_json(silent=True) or {}
    raw_items = data.get("items") or []

    buckets = {}
    normalized = []

    for it in raw_items:
        if isinstance(it, str):
            name, note = it, ""
        elif isinstance(it, dict):
            name = (it.get("name") or "").strip()
            note = (it.get("note") or "").strip()
            if not name:
                continue
        else:
            continue

        st = _station_for(name)
        obj = {"name": name, "note": note}
        normalized.append({"station": st, **obj})
        buckets.setdefault(st, []).append(obj)

    return jsonify({
        "status": "ok",
        "router": ROUTER_NAME,
        "buckets": buckets,        # {"bakaran":[{name, note},...], "bar":[...], ...}
        "normalized": normalized   # flat view showing station chosen per line
    })



@bp.before_app_request
def _log_router_once():
    if not hasattr(current_app, "_router_logged"):
        current_app._router_logged = True
        try:
            current_app.logger.info("[ROUTE] using router: %s", ROUTER_NAME)
        except Exception:
            pass

import re

def _resolve_bar_printer_by_table(table_number: str | int | None) -> str:
    """
    Choose bar printer by table *label*.
    - Floor 1: any table whose leading number is 1..30  -> bar-1f
    - Floor 2: leading number >= 31 (or no number)      -> bar-2f
    - TAKE AWAY (TA)                                    -> bar-1f
    - Floor 5 and 6(tables 500–699)                          -> bar-1f
    """
    s = str(table_number or "").strip().upper()

    # --- SPECIAL CASE: Take Away always uses bar lantai 1 ---
    if s in ("TA", "TAKE AWAY", "TAKEAWAY"):
        return "bar-1f"

    m = re.match(r"(\d+)", s)
    n = int(m.group(1)) if m else None

    # Floor 5 and 6 (500-range tables) should use bar lantai 1
    if n is not None and 500 <= n < 700:
        return "bar-1f"

    if n is not None and 1 <= n <= 100:
        return "bar-1f"
    return "bar-2f"


def _normalize_station(st: str) -> str:
    """Map common aliases to stable keys that exist in PRINTER_KEY_MAP or printers.json."""
    s = (st or "").strip().lower()
    if s in ("", "null", "none"):
        return "kitchen"
    if s in ("dapur", "all", "fallback"):
        return "kitchen"
    return s

def _printer_key_for_station(station: str, table_number: str | int | None = None) -> str:
    """
    Map a logical station (e.g. 'kitchen','bar','steam','grill','sayuran','cumi','masak','expediter')
    to a printer ID from printers.json (or cups mapping). Falls back safely.
    """
    st = _normalize_station(station)
    mapping = _read_printer_map()

    # Expediter (consolidated) → kitchen by default
    if st == "expediter":
        return mapping.get("expediter") or mapping.get("kitchen") or _default_printer_id()

    # Bar per-floor
    if st == "bar":
        return mapping.get("bar") or _resolve_bar_printer_by_table(table_number)

    # Use explicit map if present, otherwise assume station id equals printers.json id
    return mapping.get(st) or st or _default_printer_id()

# --- Robust station routing (printing/routing_rules) --------------------------
infer_route_tag = None
ROUTER_NAME = "none"
try:
    # correct path for your project layout
    from printing.routing_rules import infer_route_tag as _infer
    infer_route_tag = _infer
    ROUTER_NAME = "printing.routing_rules"
except Exception:
    infer_route_tag = None
    ROUTER_NAME = "inline(fallback)"

# Keep INLINE_* exactly aligned with routing_rules.py
INLINE_KEYWORDS = {
    # --- families that should short-circuit by name ---
    "cumi": "cumi",            # “cumi …” → cumi station
    "udang": "cumi",           # udang shares wok line with cumi
    "kerang": "steam",
    "kepiting": "masak",
    "nasi goreng": "masak",
    "bihun": "masak",

    # --- explicit technique / style keywords ---
    "steam":  "steam",
    "hongkong": "steam",
    "nyonya": "steam",
    "garden": "steam",

    "bakar spesial": "masak",
    "bakar":  "bakaran",       # grilled → grill station
    "panggang": "bakaran",

    "goreng kering": "masak",
    "goreng mentega": "masak",
    "asam manis": "masak",
    "asam pedas": "masak",
    "lada hitam": "masak",
    "saos padang": "masak",
    "saos tiram": "masak",
    "tauco": "masak",
    "sop": "masak",
    "rebus": "masak",

    # --- drinks ---
    "teh": "bar",
    "kopi": "bar",
    "soda": "bar",
    "sirup": "bar",
}

INLINE_CATEGORY_DEFAULTS = {
    # core groups
    "Minuman":     "bar",
    "Nasi":        "masak",
    "Sayur":       "sayuran",
    "Lain Lain":   "masak",
    "Kuah Masak":  "masak",

    # seafood families
    "Ikan":            "masak",   # fish default (grill/steam handled by keywords)
    "Cumi":            "cumi",
    "Udang":           "cumi",
    "Kerang Bambu":    "steam",
    "Kerang Kepa":     "steam",
    "Kerang Ijo":      "steam",
    "Kerang Dara":     "steam",
    "Keong Macan":     "steam",
    "Kepiting Jantan": "masak",
    "Kepiting Betina": "masak",

    # extras / sides
    "Ekstra Telor": "masak",
}

def _infer_station_inline(item_name: str, category_path=None) -> str:
    """
    Mirror routing_rules.infer_route_tag:
      1) keyword short-circuit (families, styles, drinks)
      2) category default
      3) special fish fallback
      4) safe default
    """
    name = (item_name or "").lower()
    cats = category_path or []

    # 1) keyword short-circuit
    for kw, tag in INLINE_KEYWORDS.items():
        if kw in name:
            return tag

    # 2) category default
    if cats:
        top = cats[0]
        if top in INLINE_CATEGORY_DEFAULTS:
            return INLINE_CATEGORY_DEFAULTS[top]

    # 3) special fish fallback
    if cats and cats[0] == "Ikan":
        return "masak"

    # 4) safe default
    return "dapur"


def _station_for(label: str, categories=None) -> str:
    # 0) TRY CATEGORY_STATION_MAP directly (if you plan to use it later)
    try:
        cfg = current_app.config.get("CATEGORY_STATION_MAP") or "{}"
        mapping = json.loads(cfg) if isinstance(cfg, str) else (cfg or {})
    except Exception:
        mapping = {}

    # 0b) Per-item override from menu.json wins.
    try:
        override = printer_override_for_label(label)
        if override:
            return _normalize_station(override)
    except Exception:
        pass

    # 1) Try the old helper (kept for backward compat). It returns an explicit station or None.
    try:
        s_old = station_for_item(label)
        if s_old:
            return _normalize_station(s_old)
    except Exception:
        pass

    # 2) Determine category from menu.json so routing rules can use it.
    base, _ = split_item_and_dish(label)
    cat = (find_category_for_item(base) or "").strip()
    cat_list = [cat] if cat else []

    # If you *do* have CATEGORY_STATION_MAP in the future, honor it first.
    if cat and mapping:
        s_map = mapping.get(cat.lower())
        if s_map:
            return _normalize_station(s_map)

    # 3) Use your project’s routing rules with category context.
    if infer_route_tag:
        try:
            s = infer_route_tag(label, cat_list)
            if s:
                return _normalize_station(s)
        except Exception:
            pass

    # 4) Inline fallback with category context.
    return _normalize_station(_infer_station_inline(label, cat_list))

def _print_ticket_for_station(station_key: str, table_number, header: dict, items: list) -> str:
    """
    Prints one ticket either via RAW ESC/POS or via HTML->CUPS, depending on PRINT_BACKEND.
    Returns a job string (raw endpoint text or lp job id text).
    """
    station_norm = (station_key or "").strip().lower()
    target_key = _printer_key_for_station(station_key, table_number)

    # helpful log to verify routing
    try:
        current_app.logger.info(
            "[PRINT] station=%s -> printer_key=%s items=%s",
            station_key, target_key, [(it.get('qty'), it.get('name')) for it in (items or [])]
        )
    except Exception:
        pass

    # --- IMPORTANT: Nasi Putih should never print on MASAK station ---
    # It already appears on the EXPEDITER consolidated ticket.
    if station_norm == "masak":
        filtered = [it for it in (items or []) if not _is_plain_rice_item(it)]
        if not filtered:
            return "skip://plain-rice-only"
        items = filtered

    def _do_print():
        if _raw_enabled():
            # RAW path (your ESC/POS builder uses ASCII '-' for notes — no weird bullet)
            return print_kitchen_raw(target_key, header, items)
        # HTML->CUPS path (if you still see the bullet '•', remove it in kitchen_chit.html)
        html = render_template("kitchen_chit.html", header=header, items=items)
        return printing.print_html_receipt(html, printer_key=target_key)

    try:
        return _do_print()
    except Exception as e:
        # One retry helps with transient network/CUPS hiccups without user re-click
        try:
            current_app.logger.warning(
                "[PRINT] station=%s printer_key=%s failed once (%s); retrying...",
                station_key, target_key, e
            )
        except Exception:
            pass
        time.sleep(0.5)
        return _do_print()


# ---------- Test route (token-guarded, optional) ----------
@bp.route("/print/kitchen/test", methods=["GET", "POST"])
def kitchen_test():
    """
    Prints a tiny test ticket to:
      1) Expediter (kitchen/all)
      2) Cumi station
    Query/body:
      ?table=14
      ?token=XXXX (must match TEST_PRINT_TOKEN env if set)
    """
    expected = os.getenv("TEST_PRINT_TOKEN", "")
    supplied = (request.args.get("token") or request.form.get("token") or "")
    if expected and supplied != expected:
        return jsonify({"status": "error", "message": "unauthorized"}), 403

    table = request.args.get("table") or "TEST"
    header_base = {"table_number": table, "printed_at": fmt_now(), "is_void": False}
    demo_items = [{"name": "Cumi Asam Manis", "qty": 1, "note": "TEST KASIH KE DAPUR"}]

    results, errors = [], []

    # Expediter (full)
    try:
        hdr = {**header_base, "title": "KITCHEN TICKET"}
        job = _print_ticket_for_station("expediter", table, hdr, demo_items)
        results.append({"station": "expediter", "job": job, "key": _printer_key_for_station("expediter", table)})
    except Exception as e:
        current_app.logger.exception("kitchen_test expediter error")
        errors.append(f"expediter: {e}")

    # Cumi station
    try:
        hdr = {**header_base, "title": "KITCHEN — CUMI"}
        job = _print_ticket_for_station("cumi", table, hdr, demo_items)
        results.append({"station": "cumi", "job": job, "key": _printer_key_for_station("cumi", table)})
    except Exception as e:
        current_app.logger.exception("kitchen_test cumi error")
        errors.append(f"cumi: {e}")

    status = "success" if not errors else ("partial_success" if results else "error")
    return jsonify({"status": status, "results": results, "errors": errors})

# ---------- Routes ----------
@bp.post("/print/kitchen/send/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def kitchen_send(session_id):
    try:
        rows = db.get_printables(None, session_id) or []
        sess_min = db.get_session_by_id(None, session_id)
        if not sess_min:
            return jsonify({"status": "error", "message": "session not found"}), 404
        _sid, table_number, _ = sess_min
    
        meta = _session_meta_for_checker(session_id)
        cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
        split_map = _split_map_for_session(session_id)
        table_print = _kitchen_table_display(meta, table_number)
        printed_at = fmt_now()
        def _hdr(title, is_void=False, split_label=None):
            return _build_kitchen_header(
                meta,
                table_number,
                title=title,
                is_void=is_void,
                split_label=split_label,
                prepared_by=cashier_name,
                printed_at=printed_at,
            )


        # Split into normal/void (unchanged)
        normal_lines, void_lines = [], []
        for r in rows:
            rid   = r[0]
            name  = r[1] or ""
            qty   = r[2] or 0
            note  = r[5] or ""
            group_key = normalize_group(r[7] if len(r) > 7 else None)
            vq = 0.0
            if len(r) >= 9:
                try: vq = float(r[8] or 0)
                except: vq = 0.0

            if qty and qty > 0:
                normal_lines.append({
                    "id": rid,
                    "name": name,
                    "qty": float(qty),
                    "note": note,
                    "group": group_key,
                })
            if name and vq and vq > 0:
                void_lines.append({
                    "id": rid,
                    "name": name,
                    "qty": -abs(float(vq)),
                    "note": note,
                    "group": group_key,
                })

        # DRY RUN (unchanged)
        if request.args.get("dryrun") == "1":
            has_any = bool(normal_lines or void_lines)
            return jsonify({"status": "ok", "has_printables": has_any}), 200

        if _demo_mode():
            has_any = bool(normal_lines or void_lines)
            if not has_any:
                return jsonify({"status": "nothing_to_print"}), 200
            # Bucket normal items by station so client can open per-station previews
            station_items: dict[str, list[int]] = {}
            for it in normal_lines:
                try:
                    st = _station_for(it["name"])
                except Exception:
                    st = "kitchen"
                station_items.setdefault(st, []).append(it["id"])
            if normal_lines:
                ids = [it["id"] for it in normal_lines]
                db.mark_items_printed(None, ids, by_user_id=getattr(current_user, "id", 0))
            try:
                session_items_changed(table_number, session_id)
                _push_state(session_id)
            except Exception:
                current_app.logger.exception("demo kitchen_send: session emit failed")
            return jsonify({
                "status": "success",
                "normal_count": len(normal_lines),
                "void_count": len(void_lines),
                "errors": [],
                "demo": True,
                "stations": sorted(station_items.keys()),
                "station_items": {st: item_ids for st, item_ids in station_items.items()},
                "actions": ["sent_to_kitchen", "printed_locally"],
            })

        printed_any = False
        normal_printed = False
        errors = []

        # 1) EXPEDITER (normal) — skip drinks
        if normal_lines:
            grouped_normals = _group_items_by_split(normal_lines)
            for group_key, group_lines in grouped_normals.items():
                split_label = _split_label_for_group(group_key, split_map)
                try:
                    normal_lines_expediter = [it for it in group_lines if not is_drink(it)]
                    if normal_lines_expediter:
                        _print_ticket_for_station(
                            "expediter", table_print, _hdr("KITCHEN TICKET", is_void=False, split_label=split_label),
                            _decorate_items_with_notes(normal_lines_expediter)
                        )
                        printed_any = True
                        normal_printed = True
                except Exception as e:
                    current_app.logger.exception("Expediter print failed: %s", e)
                    errors.append(f"expediter: {e}")

                # 2) Per-station (normal) — per-item for configured stations
                buckets = {}
                for it in group_lines:
                    # prefer explicit machine token in note if present: [[station:bar]] or [[station:kitchen]]
                    st = None
                    try:
                        note = (it.get("note") or "")
                        m = re.match(r"\s*\[\[station:([a-zA-Z0-9_-]+)\]\]\s*", note or "", re.IGNORECASE)
                        if m:
                            st = _normalize_station(m.group(1))
                    except Exception:
                        st = None

                    if not st:
                        st = _station_for(it["name"])

                    # Plain rice → only expediter (skip station buckets)
                    if _is_plain_rice_item(it):
                        continue

                    buckets.setdefault(st, []).append({"name": it["name"], "qty": it["qty"], "note": it["note"]})

                for st, items_for_station in buckets.items():
                    try:
                        # --- NEW: bar grouped (ignore PER_ITEM_STATIONS for bar) ---
                        if is_bar_station(st):
                            _print_ticket_for_station(
                                st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                                _decorate_items_with_notes(items_for_station)
                            )
                        else:
                            # original behavior for non-bar
                            if is_per_item_station(st):
                                for it in items_for_station:
                                    _print_ticket_for_station(
                                        st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                                        _decorate_items_with_notes([it])
                                    )
                            else:
                                _print_ticket_for_station(
                                    st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                                    _decorate_items_with_notes(items_for_station)
                                )
                        printed_any = True
                        normal_printed = True
                    except Exception as e:
                        current_app.logger.exception("Station '%s' print failed: %s", st, e)
                        errors.append(f"{st}: {e}")


        # 3) VOID printing — expediter skips drinks; stations support per-item
        if void_lines:
            grouped_voids = _group_items_by_split(void_lines)
            for group_key, group_lines in grouped_voids.items():
                split_label = _split_label_for_group(group_key, split_map)
                try:
                    void_lines_expediter = [it for it in group_lines if not is_drink(it)]
                    if void_lines_expediter:
                        _print_ticket_for_station(
                            "expediter", table_print, _hdr("VOID TICKET", is_void=True, split_label=split_label),
                            _decorate_items_with_notes(void_lines_expediter)
                        )
                        printed_any = True
                except Exception as e:
                    current_app.logger.exception("Expediter VOID print failed: %s", e)
                    errors.append(f"expediter_void: {e}")

                void_buckets = {}
                for it in group_lines:
                    st = None
                    try:
                        note = (it.get("note") or "")
                        m = re.match(r"\s*\[\[station:([a-zA-Z0-9_-]+)\]\]\s*", note or "", re.IGNORECASE)
                        if m:
                            st = _normalize_station(m.group(1))
                    except Exception:
                        st = None
                    if not st:
                        st = _station_for(it["name"])

                    # Plain rice → only expediter (skip station buckets)
                    if _is_plain_rice_item(it):
                        continue

                    void_buckets.setdefault(st, []).append({"name": it["name"], "qty": it["qty"], "note": it["note"]})

                for st, items_for_station in void_buckets.items():
                    try:
                        if is_bar_station(st):
                            _print_ticket_for_station(
                                st, table_print, _hdr(f"VOID — {st.upper()}", True, split_label=split_label),
                                _decorate_items_with_notes(items_for_station)
                            )
                        else:
                            if is_per_item_station(st):
                                for it in items_for_station:
                                    _print_ticket_for_station(
                                        st, table_print, _hdr(f"VOID — {st.upper()}", True, split_label=split_label),
                                        _decorate_items_with_notes([it])
                                    )
                            else:
                                _print_ticket_for_station(
                                    st, table_print, _hdr(f"VOID — {st.upper()}", True, split_label=split_label),
                                    _decorate_items_with_notes(items_for_station)
                                )
                        printed_any = True
                    except Exception as e:
                        errors.append(f"{st}_void: {e}")



        # ---------- 4) Mark printed (only if some NORMAL actually printed) ----------
        if normal_lines and normal_printed:
            ids = [it["id"] for it in normal_lines]
            db.mark_items_printed(None, ids, by_user_id=getattr(current_user, "id", 0))
            #so it doesnt merge in the db
            #db.consolidate_printed_lines(None, session_id)

        # ---------- 5) Realtime notify ----------
        if printed_any:
            session_items_changed(table_number, session_id)
            _push_state(session_id)

        had_candidates = bool(normal_lines or void_lines)
        if not printed_any:
            if had_candidates and errors:
                return jsonify({"status": "error", "message": "Printing failed", "errors": errors}), 500
            return jsonify({"status": "nothing_to_print"}), 200

        return jsonify({
            "status": "success",
            "normal_count": len(normal_lines),
            "void_count": len(void_lines),
            "errors": errors
        })

    except Exception as e:
        current_app.logger.exception("kitchen_send error")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.post("/print/kitchen/send_item/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def kitchen_send_single(session_id):
    """
    Print ONLY the specified order_item IDs to kitchen/bar.
    Expects JSON: { "item_ids": [1,2,3] }
    """
    payload = request.get_json(silent=True) or {}
    ids_raw = payload.get("item_ids") or payload.get("ids") or payload.get("order_item_ids") or []
    try:
        ids = [int(i) for i in ids_raw]
    except Exception:
        return jsonify({"status": "error", "message": "item_ids must be integers"}), 400
    ids = [i for i in ids if i > 0]
    if not ids:
        return jsonify({"status": "error", "message": "item_ids required"}), 400

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        return jsonify({"status": "error", "message": "session not found"}), 404
    _sid, table_number, _ = sess_min

    # Fetch only NEW/EDITED rows for these ids
    rows = []
    conn = db.connect_db(None)
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, item_name, qty, sauce, note, status, bill_group
                  FROM order_items
                 WHERE session_id = %s
                   AND id = ANY(%s)
                   AND status IN ('new','edited')
            """, (session_id, ids))
            rows = c.fetchall() or []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not rows:
        return jsonify({"status": "nothing_to_print", "message": "No pending items for those IDs"}), 200

    meta = _session_meta_for_checker(session_id)
    cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
    split_map = _split_map_for_session(session_id)
    table_print = _kitchen_table_display(meta, table_number)
    printed_at = fmt_now()
    def _hdr(title, is_void=False, split_label=None):
        return _build_kitchen_header(
            meta,
            table_number,
            title=title,
            is_void=is_void,
            split_label=split_label,
            prepared_by=cashier_name,
            printed_at=printed_at,
        )

    normal_lines = []
    for r in rows:
        try:
            rid   = int(r[0])
            name  = r[1] or ""
            qty   = float(r[2] or 0)
            note  = r[4] or ""
            group_key = normalize_group(r[6] if len(r) > 6 else None)
        except Exception:
            continue
        if qty <= 0:
            continue
        normal_lines.append({
            "id": rid,
            "name": name,
            "qty": qty,
            "note": note,
            "group": group_key,
        })

    if not normal_lines:
        return jsonify({"status": "nothing_to_print"}), 200

    # Dry-run support for client-side peek
    if request.args.get("dryrun") == "1":
        has_any = bool(normal_lines)
        return jsonify({"status": "ok", "has_printables": has_any}), 200

    if _demo_mode():
        station_items: dict[str, list[int]] = {}
        for it in normal_lines:
            try:
                st = _station_for(it["name"])
            except Exception:
                st = "kitchen"
            station_items.setdefault(st, []).append(it["id"])
        ids_printed = [it["id"] for it in normal_lines]
        if ids_printed:
            db.mark_items_printed(None, ids_printed, by_user_id=getattr(current_user, "id", 0))
        try:
            session_items_changed(table_number, session_id)
            _push_state(session_id)
        except Exception:
            current_app.logger.exception("demo kitchen_send_single: session emit failed")
        return jsonify({
            "status": "success",
            "count": len(normal_lines),
            "errors": [],
            "demo": True,
            "stations": sorted(station_items.keys()),
            "station_items": {st: item_ids for st, item_ids in station_items.items()},
            "actions": ["sent_to_kitchen", "printed_locally"],
        }), 200

    errors = []
    printed_any = False
    normal_printed = False

    grouped_normals = _group_items_by_split(normal_lines)
    for group_key, group_lines in grouped_normals.items():
        split_label = _split_label_for_group(group_key, split_map)
        # Expediter (skip drinks)
        try:
            exp_lines = [it for it in group_lines if not is_drink(it)]
            if exp_lines:
                _print_ticket_for_station(
                    "expediter", table_print, _hdr("KITCHEN TICKET", is_void=False, split_label=split_label),
                    _decorate_items_with_notes(exp_lines)
                )
                printed_any = True
                normal_printed = True
        except Exception as e:
            current_app.logger.exception("Single-item expediter print failed: %s", e)
            errors.append(f"expediter: {e}")

        # Per-station buckets
        buckets = {}
        for it in group_lines:
            st = None
            try:
                note = (it.get("note") or "")
                m = re.match(r"\s*\[\[station:([a-zA-Z0-9_-]+)\]\]\s*", note or "", re.IGNORECASE)
                if m:
                    st = _normalize_station(m.group(1))
            except Exception:
                st = None

            if not st:
                st = _station_for(it["name"])

            # Plain rice → only expediter (skip station buckets)
            if _is_plain_rice_item(it):
                continue

            buckets.setdefault(st, []).append({"name": it["name"], "qty": it["qty"], "note": it["note"]})

        for st, items_for_station in buckets.items():
            try:
                if is_bar_station(st):
                    _print_ticket_for_station(
                        st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                        _decorate_items_with_notes(items_for_station)
                    )
                else:
                    if is_per_item_station(st):
                        for it in items_for_station:
                            _print_ticket_for_station(
                                st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                                _decorate_items_with_notes([it])
                            )
                    else:
                        _print_ticket_for_station(
                            st, table_print, _hdr(f"KITCHEN — {st.upper()}", is_void=False, split_label=split_label),
                            _decorate_items_with_notes(items_for_station)
                        )
                printed_any = True
                normal_printed = True
            except Exception as e:
                current_app.logger.exception("Single-item station '%s' print failed: %s", st, e)
                errors.append(f"{st}: {e}")

    # Mark printed + notify
    if normal_lines and normal_printed:
        ids_printed = [it["id"] for it in normal_lines]
        db.mark_items_printed(None, ids_printed, by_user_id=getattr(current_user, "id", 0))

    if printed_any:
        try:
            session_items_changed(table_number, session_id)
            _push_state(session_id)
        except Exception:
            current_app.logger.exception("single-item: session emit failed (non-fatal)")

    if not printed_any:
        return jsonify({"status": "error", "message": "Printing failed", "errors": errors}), 500

    return jsonify({
        "status": "success" if not errors else "partial_success",
        "count": len(normal_lines),
        "errors": errors
    }), (200 if not errors else 207)
    
@bp.get("/print/kitchen/preview/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def kitchen_preview(session_id):
    # Optional filter: ?ids=1,2,3 to preview a subset (e.g., single-item send)
    ids_param = (
        request.args.get("ids")
        or request.args.get("item_ids")
        or request.args.get("id")
        or ""
    )
    id_list = []
    if ids_param:
        try:
            parts = re.split(r"[,\s]+", ids_param)
            id_list = [int(p) for p in parts if str(p).strip().isdigit()]
        except Exception:
            id_list = []

    rows = db.get_printables(None, session_id)
    if id_list:
        try:
            with db.connect_db(None) as conn, conn.cursor() as c:
                c.execute("""
                    SELECT id, item_name, qty, NULL as price, sauce, note, status, bill_group
                      FROM order_items
                     WHERE session_id = %s
                       AND id = ANY(%s)
                     ORDER BY "timestamp", id
                """, (session_id, id_list))
                rows = c.fetchall() or []
        except Exception:
            pass
    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)
    _sid, table_number, _ = sess_min

    # meta for header
    meta = _session_meta_for_checker(session_id)
    cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
    split_map = _split_map_for_session(session_id)
    split_label = _split_label_from_rows(rows, split_map)
    header = _build_kitchen_header(
        meta,
        table_number,
        title="KITCHEN TICKET",
        is_void=False,
        split_label=split_label,
        prepared_by=cashier_name,
        printed_at=fmt_now(),
    )


    # build items with note_lines
    def _row_to_item(r):
        try:
            name = (r[1] or "").strip()
            qty  = float(r[2] or 0)
            sauce = (r[4] if len(r) > 4 else None) or None
            note  = (r[5] if len(r) > 5 else "") or ""
        except Exception:
            name, qty, sauce, note = "", 0.0, None, ""
        return {
            "name": name,
            "qty": qty,
            "sauce": sauce,
            "note_lines": _normalize_note_lines(note),
        }

    items = [_row_to_item(r) for r in (rows or [])]
    if (request.args.get("silent") == "1") and not items:
        return Response("", status=204)
    return render_template("kitchen_chit.html", header=header, items=items)


@bp.post("/print/kitchen/void/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def kitchen_void_direct(session_id):
    """
    Print VOID tickets (negative qty) per station, plus a consolidated expediter VOID.
    Body accepts:
      { "lines": [ { "name":"Gurame Bakar", "qty": 2, "note":"habis 2 ons" }, ... ] }
    """
    payload = request.get_json() or {}
    lines = payload.get("lines") or []

    # simple form fallback
    if not lines:
        name = (payload.get("name") or request.args.get("name") or "").strip()
        try:
            qty = float(payload.get("qty") or request.args.get("qty") or 0)
        except Exception:
            qty = 0.0
        note = (payload.get("note") or request.args.get("note") or "").strip()
        if name and qty > 0:
            lines = [{"name": name, "qty": qty, "note": note}]

    if not lines:
        return jsonify({"status": "error", "message": "no lines"}), 400

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)
    _sid, table_number, _ = sess_min

    # Aggregate identical (name,note); force negative qty
    agg = OrderedDict()
    for it in lines:
        nm = (it.get("name") or "").strip()
        try:
            q = float(it.get("qty") or 0)
        except Exception:
            q = 0.0
        nt = (it.get("note") or "").strip()
        if not nm or q <= 0:
            continue
        key = (nm.lower(), nt.lower())
        if key in agg:
            agg[key]["qty"] += q
        else:
            agg[key] = {"name": nm, "qty": q, "note": nt}

    buckets = {}
    for _, it in agg.items():
        if it["qty"] <= 0:
            continue
        # Plain rice → only expediter (skip station buckets)
        if _is_plain_rice_item(it):
            continue
        st = _station_for(it["name"])
        item = {"name": it["name"], "qty": -abs(float(it["qty"])), "note": it["note"]}
        buckets.setdefault(st, []).append(item)

    if not buckets:
        return jsonify({"status": "error", "message": "no valid lines"}), 400

    if _demo_mode():
        return jsonify({
            "status": "success",
            "errors": [],
            "demo": True,
            "actions": ["sent_to_kitchen", "printed_locally"],
        }), 200

    errors = []

    meta = _session_meta_for_checker(session_id)
    cashier_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", None) or ""
    table_print = _kitchen_table_display(meta, table_number)
    printed_at = fmt_now()
    def _hdr(title, is_void=True):
        return _build_kitchen_header(
            meta,
            table_number,
            title=title,
            is_void=is_void,
            prepared_by=cashier_name,
            printed_at=printed_at,
        )


    # Consolidated expediter VOID (skip drinks)
    try:
        all_items = [it for items in buckets.values() for it in items]
        exp_items = [it for it in all_items if not is_drink(it)]
        if exp_items:
            _print_ticket_for_station(
                "expediter", table_print, _hdr("VOID TICKET", True),
                _decorate_items_with_notes(exp_items)
            )
    except Exception as e:
        current_app.logger.exception("Expediter VOID print failed")
        errors.append(f"expediter_void: {e}")

    # Per-station VOID (per-item where configured)
    for st, items_for_station in buckets.items():
        try:
            if is_per_item_station(st):
                for it in items_for_station:
                    _print_ticket_for_station(
                        st, table_print, _hdr(f"VOID — {st.upper()}", True),
                        _decorate_items_with_notes([it])
                    )
            else:
                _print_ticket_for_station(
                    st, table_print, _hdr(f"VOID — {st.upper()}", True),
                    _decorate_items_with_notes(items_for_station)
                )
        except Exception as e:
            errors.append(f"{st}: {e}")


    return jsonify({
        "status": "success" if not errors else "partial_success",
        "errors": errors
    }), (200 if not errors else 207)

@bp.post("/print/order/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def print_order_stub(session_id):
    rows = db.get_printables(None, session_id)
    if not rows:
        return jsonify({"status": "nothing_to_print"}), 200
    ids = [r[0] for r in rows]
    db.mark_items_printed(None, ids, by_user_id=current_app.config.get("QR_USER_ID") or 0)
    sess_min = db.get_session_by_id(None, session_id)
    if sess_min:
        _, table_number, _ = sess_min
        session_items_changed(table_number, session_id)
        _push_state(session_id)
    return jsonify({"status": "success", "count": len(ids)})

@bp.get("/print/kitchen/void_preview/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def kitchen_void_preview(session_id):
    name = (request.args.get("name") or "").strip()
    try:
        qty = float(request.args.get("qty") or "0")
    except Exception:
        qty = 0.0
    note = (request.args.get("note") or "").strip()
    if not name or qty <= 0:
        abort(400, "name & qty>0 required")

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)
    _sid, table_number, _ = sess_min

    meta = _session_meta_for_checker(session_id)
    header = _build_kitchen_header(
        meta,
        table_number,
        title="VOID TICKET",
        is_void=True,
        printed_at=fmt_now(),
    )

    items = _decorate_items_with_notes([{
        "name": name,
        "qty": -abs(qty),
        "note": note
    }])

    return render_template("kitchen_chit.html", header=header, items=items)


def _fetch_all_order_rows(session_id):
    """
    Return *all* order rows for the session (printed & unprinted).
    Prefer helpers that include status and void_qty.
    """
    candidates = [
        "get_all_order_items_by_session",  # may exclude cancelled
        "get_all_items_for_session",
        "get_all_items",
        "get_all_lines_for_session",
        "get_all_order_rows",
        "get_session_items",
        "get_all_order_items",
        "get_orders_by_session",  # often includes cancelled rows
    ]
    rows = None
    for fn in candidates:
        f = getattr(db, fn, None)
        if callable(f):
            try:
                rows = f(None, session_id)
                break
            except TypeError:
                try:
                    rows = f(session_id)
                    break
                except Exception:
                    continue
            except Exception:
                continue

    if rows is None:
        rows = db.get_printables(None, session_id)

    # Force a best-effort full pull (including cancelled + void_qty) from order_items.
    conn = None
    try:
        conn = db.connect_db(None)
        with conn.cursor() as c:
            c.execute("""
                SELECT
                    id, item_name, qty, price, total_price,
                    sauce, note, status, "timestamp", bill_group,
                    COALESCE(void_qty, 0) AS void_qty,
                    table_number
                FROM order_items
                WHERE session_id = %s
                ORDER BY "timestamp" ASC, id ASC
            """, (session_id,))
            full_rows = c.fetchall()
            if full_rows:
                rows = full_rows
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return rows


def _qr_creator_clauses(alias="oi"):
    """
    Build SQL snippet/params to match QR-origin order items.
    Checks QR_USER_ID env and/or username QR_SERVICE/override.
    """
    clauses, params = [], []

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


def _fetch_qr_order_rows(session_id, only_unprinted=True):
    """
    Return QR-origin order rows for the session.
    Defaults to only NEW/EDITED (unprinted) items.
    """
    qr_clause, qr_params = _qr_creator_clauses("oi")
    status_filter = "AND COALESCE(oi.status,'') IN ('new','edited')" if only_unprinted else ""
    with db.connect_db(None) as conn, conn.cursor() as c:
        c.execute(
            f"""
            SELECT
                oi.id,
                oi.item_name,
                oi.qty,
                oi.price,
                oi.total_price,
                oi.sauce,
                oi.note,
                oi.status,
                oi."timestamp",
                oi.bill_group,
                COALESCE(oi.void_qty, 0) AS void_qty,
                oi.created_by_user_id
            FROM public.order_items oi
            WHERE oi.session_id = %s
              AND COALESCE(oi.status,'') <> 'cancelled'
              {status_filter}
              {qr_clause}
            ORDER BY oi."timestamp" ASC, oi.id ASC
            """,
            [session_id, *qr_params],
        )
        return c.fetchall()

def _row_extract(row):
    """Return (name, qty, note, void_qty, status) from a tuple or dict."""
    name = ""; qty = 0.0; note = ""; vq = 0.0; st = ""

    def _as_float(v):
        try:
            if v is None:
                return 0.0
            if isinstance(v, str):
                s = v.strip()
                return float(s) if s else 0.0
            from decimal import Decimal
            from numbers import Number
            if isinstance(v, (int, float, Decimal, Number)):
                return float(v)
            # last resort
            return float(v)
        except Exception:
            return 0.0

    # ---- Dict shape (unchanged, but use _as_float if you want) ----
    if isinstance(row, dict):
        name = (row.get("name") or row.get("item_name") or row.get("menu_name") or "").strip()
        qty  = _as_float(row.get("qty") or row.get("quantity") or row.get("qty_total") or 0)
        # merge possible note fields
        note_parts = [
            row.get("note"), row.get("notes"), row.get("remark"), row.get("remarks"),
            row.get("extra_note"), row.get("sauce"),
        ]
        note = " | ".join([str(x).strip() for x in note_parts if x and str(x).strip()])
        vq   = _as_float(row.get("void_qty") or row.get("void_quantity") or row.get("qty_void") or 0)
        st   = str(row.get("status") or row.get("line_status") or row.get("print_status") or "").lower()
        return name, qty, note, vq, st

    # ---- Tuple / list shape ----
    def _pick(idx):
        try:
            val = row[idx]
            return str(val).strip() if val is not None else ""
        except Exception:
            return ""

    # Common "orders" table layout (id, session_id, table, name, qty, price, total, note, status, ts, printed_qty?, served?, group, void_qty, printed_ts?)
    if len(row) >= 14 and isinstance(row[3], str):
        name = (row[3] or "").strip()
        qty  = _as_float(row[4] if len(row) > 4 else 0)
        note = " | ".join([x for x in (_pick(6), _pick(7)) if x])
        st   = str(_pick(8)).lower()
        vq   = _as_float(row[13] if len(row) > 13 else (row[10] if len(row) > 10 else 0))
        return name, qty, note, vq, st

    try:
        name = (row[1] or "").strip()
    except Exception:
        name = ""

    qty = _as_float(row[2] if len(row) > 2 else 0)

    # try multiple candidate slots for note; merge if present
    note_candidates = [_pick(5), _pick(6), _pick(4)]  # (note, alt note, sauce)
    note = " | ".join([x for x in note_candidates if x])

    try:
        st = str(row[7] or "").lower()
    except Exception:
        st = ""

    # void qty: prefer index 10, fallback to 8; accept Decimal/str
    vq = 0.0
    if len(row) > 10:
        vq = _as_float(row[10])
    elif len(row) > 8:
        vq = _as_float(row[8])

    return name, qty, note, vq, st


def _row_group_key(row):
    """Return normalized bill_group key ('' for main/no-group)."""
    raw = None
    if isinstance(row, dict):
        raw = row.get("bill_group") or row.get("group") or row.get("group_label")
    elif isinstance(row, (list, tuple)):
        if len(row) > 9:
            raw = row[9]
        elif len(row) > 7:
            raw = row[7]
    return normalize_group(raw) or ""


def _filter_rows_by_groups(rows, groups):
    if not groups:
        return rows
    glower = {str(g).strip().lower() for g in groups if str(g).strip()}
    if any(g in ("all", "semua") for g in glower):
        return rows
    want_main = "main" in glower
    allowed = set()
    for g in groups:
        gs = str(g).strip()
        if not gs or gs.lower() == "main":
            continue
        norm = normalize_group(gs)
        if norm:
            allowed.add(norm)
    if not want_main and not allowed:
        return []
    out = []
    for r in (rows or []):
        g = _row_group_key(r)
        if g:
            if g in allowed:
                out.append(r)
        else:
            if want_main:
                out.append(r)
    return out


def _split_label_for_checker(session_id, groups, rows):
    group_key = None
    if groups and len(groups) == 1:
        group_key = normalize_group(groups[0])
    if not group_key:
        uniq = set()
        for r in (rows or []):
            g = _row_group_key(r)
            if g:
                uniq.add(g)
        if len(uniq) == 1:
            group_key = next(iter(uniq))
    if not group_key:
        return None
    split_map = _split_map_for_session(session_id)
    label = (split_map.get(group_key) or "").strip()
    return label or str(group_key)



PRINTED_STATUSES = {"printed", "printed_all", "partial", "printed_partial", "paid"}

def _build_checker_items(rows, include_cancelled=True, collapse_voids=True, printed_only=True):
    """
    Build checker lines, merging items with same (name, sauce, note).

    - Positive qty lines are aggregated.
    - If collapse_voids is False, void lines are also aggregated per key.
    """
    from collections import OrderedDict

    # key -> aggregated item dict
    groups = OrderedDict()

    def _as_float(v):
        try:
            if v is None:
                return 0.0
            if isinstance(v, str):
                s = v.strip()
                return float(s) if s else 0.0
            from decimal import Decimal
            from numbers import Number
            if isinstance(v, (int, float, Decimal, Number)):
                return float(v)
            return float(v)
        except Exception:
            return 0.0

    def add_line(name, qty, sauce, note, is_void=False):
        # Normalize note once for the grouped line
        note_str   = note or ""
        note_lines = _normalize_note_lines(note_str)

        # key: same name + sauce + note; separate bucket for void vs non-void
        key = (name, sauce or None, note_str, bool(is_void))

        if key not in groups:
            groups[key] = {
                "name": name,
                "qty": 0.0,
                "sauce": sauce or None,
                "note_lines": note_lines,
            }
            if is_void:
                groups[key]["_void"] = True

        groups[key]["qty"] += qty

    for r in rows:
        name, qty, note, void_qty, status = _row_extract(r)

        pre = _as_float(qty)
        vq  = _as_float(void_qty)
        is_cancelled = (status == "cancelled")

        # Cancelled rows with zero qty/void were never printed; skip them.
        if is_cancelled and pre == 0 and vq == 0:
            continue

        if not include_cancelled and is_cancelled:
            continue

        # printed_only filter (same logic as before)
        printed_ok = (status in PRINTED_STATUSES)
        try:
            printed_qty = float(
                (r.get("printed_qty") if isinstance(r, dict) else getattr(r, "printed_qty", 0)) or 0
            )
        except Exception:
            printed_qty = 0.0
        cancelled_with_qty = is_cancelled and (abs(pre) > 0 or abs(vq) > 0)

        if printed_only and not (printed_ok or printed_qty > 0 or cancelled_with_qty):
            continue

        # Optional sauce
        try:
            sauce = (r.get("sauce") if isinstance(r, dict) else (r[5] if len(r) > 5 else None)) or None
        except Exception:
            sauce = None

        # 1) aggregate PRE-VOID qty for this row
        if pre > 0:
            add_line(name, pre, sauce, note, is_void=False)

        # 2) Optional explicit VOID line(s), aggregated separately
        if not collapse_voids and vq > 0:
            add_line(name, -vq, sauce, note, is_void=True)

    # Return aggregated lines in first-seen order
    return list(groups.values())


def _staff_display_name(full_name, username, fallback="Unknown"):
    label = (full_name or "").strip()
    if label:
        return label
    label = (username or "").strip()
    if label:
        return label
    return fallback


def _fetch_admin_checker_rows(session_id):
    from psycopg.rows import dict_row

    with db.connect_db(None) as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute(
            """
            SELECT
                oi.id,
                oi.item_name,
                oi.qty,
                oi.price,
                oi.total_price,
                oi.sauce,
                oi.note,
                oi.status,
                oi."timestamp",
                oi.bill_group,
                COALESCE(oi.void_qty, 0) AS void_qty,
                oi.table_number,
                oi.created_by_user_id,
                oi.updated_by_user_id,
                cu.full_name AS created_by_full_name,
                cu.username  AS created_by_username,
                uu.full_name AS updated_by_full_name,
                uu.username  AS updated_by_username
            FROM public.order_items oi
            LEFT JOIN public.users cu ON cu.id = oi.created_by_user_id
            LEFT JOIN public.users uu ON uu.id = oi.updated_by_user_id
            WHERE oi.session_id = %s
            ORDER BY oi."timestamp" ASC, oi.id ASC
            """,
            (session_id,),
        )
        return c.fetchall() or []


def _row_is_printed_scope(row):
    status = str((row.get("status") if isinstance(row, dict) else "") or "").strip().lower()
    qty = float((row.get("qty") if isinstance(row, dict) else 0) or 0)
    void_qty = float((row.get("void_qty") if isinstance(row, dict) else 0) or 0)
    printed_qty = 0.0
    if isinstance(row, dict):
        try:
            printed_qty = float(row.get("printed_qty") or 0)
        except Exception:
            printed_qty = 0.0
    if status in PRINTED_STATUSES:
        return True
    if printed_qty > 0:
        return True
    if status == "cancelled" and (abs(qty) > 0 or abs(void_qty) > 0):
        return True
    return False


def _build_admin_checker_payload(rows, *, printed_only=True):
    sections = OrderedDict((
        ("ADD", OrderedDict()),
        ("EDIT", OrderedDict()),
        ("VOID", OrderedDict()),
    ))
    details = []

    def _float(v):
        try:
            return float(v or 0)
        except Exception:
            return 0.0

    def _bump(section_key, staff_name, *, qty=0.0, lines=0):
        if not staff_name:
            return
        bucket = sections[section_key].setdefault(staff_name, {"qty": 0.0, "lines": 0})
        bucket["qty"] += max(0.0, qty)
        bucket["lines"] += int(lines)

    for row in rows or []:
        if printed_only and not _row_is_printed_scope(row):
            continue

        name = str(row.get("item_name") or "").strip()
        if not name:
            continue

        qty = _float(row.get("qty"))
        void_qty = _float(row.get("void_qty"))
        status = str(row.get("status") or "").strip().lower()
        note_lines = _normalize_note_lines(row.get("note") or "")

        if qty <= 0 and void_qty <= 0:
            continue

        added_by = _staff_display_name(row.get("created_by_full_name"), row.get("created_by_username"), fallback="")
        updated_by = _staff_display_name(row.get("updated_by_full_name"), row.get("updated_by_username"), fallback="")

        if qty > 0 and added_by:
            _bump("ADD", added_by, qty=qty, lines=1)

        is_void_row = void_qty > 0 or (status == "cancelled" and qty > 0)
        void_amount = void_qty if void_qty > 0 else (qty if status == "cancelled" else 0.0)
        void_by = updated_by if is_void_row else ""
        if void_amount > 0 and void_by:
            _bump("VOID", void_by, qty=void_amount, lines=1)

        edit_by = ""
        if updated_by and status in {"edited", "partial", "printed_partial"} and updated_by != added_by:
            edit_by = updated_by
            _bump("EDIT", edit_by, lines=1)

        details.append({
            "name": name,
            "qty": qty,
            "void_qty": void_amount,
            "added_by": added_by or "-",
            "edited_by": edit_by,
            "void_by": void_by,
            "note_lines": note_lines,
        })

    summary_sections = []
    for title, staff_map in sections.items():
        if not staff_map:
            continue
        rows_out = []
        for staff_name, stats in staff_map.items():
            line_count = int(stats["lines"])
            parts = [f"{line_count} line" + ("" if line_count == 1 else "s")]
            if title in {"ADD", "VOID"} and stats["qty"] > 0:
                parts.append(f"{stats['qty']:g} qty")
            rows_out.append({"name": staff_name, "meta": " / ".join(parts)})
        summary_sections.append({"title": title, "rows": rows_out})

    return {"sections": summary_sections, "details": details}

import re
_DOT_RE = re.compile(r'\s*\(dot\)\s*', re.IGNORECASE)

def _normalize_note_lines(note: str):
    if not note:
        return []
    s = str(note)

    # Remove any machine-only station hint token so it doesn't appear on printed tickets
    try:
        s = re.sub(r'^\s*\[\[station:[A-Za-z0-9_\-]+\]\]\s*', '', s)
    except Exception:
        pass

    # standardize separators and "(dot)" -> newline
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = s.replace(';', '\n').replace('|', '\n').replace('•', '\n')
    s = _DOT_RE.sub('\n', s)

    out = []
    for p in (t.strip() for t in s.split('\n')):
        if not p:
            continue
        q = (p.replace('Rp','').replace('rp','')
               .replace('.','').replace(',','').replace(' ',''))
        if q.isdigit():           # looks like a pure price -> drop
            continue
        out.append(p)
    return out

def _decorate_items_with_notes(items):
    """Add note_lines for the Jinja template."""
    out = []
    for it in items or []:
        note = (it.get("note") or "").strip()
        out.append({**it, "note_lines": _normalize_note_lines(note)})
    return out

def _split_map_for_session(session_id):
    try:
        raw = db.get_split_labels(None, session_id) or []
    except Exception:
        raw = []
    return split_meta_map(raw)

def _split_label_for_group(group_key, split_map):
    if not group_key:
        return None
    name = (split_map.get(group_key) or "").strip()
    return name or str(group_key)

def _group_items_by_split(items):
    grouped = OrderedDict()
    for it in items or []:
        grouped.setdefault(it.get("group"), []).append(it)
    return grouped

def _split_label_from_rows(rows, split_map):
    groups = []
    for r in (rows or []):
        g = normalize_group(r[7] if len(r) > 7 else None)
        if g:
            groups.append(g)
    uniq = {g for g in groups if g}
    if len(uniq) == 1:
        return _split_label_for_group(next(iter(uniq)), split_map)
    return None

def _session_meta_for_checker(session_id):
    dp_total = db.get_dp_amount(None, session_id) or 0
    dp_used  = db.get_dp_used(None, session_id) or 0
    dp_rem   = max(int(dp_total) - int(dp_used), 0)

    conn = db.connect_db(None)
    res_row = None
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT
                    COALESCE(pax,1),
                    COALESCE(guest_name,''),
                    COALESCE(note,''),
                    COALESCE(service_type::text,'dine_in'),
                    COALESCE(table_number::text,'')
                  FROM public.sessions
                 WHERE id=%s
            """, (session_id,))
            row = c.fetchone() or (1, "", "", "dine_in", "")

            c.execute("""
                SELECT id, table_number, date, time
                  FROM public.reservations
                 WHERE session_id=%s
                   AND COALESCE(status,'') IN ('seated','confirmed','pending')
                 ORDER BY id DESC
                 LIMIT 1
            """, (session_id,))
            res_row = c.fetchone()
            is_res = bool(res_row)
    finally:
        conn.close()

    # use your existing splitter so notes can be multi-line
    note_lines = _normalize_note_lines(row[2] or "")
    svc_type   = (row[3] or "dine_in").strip().lower()
    tbl_raw    = row[4]

    def _table_label_for_print(table_val, svc):
        s = str(table_val or "").strip()
        if svc == "takeaway":
            if s.lower() == "ta" or s == "":
                return "Take Away"
        return s

    def _fmt_rp(n: int) -> str:
        return f"Rp {int(n):,}".replace(",", ".")

    res_table = None
    res_date = None
    res_time = None
    if res_row:
        res_table = res_row[1]
        res_date = res_row[2]
        res_time = res_row[3]

    def _fmt_time(val):
        if val is None:
            return None
        try:
            return val.strftime("%H:%M")
        except Exception:
            s = str(val)
            return s[:5] if len(s) >= 5 else s

    def _fmt_date(val):
        if val is None:
            return None
        try:
            return val.strftime("%Y-%m-%d")
        except Exception:
            return str(val)

    return {
        "pax": int(row[0] or 1),
        "guest_name": (row[1] or None) or None,
        "session_note": row[2] or "",
        "session_note_lines": note_lines,        
        "dp_total": int(dp_total),
        "dp_remaining": int(dp_rem),
        "dp_total_fmt": _fmt_rp(dp_total),
        "dp_remaining_fmt": _fmt_rp(dp_rem),
        "is_reservation": is_res,             
        "reservation_table_number": (str(res_table) if res_table is not None else None),
        "reservation_date": _fmt_date(res_date),
        "reservation_time": _fmt_time(res_time),
        "service_type": svc_type,
        "table_label": _table_label_for_print(tbl_raw, svc_type),
        "table_number": tbl_raw,
    }


def _kitchen_table_display(meta, table_number):
    res_tbl = (meta.get("reservation_table_number") or "").strip()
    if res_tbl:
        return res_tbl
    return meta.get("table_label") or table_number


def _build_kitchen_header(
    meta,
    table_number,
    *,
    title,
    is_void=False,
    split_label=None,
    prepared_by=None,
    printed_at=None,
):
    table_display = _kitchen_table_display(meta, table_number)
    return {
        "table_number": table_display,
        "table_label": table_display,
        "printed_at": printed_at or fmt_now(),
        "title": title,
        "is_void": is_void,
        "prepared_by": prepared_by,
        "split_label": split_label,
        "guest_name": meta.get("guest_name"),
        "pax": meta.get("pax"),
        "dp_total_fmt": meta.get("dp_total_fmt"),
        "dp_remaining_fmt": meta.get("dp_remaining_fmt"),
        "is_reservation": meta.get("is_reservation"),
        "reservation_time": meta.get("reservation_time"),
        "reservation_table_number": meta.get("reservation_table_number"),
        "table_note_lines": meta.get("session_note_lines"),
        "is_takeaway": (meta.get("service_type") == "takeaway"),
    }


@bp.get("/print/checker/preview/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def checker_preview(session_id):
    include_cancelled = request.args.get("include_cancelled", "1") != "0"
    collapse_voids    = request.args.get("collapse_voids", "1") != "0"
    printed_only      = request.args.get("printed_only", "1") != "0"

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min: abort(404)
    _sid, table_number, _ = sess_min

    groups = _parse_groups()
    rows  = _fetch_all_order_rows(session_id)
    rows  = _filter_rows_by_groups(rows, groups)
    items = _build_checker_items(rows,
                                 include_cancelled=include_cancelled,
                                 collapse_voids=collapse_voids,
                                 printed_only=printed_only)

    split_label = _split_label_for_checker(session_id, groups, rows)
    meta = _session_meta_for_checker(session_id)
    table_label = meta.get("table_label") or table_number
    is_takeaway = (meta.get("service_type") == "takeaway")
    header = {
        "table_number": table_number,
        "table_label": table_label,
        "title": "CHECKER TICKET",
        "is_void": False,
        "hide_price": True,
        "printed_at": fmt_now(),
        "guest_name": meta["guest_name"],
        "pax": meta["pax"],
        "dp_total_fmt": meta["dp_total_fmt"],
        "dp_remaining_fmt": meta["dp_remaining_fmt"],
        "is_reservation": meta["is_reservation"],           
        "table_note_lines": meta["session_note_lines"],     
        "is_takeaway": is_takeaway,
    }
    if split_label:
        header["split_label"] = split_label

    current_app.logger.info("CHECKER lines: %s", [(it["qty"], it["name"]) for it in items])
    return render_template("kitchen_chit.html", header=header, items=items)


@bp.get("/print/admin_checker/preview/<session_id>")
@login_required
@roles_required("admin")
def admin_checker_preview(session_id):
    printed_only = request.args.get("printed_only", "1") != "0"

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)
    _sid, table_number, _ = sess_min

    groups = _parse_groups()
    rows = _fetch_admin_checker_rows(session_id)
    rows = _filter_rows_by_groups(rows, groups)
    payload_data = _build_admin_checker_payload(rows, printed_only=printed_only)
    split_label = _split_label_for_checker(session_id, groups, rows)

    meta = _session_meta_for_checker(session_id)
    header = {
        "table_number": table_number,
        "table_label": meta.get("table_label") or table_number,
        "title": "ADMIN CHECKER",
        "printed_at": fmt_now(),
        "guest_name": meta.get("guest_name"),
        "pax": meta.get("pax"),
        "is_takeaway": (meta.get("service_type") == "takeaway"),
    }
    if split_label:
        header["split_label"] = split_label

    return render_template(
        "admin_checker.html",
        header=header,
        sections=payload_data.get("sections") or [],
        details=payload_data.get("details") or [],
    )



@bp.get("/print/qr_checker/preview/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def qr_checker_preview(session_id):
    only_unprinted = request.args.get("unprinted", "1") != "0"

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)
    _sid, table_number, _ = sess_min

    rows = _fetch_qr_order_rows(session_id, only_unprinted=only_unprinted)
    items = _build_checker_items(
        rows,
        include_cancelled=False,
        collapse_voids=True,
        printed_only=False
    )

    meta = _session_meta_for_checker(session_id)
    table_label = meta.get("table_label") or table_number
    is_takeaway = (meta.get("service_type") == "takeaway")
    header = {
        "table_number": table_number,
        "table_label": table_label,
        "title": "QR CHECK" + (" (UNSENT)" if only_unprinted else ""),
        "is_void": False,
        "hide_price": True,
        "printed_at": fmt_now(),
        "guest_name": meta["guest_name"],
        "pax": meta["pax"],
        "dp_total_fmt": meta["dp_total_fmt"],
        "dp_remaining_fmt": meta["dp_remaining_fmt"],
        "is_reservation": meta["is_reservation"],
        "table_note_lines": meta["session_note_lines"],
        "prepared_by": (os.getenv("QR_USERNAME") or "qr_service"),
        "is_takeaway": is_takeaway,
    }

    current_app.logger.info("QR CHECKER lines: %s", [(it["qty"], it["name"]) for it in items])
    return render_template("kitchen_chit.html", header=header, items=items)


@bp.post("/print/checker/send/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter")
def print_checker(session_id):
    payload = request.get_json(silent=True) or {}
    only_local        = bool(payload.get("only_local", True))
    include_cancelled = bool(payload.get("include_cancelled", True))
    collapse_voids    = bool(payload.get("collapse_voids", True))
    printed_only      = bool(payload.get("printed_only", True))  # <-- default True
    server_station    = (payload.get("server_station") or "expediter").strip().lower()
    groups = _parse_groups()
    if not groups:
        payload_groups = payload.get("group") or payload.get("groups")
        if isinstance(payload_groups, (list, tuple, set)):
            groups = [str(g).strip() for g in payload_groups if str(g).strip()]
        elif payload_groups:
            groups = [g.strip() for g in str(payload_groups).split(",") if g.strip()]

    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        return jsonify({"status": "error", "message": "session not found"}), 404
    _sid, table_number, _ = sess_min

    rows  = _fetch_all_order_rows(session_id)
    rows  = _filter_rows_by_groups(rows, groups)
    items = _build_checker_items(
        rows,
        include_cancelled=include_cancelled,
        collapse_voids=collapse_voids,
        printed_only=printed_only
    )

    if not items:
        return jsonify({"status": "nothing_to_print"}), 200

    if only_local:
        from urllib.parse import urlencode
        qs_params = {
            "include_cancelled": "1" if include_cancelled else "0",
            "collapse_voids":    "1" if collapse_voids    else "0",
            "printed_only":      "1" if printed_only      else "0",
        }
        if groups:
            qs_params["group"] = groups
        qs = urlencode(qs_params, doseq=True)
        url = f"/print/checker/preview/{session_id}?{qs}"
        return jsonify({"status": "preview", "preview_url": url})

    try:
        split_label = _split_label_for_checker(session_id, groups, rows)
        meta = _session_meta_for_checker(session_id)       
        table_label = meta.get("table_label") or table_number
        is_takeaway = (meta.get("service_type") == "takeaway")
        header = {
            "table_number": table_number,
            "table_label": table_label,
            "printed_at": fmt_now(),
            "title": "CHECKER TICKET",
            "is_void": False,
            "hide_price": True,
            "guest_name": meta["guest_name"],              
            "pax": meta["pax"],                             
            "dp_total_fmt": meta["dp_total_fmt"],           
            "dp_remaining_fmt": meta["dp_remaining_fmt"],   
            "is_reservation": meta["is_reservation"],       
            "table_note_lines": meta["session_note_lines"], 
            "is_takeaway": is_takeaway,
        }
        if split_label:
            header["split_label"] = split_label
        station_key = server_station or "expediter"
        _print_ticket_for_station(station_key, table_number, header, items)
        return jsonify({"status": "sent", "station": station_key})
    
    except Exception as e:
        current_app.logger.exception("print_checker server print failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.post("/print/qr/<table>/<session_id>")
@login_required
@roles_required("admin", "cashier", "waiter", "viewer")
def print_qr_direct(table, session_id):
    url = build_qr_order_url(table, session_id)
    png = qr_bytes(url)
    try:
        job = printing.print_png_bytes(png, printer_key=_default_printer_id())
        return jsonify({"status": "printed", "job": job})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
