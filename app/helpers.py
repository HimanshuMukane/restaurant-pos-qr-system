import json
import os
import re
import base64
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import qrcode
from flask import current_app
from json import loads


try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Jakarta")
except Exception:
    TZ = None

_MENU_CACHE = None
_MENU_MTIME = None
QR_SETTINGS_PATH = os.getenv("QR_SETTINGS_JSON", os.path.join("static", "qr_settings.json"))

def now_wib():
    return datetime.now(TZ) if TZ else datetime.now()

def fmt_now(fmt="%d-%m-%y %H:%M"):
    return now_wib().strftime(fmt)

def qty_half_step(v):
    try:
        if isinstance(v, str):
            v = v.strip().replace(",", ".")
        x = float(v)
    except Exception:
        return None
    if abs(x * 2 - round(x * 2)) > 1e-9:
        return None
    return round(x * 2) / 2.0


def fmt_dt(value, fmt: str = "%d-%m-%Y %H:%M") -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except Exception:
            return "-"
    # If your DB stores naive timestamps, assume WIB for display
    if TZ and dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.strftime(fmt)

def load_menu():
    global _MENU_CACHE, _MENU_MTIME
    path = os.path.join("static", "menu.json")
    try:
        mtime = os.path.getmtime(path)
    except Exception:
        mtime = None
    if _MENU_CACHE is not None and _MENU_MTIME == mtime:
        return _MENU_CACHE
    with open(path, "r", encoding="utf-8") as f:
        _MENU_CACHE = json.load(f)
        _MENU_MTIME = mtime
    return _MENU_CACHE

def load_qr_settings():
    data = {}
    try:
        with open(QR_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {}
    except FileNotFoundError:
        data = {}
    except Exception:
        data = {}

    mode = str(data.get("qr_session_mode") or data.get("qr_mode") or "session").strip().lower()
    if mode not in ("session", "table"):
        mode = "session"
    data["qr_session_mode"] = mode
    return data

def write_qr_settings(data: dict):
    os.makedirs(os.path.dirname(QR_SETTINGS_PATH) or ".", exist_ok=True)
    tmp = QR_SETTINGS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, QR_SETTINGS_PATH)

def get_qr_session_mode() -> str:
    return (load_qr_settings().get("qr_session_mode") or "session").strip().lower()

def build_qr_order_url(table_number: str, session_id: str, lang: str | None = None) -> str:
    base = (current_app.config.get("QR_ORDER_BASE") or "").rstrip("/")
    default_lang = (current_app.config.get("QR_DEFAULT_LANG") or "id").strip().lower()
    lang = (lang or default_lang).strip().lower()
    mode = get_qr_session_mode()
    if mode == "table":
        target = f"{base}/order/{table_number}"
    else:
        target = f"{base}/order/{table_number}/{session_id}"
    return f"{target}?lang={lang}"

def find_category_for_item(base_item: str):
    menu = load_menu()
    target = (base_item or "").strip().casefold()
    def _norm(val):
        return (val or "").strip().casefold()

    for cat, items in menu.items():
        # items is a dict of item_name -> meta
        # do a case-insensitive key match
        for k, meta in items.items():
            if target == _norm(k):
                return cat

            # Also match against dish names (flattened items, e.g. Minuman variants)
            dishes = meta.get("dishes") if isinstance(meta, dict) else None
            for d in dishes or []:
                name = d if isinstance(d, str) else (d.get("name") if isinstance(d, dict) else None)
                if target and target == _norm(name):
                    return cat
    return None


def split_item_and_dish(label: str):
    parts = re.split(r"\s+[—-]\s+", (label or "").strip(), maxsplit=1)
    base = parts[0].strip() if parts else ""
    dish = parts[1].strip() if len(parts) == 2 else None
    return base, dish

def dish_display_label(base: str, dish: str | None) -> str:
    if not dish:
        return base
    d = dish.strip()
    if d.lower().startswith(base.lower() + " "):
        return d
    return f"{base} {d}"

def resolve_price_and_availability(item_label: str):
    menu = load_menu()
    parts = [p.strip() for p in (item_label or "").split("—", 1)]
    base_item = parts[0]
    dish_name = parts[1] if len(parts) == 2 else None
    for _, items in menu.items():
        if base_item in items:
            meta = items[base_item]
            item_available = bool(meta.get("available", True))
            base_price = int(meta.get("price_per_kg", 0))
            norm = normalize_dishes(meta.get("dishes"))
            if not dish_name:
                if not item_available:
                    return (None, False)
                return (base_price, True)
            target = next((d for d in norm if (d.get("name") or "").strip() == dish_name), None)
            if not target:
                return (None, False)
            if not item_available or (target.get("available") is False):
                return (None, False)
            price = int(target["price_override"]) if target.get("price_override") is not None else base_price
            return (price, True)
    return (None, False)


def normalize_dishes(dishes):
    """
    Normalize the dishes array so callers can depend on dict entries with
    a default availability flag.
    """
    norm = []
    for d in dishes or []:
        if isinstance(d, str):
            norm.append({"name": d, "available": True})
        else:
            row = dict(d)
            if "available" not in row:
                row["available"] = True
            norm.append(row)
    return norm


def printer_override_for_label(item_label: str) -> str | None:
    """
    Look up a per-item or per-dish printer override from menu.json.
    Returns a trimmed string or None if not set.
    """
    menu = load_menu()
    base, dish = split_item_and_dish(item_label)
    base_key = (base or "").strip()
    base_key_cf = base_key.casefold()
    if not base_key:
        return None

    target_meta = None
    for _, items in menu.items():
        for k, meta in items.items():
            if base_key_cf == (k or "").strip().casefold():
                target_meta = meta
                break
        if target_meta:
            break
    if not target_meta:
        # Fallback: label might be a dish name without base prefix.
        label_cf = (item_label or "").strip().casefold()
        for _, items in menu.items():
            for meta in items.values():
                dish_norm = normalize_dishes(meta.get("dishes"))
                match = next(
                    (d for d in dish_norm if (d.get("name") or "").strip().casefold() == label_cf),
                    None
                )
                if match:
                    ov = match.get("printer_override")
                    if ov:
                        s = str(ov).strip()
                        return s or None
        return None

    dish_norm = normalize_dishes(target_meta.get("dishes"))
    if dish:
        dish_lc = dish.strip().casefold()
        match = next(
            (d for d in dish_norm if (d.get("name") or "").strip().casefold() == dish_lc),
            None
        )
        if match:
            ov = match.get("printer_override")
            if ov:
                s = str(ov).strip()
                return s or None

    ov = target_meta.get("printer_override")
    if ov:
        s = str(ov).strip()
        return s or None
    return None

def menu_unit_for_label(item_label: str) -> str | None:
    """
    Resolve the menu unit for an item label (base item or dish name).
    """
    menu = load_menu()
    base, _ = split_item_and_dish(item_label)
    base_key = (base or "").strip()
    base_cf = base_key.casefold()
    if not base_key:
        return None

    target_meta = None
    for _, items in menu.items():
        for k, meta in items.items():
            if base_cf == (k or "").strip().casefold():
                target_meta = meta
                break
        if target_meta:
            break

    if not target_meta:
        label_cf = (item_label or "").strip().casefold()
        for _, items in menu.items():
            for meta in items.values():
                dish_norm = normalize_dishes(meta.get("dishes"))
                match = next(
                    (d for d in dish_norm if (d.get("name") or "").strip().casefold() == label_cf),
                    None,
                )
                if match:
                    unit = meta.get("unit")
                    if unit:
                        s = str(unit).strip()
                        return s or None
        return None

    unit = target_meta.get("unit")
    if unit:
        s = str(unit).strip()
        return s or None
    return None

def qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def qr_png_b64(url: str) -> str:
    return base64.b64encode(qr_bytes(url)).decode("utf-8")

def station_for_item(item_label: str) -> str | None:
    cfg = current_app.config.get("CATEGORY_STATION_MAP") or "{}"
    try:
        mapping = loads(cfg)
    except Exception:
        mapping = {}
    base, _ = split_item_and_dish(item_label)
    cat = (find_category_for_item(base) or "").strip().lower()
    # return None if not mapped so caller can apply routing rules
    return mapping.get(cat)


def pct_round_half_up(amount_int: int, pct: int) -> int:
    return (int(amount_int) * int(pct) + 50) // 100

def printer_key_for_station(station: str | None) -> str | None:
    """
    Resolve printing key for a station from PRINTER_KEY_MAP (JSON).
    Example PRINTER_KEY_MAP: {"kitchen":"kitchen01","bar":"bar01","fry":"fry01","rice":"rice01"}
    """
    try:
        mapping = loads(current_app.config.get("PRINTER_KEY_MAP") or "{}")
    except Exception:
        mapping = {}
    s = (station or "kitchen").strip().lower()
    return mapping.get(s)
