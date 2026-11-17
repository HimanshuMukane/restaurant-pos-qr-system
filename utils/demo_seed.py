"""
Demo seed — wipes transactional tables and inserts a realistic restaurant snapshot.
Called by scripts/demo_seed.py (CLI) and app/views/demo.py (HTTP reset endpoint).
"""
import bcrypt
import os
import shutil
from datetime import datetime, timedelta
from .data.core import connect_db

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_STATIC_DIR   = os.path.join(os.path.dirname(__file__), "..", "static")
_DEFAULTS_DIR = os.path.join(_STATIC_DIR, "defaults")

# ---------------------------------------------------------------------------
# Demo users  (match app/config.py DEMO_USERS)
# ---------------------------------------------------------------------------
DEMO_USERS = [
    {"username": "admin",   "password": "admin123",   "full_name": "Admin",   "role": "admin"},
    {"username": "cashier", "password": "cashier123", "full_name": "Cashier", "role": "cashier"},
    {"username": "waiter",  "password": "waiter123",  "full_name": "Waiter",  "role": "waiter"},
]

# ---------------------------------------------------------------------------
# Demo sessions
# ---------------------------------------------------------------------------
DEMO_SESSIONS = [
    {
        "id": "demo-s01-tbl05",
        "table": "05",
        "pax": 4,
        "guest": None,
        "mins_ago": 90,
        "items": [
            # already sent to kitchen
            {"name": "Grilled Fish - Herb Butter", "qty": 2, "price": 120_000, "status": "printed"},
            {"name": "Grilled Fish - Spicy",       "qty": 1, "price": 120_000, "status": "printed"},
            {"name": "Stir-Fried Greens",          "qty": 1, "price":  22_000, "status": "printed"},
            {"name": "Steamed Rice",               "qty": 4, "price":   8_000, "status": "printed"},
            {"name": "Cola",                       "qty": 4, "price":  15_000, "status": "printed"},
            # just added — pending kitchen send
            {"name": "Prawn - Butter Garlic",      "qty": 1, "price": 150_000, "status": "new"},
            {"name": "Still Water",                "qty": 2, "price":   8_000, "status": "new"},
        ],
    },
    {
        "id": "demo-s02-tbl09",
        "table": "09",
        "pax": 8,
        "guest": "Johnson Family",
        "mins_ago": 150,
        "items": [
            {"name": "Beef Steak - Black Pepper Sauce", "qty": 2, "price": 85_000, "status": "printed"},
            {"name": "Beef Steak - Medium",             "qty": 1, "price": 85_000, "status": "printed"},
            {"name": "Grilled Chicken - BBQ",           "qty": 2, "price": 45_000, "status": "printed"},
            {"name": "Spaghetti Bolognese",             "qty": 2, "price": 38_000, "status": "printed"},
            {"name": "Sautéed Mushroom",                "qty": 1, "price": 22_000, "status": "printed"},
            {"name": "Mixed Salad",                     "qty": 1, "price": 25_000, "status": "printed"},
            {"name": "Steamed Rice",                    "qty": 8, "price":  8_000, "status": "printed"},
            {"name": "Cola",                            "qty": 6, "price": 15_000, "status": "printed"},
            {"name": "Still Water",                     "qty": 2, "price":  8_000, "status": "printed"},
            {"name": "Chocolate Lava Cake",             "qty": 2, "price": 28_000, "status": "printed"},
        ],
    },
    {
        "id": "demo-s03-tbl03",
        "table": "03",
        "pax": 2,
        "guest": None,
        "mins_ago": 8,
        "items": [
            {"name": "Squid - Grilled",   "qty": 1, "price": 90_000, "status": "new"},
            {"name": "Steamed Rice",      "qty": 2, "price":  8_000, "status": "new"},
            {"name": "Lemon Soda",        "qty": 2, "price": 15_000, "status": "new"},
        ],
    },
]

# ---------------------------------------------------------------------------
# Demo reservations
# ---------------------------------------------------------------------------
DEMO_RESERVATIONS = [
    {
        "guest_name": "Williams Party",
        "phone": "555-0101",
        "pax": 6,
        "days_ahead": 1,
        "time": "19:00",
        "notes": "Window seat preferred",
        "status": "confirmed",
        "dp_amount": 200_000,
        "dp_method": "card",
    },
    {
        "guest_name": "Smith Family",
        "phone": "555-0202",
        "pax": 10,
        "days_ahead": 2,
        "time": "18:30",
        "notes": "Birthday celebration",
        "status": "pending",
        "dp_amount": 0,
        "dp_method": None,
    },
    {
        "guest_name": "Mr. Brown",
        "phone": "555-0303",
        "pax": 4,
        "days_ahead": 3,
        "time": "12:00",
        "notes": None,
        "status": "pending",
        "dp_amount": 0,
        "dp_method": None,
    },
]


def run_seed(if_empty: bool = False):
    """
    Seed the database with demo data.
    if if_empty=True, skip if sessions table already has rows.
    """
    with connect_db() as conn, conn.cursor() as c:
        if if_empty:
            c.execute("SELECT 1 FROM sessions LIMIT 1")
            if c.fetchone():
                return  # already seeded

        # 1) Wipe transactional tables
        c.execute("DELETE FROM payments")
        c.execute("DELETE FROM reservation_items")
        c.execute("DELETE FROM reservations")
        c.execute("DELETE FROM order_items")
        c.execute("DELETE FROM sessions")

        # 2) Upsert demo users
        for u in DEMO_USERS:
            pw_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
            c.execute("""
                INSERT INTO users (username, full_name, password_hash, demo_password_plain, role, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (username) DO UPDATE
                  SET password_hash        = EXCLUDED.password_hash,
                      demo_password_plain  = EXCLUDED.demo_password_plain,
                      full_name            = EXCLUDED.full_name,
                      role                 = EXCLUDED.role,
                      is_active            = TRUE
            """, (u["username"], u["full_name"], pw_hash, u["password"], u["role"]))

        c.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
        row = c.fetchone()
        admin_id = row[0] if row else None

        # 3) Sessions + order items
        now = datetime.now()
        for sess in DEMO_SESSIONS:
            created_at = now - timedelta(minutes=sess["mins_ago"])
            c.execute("""
                INSERT INTO sessions
                  (id, pax, table_number, created_at, guest_name, dp_amount, status, opened_by_user_id)
                VALUES (%s, %s, %s, %s, %s, 0, 'active', %s)
            """, (sess["id"], sess["pax"], sess["table"], created_at, sess["guest"], admin_id))

            for i, item in enumerate(sess["items"]):
                item_ts = created_at + timedelta(minutes=i * 3)
                c.execute("""
                    INSERT INTO order_items
                      (session_id, table_number, item_name, qty, price, total_price,
                       status, "timestamp", created_by_user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    sess["id"], sess["table"],
                    item["name"], item["qty"], item["price"],
                    int(item["qty"] * item["price"]),
                    item["status"], item_ts, admin_id,
                ))

        # 4) Reservations
        for res in DEMO_RESERVATIONS:
            res_date = (now + timedelta(days=res["days_ahead"])).date()
            c.execute("""
                INSERT INTO reservations
                  (guest_name, phone, pax, date, time, notes, status,
                   dp_amount, dp_method, created_at, created_by_user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (
                res["guest_name"], res["phone"], res["pax"],
                res_date, res["time"], res["notes"], res["status"],
                res["dp_amount"], res.get("dp_method"), admin_id,
            ))

        conn.commit()


# ---------------------------------------------------------------------------
# Nightly reset — lightweight, keeps order history & payments
# ---------------------------------------------------------------------------

def _restore_default_file(filename: str):
    """Atomically copy static/defaults/<filename> → static/<filename>."""
    src = os.path.join(_DEFAULTS_DIR, filename)
    dst = os.path.join(_STATIC_DIR, filename)
    tmp = dst + ".tmp"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def run_nightly_reset():
    """
    Nightly demo reset — does NOT wipe order history or payments.

    - Restores menu.json and tables.json from baked-in defaults
    - Resets demo user passwords/roles; deletes any users added during demo
    - Auto-closes any active sessions older than 24 hours
    """
    # 1) Restore static files
    _restore_default_file("menu.json")
    _restore_default_file("tables.json")

    with connect_db() as conn, conn.cursor() as c:
        # 2) Close stale active sessions (opened more than 24 h ago)
        cutoff = datetime.now() - timedelta(hours=24)
        c.execute("""
            UPDATE sessions
               SET status     = 'cancelled',
                   closed_at  = NOW()
             WHERE status     = 'active'
               AND created_at < %s
        """, (cutoff,))

        # 3) Delete any users not in the demo list
        demo_usernames = [u["username"] for u in DEMO_USERS]
        c.execute(
            "DELETE FROM users WHERE username <> ALL(%s)",
            (demo_usernames,)
        )

        # 4) Upsert demo users back to default credentials
        for u in DEMO_USERS:
            pw_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
            c.execute("""
                INSERT INTO users (username, full_name, password_hash, demo_password_plain, role, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (username) DO UPDATE
                  SET password_hash       = EXCLUDED.password_hash,
                      demo_password_plain = EXCLUDED.demo_password_plain,
                      full_name           = EXCLUDED.full_name,
                      role                = EXCLUDED.role,
                      is_active           = TRUE
            """, (u["username"], u["full_name"], pw_hash, u["password"], u["role"]))

        conn.commit()
