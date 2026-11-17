import json, os
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from ..authz import roles_required

bp = Blueprint("menu", __name__)

@bp.get("/api/menu")
@login_required
@roles_required("admin", "cashier")
def api_get_menu():
    with open("static/menu.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@bp.patch("/api/menu/item")
@login_required
@roles_required("admin", "cashier")
def api_patch_item():
    body = request.get_json() or {}
    category = body.get("category")
    item = body.get("item")
    if not category or not item:
        return jsonify({"status": "error", "message": "category and item required"}), 400
    path = "static/menu.json"
    with open(path, "r", encoding="utf-8") as f:
        menu = json.load(f)
    if category not in menu or item not in menu[category]:
        return jsonify({"status": "error", "message": "not found"}), 404
    itm = menu[category][item]
    if "available" in body:
        itm["available"] = bool(body["available"])
    if "price_per_kg" in body:
        price = int(body["price_per_kg"])
        if price < 0:
            return jsonify({"status": "error", "message": "invalid price"}), 400
        itm["price_per_kg"] = price
    if "qr_render" in body:
        qr = body.get("qr_render")
        if qr is None:
            itm.pop("qr_render", None)   # unset -> default true
        else:
            itm["qr_render"] = bool(qr)
    if "printer_override" in body:
        ov = body.get("printer_override")
        if ov is None or str(ov).strip() == "":
            itm.pop("printer_override", None)
        else:
            itm["printer_override"] = str(ov).strip()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(menu, f, ensure_ascii=False, indent=2)
        f.flush()
        import os
        os.fsync(f.fileno())
    import os
    os.replace(tmp, path)
    return jsonify({"status": "ok"})

@bp.patch("/api/menu/dish")
@login_required
@roles_required("admin", "cashier")
def api_patch_dish():
    body = request.get_json() or {}
    category, item, name = body.get("category"), body.get("item"), body.get("name")
    if not all([category, item, name]):
        return jsonify({"status": "error", "message": "category, item, name required"}), 400
    path = "static/menu.json"
    with open(path, "r", encoding="utf-8") as f:
        menu = json.load(f)
    if category not in menu or item not in menu[category]:
        return jsonify({"status": "error", "message": "not found"}), 404
    dishes = menu[category][item].get("dishes", [])
    fixed = []
    for d in dishes:
        if isinstance(d, str):
            fixed.append({"name": d, "available": True})
        else:
            if "available" not in d:
                d["available"] = True
            fixed.append(d)
    dishes = fixed
    target = next((d for d in dishes if d.get("name") == name), None)
    if not target:
        return jsonify({"status": "error", "message": "dish not found"}), 404
    if "available" in body:
        target["available"] = bool(body["available"])
    if "price_override" in body:
        po = body["price_override"]
        if po is None:
            target.pop("price_override", None)
        else:
            po = int(po)
            if po < 0:
                return jsonify({"status": "error", "message": "invalid price"}), 400
            target["price_override"] = po
    if "printer_override" in body:
        ov = body.get("printer_override")
        if ov is None or str(ov).strip() == "":
            target.pop("printer_override", None)
        else:
            target["printer_override"] = str(ov).strip()
    menu[category][item]["dishes"] = dishes
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(menu, f, ensure_ascii=False, indent=2)
        f.flush()
        import os
        os.fsync(f.fileno())
    import os
    os.replace(tmp, path)
    return jsonify({"status": "ok"})

@bp.patch("/api/menu/category")
@login_required
@roles_required("admin", "cashier")
def api_patch_category():
    body = request.get_json() or {}
    category = (body.get("category") or "").strip()
    if not category:
        return jsonify({"status": "error", "message": "category required"}), 400

    path = "static/menu.json"
    with open(path, "r", encoding="utf-8") as f:
        menu = json.load(f)
    if category not in menu:
        return jsonify({"status": "error", "message": "category not found"}), 404

    # validate inputs (optional keys)
    if "price_per_kg" in body:
        try:
            price = int(body["price_per_kg"])
            if price < 0: raise ValueError()
        except Exception:
            return jsonify({"status": "error", "message": "invalid price"}), 400

    updated = 0
    for item_name, itm in menu[category].items():
        if "available" in body:
            itm["available"] = bool(body["available"])
        if "price_per_kg" in body:
            itm["price_per_kg"] = int(body["price_per_kg"])
        updated += 1

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(menu, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    return jsonify({"status": "ok", "updated_items": updated})


@bp.post("/api/menu/item")
@login_required
@roles_required("admin", "cashier")
def api_add_item():
    b = request.get_json() or {}
    required = ["category", "item", "price_per_kg", "portion_info", "unit"]
    if any(k not in b or b[k] in (None, "") for k in required):
        return jsonify({"status": "error", "message": "missing fields"}), 400
    category, item = b["category"], b["item"]
    price = int(b["price_per_kg"])
    if price < 0:
        return jsonify({"status": "error", "message": "invalid price"}), 400
    path = "static/menu.json"
    with open(path, "r", encoding="utf-8") as f:
        menu = json.load(f)
    if category not in menu:
        menu[category] = {}
    if item in menu[category]:
        return jsonify({"status": "error", "message": "item already exists"}), 409
    available = bool(b.get("available", True))
    qr_render = b.get("qr_render", None)
    dishes_in = b.get("dishes", [])
    dishes = []
    for d in dishes_in:
        if isinstance(d, str):
            dishes.append({"name": d, "available": True})
        else:
            if "name" not in d:
                return jsonify({"status": "error", "message": "dish name required"}), 400
            if "available" not in d:
                d["available"] = True
            dishes.append(d)
    printer_override = str(b["printer_override"]).strip() if b.get("printer_override") not in (None, "") else None
    base_item = {
        "price_per_kg": price,
        "portion_info": b["portion_info"],
        "unit": b["unit"],
        "available": available,
        "dishes": dishes,
    }
    if printer_override:
        base_item["printer_override"] = printer_override
    if qr_render is not None:
        base_item["qr_render"] = bool(qr_render)
    menu[category][item] = base_item
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(menu, f, ensure_ascii=False, indent=2)
        f.flush()
        import os
        os.fsync(f.fileno())
    import os
    os.replace(tmp, path)
    return jsonify({"status": "ok"})

@bp.get("/admin/menu")
@login_required
@roles_required("admin", "cashier")
def menu_admin():
    return render_template("menu_admin.html", active_tab="menu")
