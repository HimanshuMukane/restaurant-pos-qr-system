import json
import os
import threading
from copy import deepcopy

CONFIG_PATH = os.getenv("POS_CONFIG_JSON", os.path.join("static", "pos_config.json"))

DEFAULT_RECEIPT_COLS = int(os.getenv("RECEIPT_COLS", "48"))
DEFAULT_CHECKER_COLS = int(os.getenv("CHECKER_COLS", str(DEFAULT_RECEIPT_COLS)))
DEFAULT_FEED_LINES = int(os.getenv("RECEIPT_FEED_LINES", "6"))
DEFAULT_RIGHT_GUARD = int(os.getenv("RECEIPT_RIGHT_GUARD", "0"))

DEFAULT_CONFIG = {
    "billing": {
        "tax_percent": 10,
        "service_percent": 5,
        "tax_on_service": False,
        "takeaway_fee_idr": 10000,
        "rounding_step_idr": 100,
        "payment_methods": ["cash", "debit", "mastercard", "visa"],
    },
    "receipt": {
        "header_lines": [
            "DEMO RESTAURANT",
            "123 Demo Street",
            "City, 12345",
        ],
        "footer_note": "Thank you for dining with us!",
    },
    "printing": {
        "paper_width_mm": 80,
        "cups_media": "Custom.80x5000mm",
        "cups_qr_media": "Custom.80x80mm",
        "lp_options": {
            "media": "Custom.80x5000mm",
            "fit-to-page": "true",
            "page-left": "0",
            "page-right": "0",
            "page-top": "0",
            "page-bottom": "0",
        },
    },
    "escpos": {
        "receipt_cols": DEFAULT_RECEIPT_COLS,
        "checker_cols": DEFAULT_CHECKER_COLS,
        "feed_lines": DEFAULT_FEED_LINES,
        "right_guard": DEFAULT_RIGHT_GUARD,
    },
    "ui": {
        "click_debounce_ms": 100,
        "instant_table_open": False,
        "route_prefetch": True,
    },
}

_CONFIG_CACHE = None
_CONFIG_MTIME = None
_LOCK = threading.Lock()


def _to_int(val, default):
    try:
        if isinstance(val, bool):
            return default
        return int(float(val))
    except Exception:
        return default


def _to_float(val, default):
    try:
        if isinstance(val, bool):
            return default
        return float(val)
    except Exception:
        return default


def _to_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off"):
            return False
    return default


def _clamp(val, low, high):
    return max(low, min(high, val))


def _clean_lines(val, fallback):
    if val is None:
        return list(fallback)
    lines = None
    if isinstance(val, str):
        lines = val.splitlines()
    elif isinstance(val, (list, tuple)):
        lines = list(val)
    if lines is None:
        return list(fallback)
    cleaned = [str(x).strip() for x in lines if str(x).strip()]
    return cleaned or list(fallback)


def _normalize_config(raw):
    base = deepcopy(DEFAULT_CONFIG)
    data = raw if isinstance(raw, dict) else {}

    billing = data.get("billing")
    if isinstance(billing, dict):
        tax_pct = _to_int(billing.get("tax_percent"), base["billing"]["tax_percent"])
        service_pct = _to_int(billing.get("service_percent"), base["billing"]["service_percent"])
        base["billing"]["tax_percent"] = _clamp(tax_pct, 0, 100)
        base["billing"]["service_percent"] = _clamp(service_pct, 0, 100)
        base["billing"]["tax_on_service"] = _to_bool(
            billing.get("tax_on_service"), base["billing"]["tax_on_service"]
        )
        base["billing"]["takeaway_fee_idr"] = max(
            0, _to_int(billing.get("takeaway_fee_idr"), base["billing"]["takeaway_fee_idr"])
        )
        base["billing"]["rounding_step_idr"] = max(
            0, _to_int(billing.get("rounding_step_idr"), base["billing"]["rounding_step_idr"])
        )
        methods_raw = billing.get("payment_methods")
        if methods_raw is not None:
            methods_list = None
            if isinstance(methods_raw, str):
                methods_list = [p.strip() for p in methods_raw.replace(",", " ").split() if p.strip()]
            elif isinstance(methods_raw, (list, tuple)):
                methods_list = [str(m).strip() for m in methods_raw if str(m).strip()]
            if methods_list is not None:
                allowed = {
                    "cash",
                    "debit",
                    "mastercard",
                    "visa",
                    "qris",
                    "card",
                    "credit",
                    "transfer",
                }
                cleaned = []
                seen = set()
                for m in methods_list:
                    key = str(m).strip().lower()
                    if key in allowed and key not in seen:
                        cleaned.append(key)
                        seen.add(key)
                if cleaned:
                    base["billing"]["payment_methods"] = cleaned

    receipt = data.get("receipt")
    if isinstance(receipt, dict):
        base["receipt"]["header_lines"] = _clean_lines(
            receipt.get("header_lines"), base["receipt"]["header_lines"]
        )
        footer = receipt.get("footer_note")
        if footer is not None:
            base["receipt"]["footer_note"] = str(footer).strip() or base["receipt"]["footer_note"]

    printing = data.get("printing")
    if isinstance(printing, dict):
        base["printing"]["paper_width_mm"] = max(
            20, _to_int(printing.get("paper_width_mm"), base["printing"]["paper_width_mm"])
        )
        media = printing.get("cups_media")
        if media is not None:
            base["printing"]["cups_media"] = str(media).strip() or base["printing"]["cups_media"]
        qr_media = printing.get("cups_qr_media")
        if qr_media is not None:
            base["printing"]["cups_qr_media"] = str(qr_media).strip() or base["printing"]["cups_qr_media"]
        lp_opts = printing.get("lp_options")
        if isinstance(lp_opts, dict):
            for k, v in lp_opts.items():
                if k is None:
                    continue
                if v is None:
                    continue
                base["printing"]["lp_options"][str(k)] = str(v)

    escpos = data.get("escpos")
    if isinstance(escpos, dict):
        base["escpos"]["receipt_cols"] = max(
            16, _to_int(escpos.get("receipt_cols"), base["escpos"]["receipt_cols"])
        )
        base["escpos"]["checker_cols"] = max(
            16, _to_int(escpos.get("checker_cols"), base["escpos"]["checker_cols"])
        )
        base["escpos"]["feed_lines"] = max(
            0, _to_int(escpos.get("feed_lines"), base["escpos"]["feed_lines"])
        )
        base["escpos"]["right_guard"] = max(
            0, _to_int(escpos.get("right_guard"), base["escpos"]["right_guard"])
        )

    ui = data.get("ui")
    if isinstance(ui, dict):
        debounce_ms = _to_int(ui.get("click_debounce_ms"), base["ui"]["click_debounce_ms"])
        base["ui"]["click_debounce_ms"] = _clamp(debounce_ms, 0, 1000)
        base["ui"]["instant_table_open"] = _to_bool(
            ui.get("instant_table_open"), base["ui"]["instant_table_open"]
        )
        base["ui"]["route_prefetch"] = _to_bool(
            ui.get("route_prefetch"), base["ui"]["route_prefetch"]
        )

    return base


def _read_raw_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def load_config():
    global _CONFIG_CACHE, _CONFIG_MTIME
    with _LOCK:
        try:
            mtime = os.path.getmtime(CONFIG_PATH)
        except Exception:
            mtime = None
        if _CONFIG_CACHE is not None and _CONFIG_MTIME == mtime:
            return _CONFIG_CACHE
        raw = _read_raw_config()
        cfg = _normalize_config(raw)
        _CONFIG_CACHE = cfg
        _CONFIG_MTIME = mtime
        return cfg


def _deep_merge(base, patch):
    out = deepcopy(base)
    if not isinstance(patch, dict):
        return out
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def write_config(data):
    global _CONFIG_CACHE, _CONFIG_MTIME
    cfg = _normalize_config(data)
    os.makedirs(os.path.dirname(CONFIG_PATH) or ".", exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, CONFIG_PATH)
    try:
        mtime = os.path.getmtime(CONFIG_PATH)
    except Exception:
        mtime = None
    with _LOCK:
        _CONFIG_CACHE = cfg
        _CONFIG_MTIME = mtime
    return cfg


def update_config(patch):
    merged = _deep_merge(load_config(), patch or {})
    return write_config(merged)


def get_app_config():
    return load_config()


def get_billing_config():
    return load_config().get("billing", {})


def get_receipt_config():
    return load_config().get("receipt", {})


def get_printing_config():
    return load_config().get("printing", {})


def get_escpos_config():
    return load_config().get("escpos", {})
