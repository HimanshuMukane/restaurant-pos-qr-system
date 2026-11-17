import os, json, re
from datetime import datetime
from copy import deepcopy
from flask import Blueprint, request, render_template, redirect, url_for, jsonify, current_app, abort
from utils import db
from utils.tenancy import get_current_tenant_id, set_current_tenant_id
from ..helpers import get_qr_session_mode
from ..events import session_items_changed  
from ..socketbus import _push_state

bp = Blueprint("qr_public", __name__)

DEFAULT_LANG = os.getenv("QR_LANG", "en")
DEFAULT_GUEST = os.getenv("QR_GUEST_NAME", "Guest")

def _load_menu():
    tid = get_current_tenant_id()
    # Check if tenant has customized menu file: static/defaults/menu_<tenant>.json or static/menu.json
    custom_path = f"static/defaults/menu_{tid}.json"
    if os.path.exists(custom_path):
        with open(custom_path, "r", encoding="utf-8") as f:
            return json.load(f)
    with open("static/menu.json", "r", encoding="utf-8") as f:
        return json.load(f)

def _filter_menu_for_qr(menu):
    out = {}
    for cat, items in menu.items():
        keep = {}
        for item_name, meta in items.items():
            if meta.get("qr_render") is False:
                continue
            if meta.get("available") is False:
                continue
            m = dict(meta)
            norm = []
            for d in (m.get("dishes") or []):
                if isinstance(d, str):
                    norm.append({"name": d, "available": True})
                else:
                    dd = dict(d)
                    if "available" not in dd:
                        dd["available"] = True
                    if dd["available"]:
                        norm.append(dd)
            m["dishes"] = norm
            keep[item_name] = m
        if keep:
            out[cat] = keep
    return out

def _resolve_price(menu, base_item, dish_name=None):
    for items in menu.values():
        itm = items.get(base_item)
        if not itm:
            continue
        if dish_name:
            for d in (itm.get("dishes") or []):
                dn = d["name"] if isinstance(d, dict) else str(d)
                if dn.strip().lower() == dish_name.strip().lower():
                    po = d.get("price_override") if isinstance(d, dict) else None
                    if po is not None:
                        return int(po)
        return int(itm.get("price_per_kg") or 0)
    return 0

def _compose_display_name(base_item, dish_name):
    return dish_name.strip() if dish_name else base_item

def parse_portion_bounds(meta):
    mn = meta.get("portion_ons_min")
    mx = meta.get("portion_ons_max")
    if isinstance(mn, int) and mn > 0:
        if not (isinstance(mx, int) and mx >= mn):
            mx = mn
        return mn, mx

    pinfo = (meta.get("portion_info") or "").lower()
    m_pm = re.search(r"±\s*(\d+)\s*on", pinfo)
    m_rg = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*on", pinfo)
    m_sg = re.search(r"\b(\d+)\s*on", pinfo)

    if m_rg:
        try:
            a, b = int(m_rg.group(1)), int(m_rg.group(2))
            if a > 0 and b >= a:
                return a, b
        except Exception:
            pass
    if m_pm:
        try:
            base = int(m_pm.group(1))
            if base > 0:
                return base, max(base, base + 2)
        except Exception:
            pass
    if m_sg:
        try:
            base = int(m_sg.group(1))
            if base > 0:
                return base, max(base, base + 2)
        except Exception:
            pass
    return 3, 5

def compute_price_per_ons(meta):
    pkg = int(meta.get("price_per_kg") or 0)
    return int(round(pkg / 10)) if pkg > 0 else None

def enrich_menu_for_portions(menu):
    m2 = deepcopy(menu)
    for cat, items in m2.items():
        for name, meta in items.items():
            per_ons = compute_price_per_ons(meta)
            mn, mx = parse_portion_bounds(meta)
            meta["price_per_ons"]   = per_ons
            meta["portion_ons_min"] = mn
            meta["portion_ons_max"] = mx
    return m2

def _require_token():
    token = request.args.get("token") or request.headers.get("X-QR-Token")
    conf = current_app.config.get("QR_TOKEN") or os.getenv("QR_TOKEN", "")
    if conf and token != conf:
        abort(401, "invalid token")

@bp.get("/qr/menu.json")
def qr_menu():
    """Public, cacheable menu for QR app."""
    return jsonify(_filter_menu_for_qr(_load_menu()))

@bp.get("/qr/session_summary.json")
def qr_session_summary():
    sid = (request.args.get("session") or "").strip()
    if not sid:
        return jsonify({"status": "error", "message": "session required"}), 400
    detail = db.get_session_detail(None, sid)
    if not detail:
        return jsonify({"status": "not_found", "session_id": sid}), 404
    # detail: pax, guest_name, dp_amount, note, created_at, status, closed_at
    return jsonify({
        "status": "ok",
        "session_id": sid,
        "pax": detail[0],
        "guest_name": detail[1],
        "dp_amount": detail[2],
        "note": detail[3],
        "created_at": str(detail[4]) if detail[4] else None,
        "session_status": detail[5]
    })

@bp.get("/qr/table_session.json")
def qr_table_session():
    _require_token()
    table_number = (request.args.get("table") or "").strip()
    if not table_number:
        return jsonify({"status": "error", "message": "table required"}), 400
    session_id = db.get_session_by_table(None, table_number)
    if not session_id:
        return jsonify({"status": "not_found", "session_id": None}), 404
    return jsonify({"status": "ok", "session_id": session_id})

@bp.post("/api/qr/order")
def api_qr_order():
    _require_token()
    body = request.get_json(force=True, silent=True) or {}
    table_number = str(body.get("table_number") or "").strip()
    if not table_number:
        return jsonify({"status": "error", "message": "table_number required"}), 400

    session_id = (body.get("session_id") or "").strip() or None
    guest_name = (body.get("guest_name") or "QR Guest").strip()
    items_in   = body.get("items") or []
    if not items_in:
        return jsonify({"status": "error", "message": "no items"}), 400

    # 1) Find or create target session
    if session_id:
        sess = db.get_session_detail(None, session_id)
        if not sess:
            return jsonify({"status": "error", "message": "session not found"}), 404
        if (sess[5] or "").lower() != "active":
            return jsonify({"status": "error", "message": "session not active"}), 400

        conn_chk = db.connect_db(None)
        c_chk = conn_chk.cursor()
        try:
            c_chk.execute("SELECT table_number FROM sessions WHERE id=%s", (session_id,))
            row = c_chk.fetchone()
        finally:
            conn_chk.close()
        if not row:
            return jsonify({"status": "error", "message": "session not found"}), 404
        if str(row[0]) != str(table_number):
            return jsonify({"status": "error", "message": "session does not belong to this table"}), 400
    else:
        existing = db.get_session_by_table(None, table_number)
        if existing:
            session_id = existing
        else:
            if get_qr_session_mode() == "table":
                return jsonify({"status": "error", "message": "no active session for table"}), 409
            uid = int(os.getenv("QR_USER_ID", "1"))
            session_id = db.create_session(
                None,
                table_number,
                pax=1,
                guest_name=guest_name,
                dp_amount=0,
                note="QR Order",
                opened_by_user_id=uid
            )
            try:
                from ..events import session_created
                session_created(table_number, session_id, pax=1, guest_name=guest_name)
            except Exception:
                pass

    menu = _filter_menu_for_qr(_load_menu())
    qr_user_id = int(os.getenv("QR_USER_ID", "1"))
    inserted = 0

    for it in items_in:
        raw_name = (it.get("item_name") or it.get("item") or "").strip()
        if not raw_name:
            continue
        note      = (it.get("note")  or "").strip() or None
        bill_group = (it.get("bill_group") or "").strip() or "main"

        base, dish = raw_name, None
        if "—" in raw_name:
            parts = [p.strip() for p in raw_name.split("—", 1)]
            base, dish = parts[0], (parts[1] if len(parts) > 1 else None)
        elif " - " in raw_name:
            parts = [p.strip() for p in raw_name.split(" - ", 1)]
            base, dish = parts[0], (parts[1] if len(parts) > 1 else None)

        try:
            qty = float(it.get("qty") or 1)
        except Exception:
            qty = 1.0
        if qty <= 0:
            continue

        unit_price = _resolve_price(menu, base, dish)
        display_name = _compose_display_name(base, dish)

        db.insert_order_item(
            None,
            session_id,
            table_number,
            display_name,
            qty,
            unit_price,
            sauce=None,
            note=note,
            created_by_user_id=qr_user_id,
            bill_group=bill_group
        )
        inserted += 1

    try:
        session_items_changed(table_number, session_id)
        _push_state(session_id)  
    except Exception:
        current_app.logger.exception("add_order: session_items_changed failed (non-fatal)")

    return jsonify({"status": "ok", "session_id": session_id, "inserted": inserted})


# =========================================================================
# QR DIRECT ENDPOINTS (Integrated from repo-open-qr for single runtime)
# =========================================================================

@bp.route("/order/<table>/<session_id>", methods=["GET"])
def order(table, session_id):
    lang = request.args.get("lang", DEFAULT_LANG)
    base_menu = _filter_menu_for_qr(_load_menu())
    menu = enrich_menu_for_portions(base_menu)

    guest_name = None
    try:
        detail = db.get_session_detail(None, session_id)
        if detail:
            guest_name = detail[1]
    except Exception:
        pass

    item_translations = {}
    item_translations_lower = {}
    category_translations = {}
    category_translations_rev = {}

    return render_template(
        "order.html",
        table=table,
        session=session_id,
        lang=lang,
        language=lang,
        menu=menu,
        hours=None,
        guest_name=guest_name,
        category_translations=category_translations,
        category_translations_rev=category_translations_rev,
        item_translations=item_translations,
        item_translations_lower=item_translations_lower,
        cart_poll_ms=3000,
    )

@bp.route("/cart", methods=["GET"])
def show_cart():
    table   = request.args.get("table")
    session_id = request.args.get("session")
    lang    = request.args.get("lang", DEFAULT_LANG)

    if not table or not session_id:
        return "Missing table or session", 400

    return render_template("cart.html", table=table, session=session_id, language=lang)

@bp.route("/submit", methods=["POST"])
def submit():
    try:
        cart = json.loads(request.form.get("cart_data", "[]"))
    except json.JSONDecodeError:
        return "Invalid cart data", 400
    if not cart:
        return "Cart is empty", 400

    table      = (request.form.get("table") or "").strip()
    session_id = (request.form.get("session") or "").strip()
    lang       = request.form.get("lang", DEFAULT_LANG)
    guest_name = (request.form.get("guest_name") or DEFAULT_GUEST).strip()

    items = []
    for it in cart:
        name_for_pos = it.get("item") or it.get("item_name")
        qty = int(it.get("qty") or 1)
        items.append({
            "item_name": name_for_pos,
            "qty": qty,
            "note": it.get("note") or "",
        })

    # Internal dispatch to order processing logic
    menu = _filter_menu_for_qr(_load_menu())
    qr_user_id = int(os.getenv("QR_USER_ID", "1"))

    # If session doesn't exist yet, open it
    if not session_id:
        existing = db.get_session_by_table(None, table)
        if existing:
            session_id = existing
        else:
            session_id = db.create_session(
                None,
                table,
                pax=1,
                guest_name=guest_name,
                dp_amount=0,
                note="QR Order",
                opened_by_user_id=qr_user_id
            )

    for it in items:
        raw_name = it["item_name"]
        qty = it["qty"]
        note = it["note"]
        unit_price = _resolve_price(menu, raw_name)
        db.insert_order_item(
            None,
            session_id,
            table,
            raw_name,
            qty,
            unit_price,
            sauce=None,
            note=note,
            created_by_user_id=qr_user_id,
            bill_group="main"
        )

    try:
        session_items_changed(table, session_id)
        _push_state(session_id)
    except Exception:
        pass

    redirect_url = url_for("qr_public.order", table=table, session_id=session_id, lang=lang)
    sep = "&" if "?" in redirect_url else "?"
    redirect_url = f"{redirect_url}{sep}submitted=1"
    return render_template("submitted_redirect.html", redirect_url=redirect_url)

@bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    table = request.args.get("table", "")
    session_id = request.args.get("session", "")
    tenant_id = get_current_tenant_id()

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "Anonymous")
        table_number = request.form.get("table", table)
        sess_id = request.form.get("session", session_id)
        rating = int(request.form.get("rating", 5))
        food_rating = int(request.form.get("food_rating", 5))
        service_rating = int(request.form.get("service_rating", 5))
        comments = request.form.get("comments", "").strip()

        with db.connect_db() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tenant_feedback (tenant_id, table_number, session_id, customer_name, rating, food_rating, service_rating, comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (tenant_id, table_number, sess_id, customer_name, rating, food_rating, service_rating, comments))
            conn.commit()

        return render_template("feedback_thanks.html", table=table_number, session=sess_id)

    return render_template("feedback.html", table=table, session=session_id)

@bp.get("/api/feedback")
def api_list_feedback():
    tenant_id = get_current_tenant_id()
    with db.connect_db() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, tenant_id, table_number, session_id, customer_name, rating, food_rating, service_rating, comments, created_at
            FROM tenant_feedback
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 100
        """, (tenant_id,))
        rows = cur.fetchall()
        return jsonify({"status": "ok", "feedback": [dict(r) for r in rows]})
