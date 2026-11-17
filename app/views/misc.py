import io
import json
import os
from collections import OrderedDict
from datetime import datetime

from flask import (
    Blueprint, Response, render_template, render_template_string,
    request, jsonify, abort, current_app, url_for
)
from flask_login import login_required, current_user
from ..authz import roles_required
from ..helpers import (
    qr_bytes, qr_png_b64, station_for_item, fmt_now, find_category_for_item,
    split_item_and_dish, build_qr_order_url, get_qr_session_mode
)
from utils import db
from utils.services import printing
from ..events import session_items_changed
from urllib.parse import urlencode
from ..socketbus import _push_state

bp = Blueprint("misc", __name__)


# ---------- Static/menu + QR ----------
@bp.get("/menu.json")
def serve_menu():
    return current_app.send_static_file("menu.json")

@bp.get("/qr/<table_number>/<session_id>")
@login_required
def session_qr_page(table_number, session_id):
    url = build_qr_order_url(table_number, session_id)
    qr_b64 = qr_png_b64(url)
    return render_template("qr_preview.html", qr_data=qr_b64, url=url, table=table_number, session_id=session_id)

@bp.get("/qr/<table_number>/<session_id>.png")
@login_required
def session_qr_png(table_number, session_id):
    url = build_qr_order_url(table_number, session_id)
    png = qr_bytes(url)
    return Response(
        png,
        mimetype="image/png",
        headers={"Content-Disposition": f'inline; filename="qr_{table_number}_{session_id}.png"'}
    )

@bp.get("/print/qr/preview/<table>/<session_id>")
@login_required
def qr_ticket(table, session_id):
    cfg = current_app.config
    # The URL the QR points to (used as fallback text too)
    qr_url = build_qr_order_url(table, session_id)

    # Your existing PNG generator for the QR image
    qr_png_url = url_for("session_qr_png", table_number=table, session_id=session_id)

    # Optional branding & Wi-Fi (set these in your config)
    brand_name = cfg.get("BRAND_NAME", "Demo Restaurant")
    logo_url   = cfg.get("BRAND_LOGO_URL")  
    wifi_ssid  = cfg.get("GUEST_WIFI_SSID", "Demo Restaurant")
    wifi_pass  = cfg.get("GUEST_WIFI_PASS", "demo-wifi-pass")

    issued_at  = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = get_qr_session_mode()
    short_code = str(table).upper() if mode == "table" else session_id.split("-")[0].upper()

    # autoprint=1 → window.print() on load
    autoprint = (request.args.get("autoprint") == "1")

    return render_template(
        "qr_ticket.html",
        table=table,
        session_id=session_id,
        qr_url=qr_url,
        qr_png_url=qr_png_url,
        brand_name=brand_name,
        logo_url=logo_url,
        wifi_ssid=wifi_ssid,
        wifi_pass=wifi_pass,
        issued_at=issued_at,
        short_code=short_code,
        autoprint=autoprint,
    )

@bp.route("/qr/generate", methods=["GET", "POST"])
def qr_generate():
    table = (request.values.get("table") or "").strip()
    if not table:
        return render_template_string("""
        <h3>Generate Table QR</h3>
        <form method="post">
          <input name="table" placeholder="Table number">
          <button type="submit">Generate</button>
        </form>
        """)
    mode = get_qr_session_mode()
    s = db.get_open_session_for_table(table)
    if s:
        session_id = s[0]
    elif mode == "session":
        uid = int(current_app.config.get("QR_USER_ID") or 0)
        session_id = db.open_session(table, guest_name="QR Guest", opened_by_user_id=uid)
    else:
        session_id = "table"
    target = build_qr_order_url(table, session_id)
    png_url = f"/qr/{table}/{session_id}.png"
    return render_template_string("""
    <h2>QR for Table {{table}}</h2>
    <p>Mode: {{mode}}</p>
    <p>Session: {{session}}</p>
    <p><a href="{{target}}" target="_blank">Open QR destination</a></p>
    <img src="{{png_url}}" alt="QR">
    """, table=table, session=session_id, target=target, png_url=png_url, mode=mode)
