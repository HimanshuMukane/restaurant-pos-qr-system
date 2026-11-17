import os
import json

def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name, default) or "").strip().lower() in ("1", "true", "yes", "on")

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    QR_USER_ID = int(os.environ.get("QR_USER_ID") or 0)
    QR_SHARED_SECRET = (os.environ.get("QR_SHARED_SECRET") or "").strip()
    QR_ORDER_BASE = (os.environ.get("QR_ORDER_BASE", "http://127.0.0.1:5000").strip().rstrip("/"))
    QR_DEFAULT_LANG = (os.environ.get("QR_DEFAULT_LANG", "en") or "en").strip().lower()

    CATEGORY_STATION_MAP = os.environ.get("CATEGORY_STATION_MAP", "{}")

    DEFAULT_KITCHEN_PRINTER = os.environ.get("DEFAULT_KITCHEN_PRINTER", "kitchen")

    # Map logical station aliases -> printer IDs (from printers.json).
    # Override via PRINTER_KEY_MAP env var (JSON string) to match your setup.
    PRINTER_KEY_MAP = os.environ.get("PRINTER_KEY_MAP", json.dumps({
        "expediter": "kitchen",
        "kitchen":   "kitchen",
        "bar":       "bar",
        "grill":     "grill",
        "steam":     "steam",
    }))

    DUE_SOON_MINUTES = int(os.environ.get("DUE_SOON_MINUTES", "120"))
    DEMO_MODE = _env_flag("DEMO_MODE", "1")
    DEMO_USERS = [
        {
            "label": "Admins",
            "entries": [{"username": "admin", "password": "admin123", "role": "admin"}],
        },
        {
            "label": "Cashiers",
            "entries": [{"username": "cashier", "password": "cashier123", "role": "cashier"}],
        },
        {
            "label": "Waiters",
            "entries": [{"username": "waiter", "password": "waiter123", "role": "waiter"}],
        },
    ]


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False
