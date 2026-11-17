# open-pos — Developer & Operator Documentation

## Table of contents

1. [Architecture overview](#architecture-overview)
2. [Database schema](#database-schema)
3. [Configuration reference](#configuration-reference)
4. [Menu format](#menu-format)
5. [Table & floor layout](#table--floor-layout)
6. [Printer setup](#printer-setup)
7. [User roles](#user-roles)
8. [Real-time events (Socket.IO)](#real-time-events-socketio)
9. [QR ordering integration](#qr-ordering-integration)
10. [Demo mode](#demo-mode)
11. [Running tests](#running-tests)
12. [Deployment](#deployment)

---

## Architecture overview

```
Browser (JS + CSS)
       │  HTTP + WebSocket
       ▼
Flask app (app/)
  ├── Blueprints (app/views/)   ← one per feature domain
  ├── Socket.IO bus (socketbus) ← real-time events
  └── Context processors        ← injects pos_config, is_admin, demo_users
       │
       ├── utils/data/          ← raw SQL queries (psycopg 3)
       ├── utils/services/      ← business logic (billing, ESC/POS, reservations)
       └── utils/config_store.py ← reads pos_config.json (hot-reloaded)
       │
       └── PostgreSQL (public schema)
```

The app is **stateless** beyond the database — all session state lives in PostgreSQL.  
Socket.IO rooms are named `outlet:{code}`, `outlet:{code}:floor:{n}`, `table:{n}`, `session:{id}`.

---

## Database schema

Run `schema.sql` once to create all tables. Key tables:

### `sessions`

A session represents one dine-in visit or takeaway order.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | UUID assigned at creation |
| `table_number` | TEXT | Matches an entry in `tables.json` |
| `status` | TEXT | `active`, `closed`, `cancelled`, `moved` |
| `service_type` | ENUM | `dine_in`, `takeaway`, `delivery` |
| `pax` | INTEGER | Guest count |
| `guest_name` | TEXT | Optional |
| `billing_started_at` | TIMESTAMPTZ | Set when cashier opens the bill |
| `split_meta` | JSONB | Bill-split configuration |
| `lock_user_id` | INTEGER | Optimistic lock owner |

### `order_items`

Each line item added to a session.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER IDENTITY PK | |
| `session_id` | TEXT FK → sessions | |
| `item_name` | TEXT | Free-text name from menu |
| `qty` | NUMERIC(10,1) | Supports 0.5 increments |
| `price` | INTEGER | Per-unit price in local currency |
| `total_price` | INTEGER | `qty × price` |
| `status` | TEXT | `new`, `edited`, `printed`, `served`, `paid`, `cancelled` |
| `void_qty` | NUMERIC(10,1) | Quantity voided |
| `bill_group` | TEXT | `NULL` = main bill, otherwise a split label |
| `sauce` | TEXT | Optional sauce note |
| `note` | TEXT | Optional kitchen note |

### `payments`

One row per payment event (including split payments and refunds).

| Column | Type | Notes |
|---|---|---|
| `session_id` | TEXT FK → sessions | |
| `amount` | INTEGER | Amount paid |
| `method` | TEXT | `cash`, `debit`, etc. |
| `discount_percent` | INTEGER | |
| `is_refund` | BOOLEAN | TRUE for refund rows |
| `is_dp` | BOOLEAN | TRUE for deposit payments |

### `reservations`

| Column | Type | Notes |
|---|---|---|
| `guest_name` | TEXT | |
| `pax` | INTEGER | |
| `date` | DATE | |
| `time` | TIME | |
| `status` | TEXT | `pending`, `confirmed`, `seated`, `cancelled` |
| `dp_amount` | INTEGER | Deposit collected |
| `session_id` | TEXT | Set when the guest is seated |

### `floor_layouts`

Stores drag-and-drop table positions for each floor.

| Column | Type | Notes |
|---|---|---|
| `floor` | TEXT PK | e.g. `"1"`, `"2"`, `"1B"` |
| `boxes` | JSONB | `{ "01": { "c": 5, "r": 3, "w": 4, "h": 3, "shape": "circle" } }` |

### `users`

| Column | Type | Notes |
|---|---|---|
| `username` | TEXT UNIQUE | |
| `password_hash` | TEXT | bcrypt |
| `role` | TEXT | `admin`, `cashier`, `waiter`, `viewer` |
| `demo_password_plain` | TEXT | Only set in demo mode (displayed on login page) |

### `qr.qr_orders`

Pending orders from an external QR ordering service.

| Column | Type | Notes |
|---|---|---|
| `table_number` | TEXT | |
| `items` | JSONB | Order payload |
| `status` | TEXT | `new`, `pending`, `sent` |
| `sent_at` | TIMESTAMPTZ | Set when absorbed into a POS session |

---

## Configuration reference

### Environment variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | — | Flask session secret |
| `DEMO_MODE` | | `1` | Show demo login panel |
| `DEMO_RESET_SECRET` | | — | Token for `POST /demo/reset` (for cron reset) |
| `PRINT_BACKEND` | | `mock` | `raw` (TCP ESC/POS) or `mock` (log to file) |
| `PRINT_MOCK_DIR` | | — | Directory to write mock receipts |
| `DEFAULT_KITCHEN_PRINTER` | | `kitchen` | Fallback printer ID |
| `PRINTER_KEY_MAP` | | (see config.py) | JSON map: alias → printer ID |
| `QR_SHARED_SECRET` | | — | HMAC secret for QR order webhook |
| `QR_USER_ID` | | `0` | User ID of the QR service account |
| `QR_ORDER_BASE` | | `http://127.0.0.1:5001` | Base URL of the QR ordering app |
| `DUE_SOON_MINUTES` | | `120` | Minutes before reservation to show "due soon" alert |

### `static/pos_config.json`

Hot-reloaded at runtime (no restart needed).

```json
{
  "billing": {
    "tax_percent": 10,
    "service_percent": 5,
    "tax_on_service": false,
    "takeaway_fee_idr": 5000,
    "rounding_step_idr": 100,
    "payment_methods": ["cash", "debit", "mastercard", "visa"]
  },
  "receipt": {
    "header_lines": ["YOUR RESTAURANT NAME", "Street", "City"],
    "footer_note": "Thank you!"
  },
  "printing": {
    "paper_width_mm": 80,
    "cups_media": "Custom.80x5000mm"
  },
  "escpos": {
    "receipt_cols": 48,
    "feed_lines": 6
  },
  "ui": {
    "click_debounce_ms": 40,
    "instant_table_open": false,
    "route_prefetch": true
  }
}
```

**Billing notes:**
- `tax_on_service: false` — tax is applied on subtotal only, not on the service charge
- `rounding_step_idr` — total is rounded up to the nearest multiple of this value
- `payment_methods` — drives the payment method selector on the billing screen

---

## Menu format

`static/menu.json` is the active runtime menu. `static/defaults/menu.json` is the seed default.

### Simple fixed-price item group

```json
{
  "Mains": {
    "Grilled Chicken": {
      "price": 45000,
      "dishes": [
        {"name": "Grilled Chicken - Original", "available": true},
        {"name": "Grilled Chicken - BBQ",      "available": true}
      ]
    }
  }
}
```

When a waiter picks "Grilled Chicken - Original", the item is added at `price = 45000`.

### Weight-based item group

```json
{
  "Seafood": {
    "Grilled Fish": {
      "price_per_kg": 120000,
      "portion_info": "300–500 g",
      "unit": "gram",
      "dishes": [
        {"name": "Grilled Fish - Herb Butter", "available": true}
      ]
    }
  }
}
```

The waiter enters weight (e.g. 350 g); the system computes `price = ceil(350/1000 × 120000)`.

### Price override on a dish

```json
{"name": "Fried Rice", "available": true, "price_override": 18000}
```

Overrides the parent group's base price for that specific dish.

### Availability toggle

Set `"available": false` to hide a dish from the ordering screen without deleting it.  
The **Menu admin** page (`/menu_admin`) provides a UI to toggle availability live.

---

## Table & floor layout

### `static/tables.json`

```json
[
  {"number": "01", "max_pax": 4, "floor": 1},
  {"number": "02", "max_pax": 6, "floor": 1},
  {"number": "101", "max_pax": 8, "floor": 2}
]
```

- `number` — unique identifier used throughout the system; can be alphanumeric
- `floor` — must match a key in `floor_layouts` if you use the visual floor plan
- `max_pax` — shown on the table card; not enforced as a hard limit

### Visual floor plan

Admin users can drag tables into position at `/admin/layout`. Positions are stored in `floor_layouts` (DB). The floor plan is broadcast in real-time so all tabs update instantly.

---

## Printer setup

### `static/printers.json`

```json
{
  "printers": [
    {"id": "kitchen", "ip": "10.0.0.10", "port": 9100, "tags": ["dapur", "all", "fallback"]},
    {"id": "bar",     "ip": "10.0.0.11", "port": 9100, "tags": ["bar"]},
    {"id": "grill",   "ip": "10.0.0.12", "port": 9100, "tags": ["grill"]}
  ],
  "fallback_printer_id": "kitchen",
  "table_floor_rules": {
    "by_range": [
      {"floor": "1", "min": 1,   "max": 99},
      {"floor": "2", "min": 100, "max": 199}
    ]
  }
}
```

### Routing logic

Order items are routed to printers by matching **item category tags** to **printer tags**:

1. The system reads the item's top-level category from `menu.json` (e.g. `"Seafood"`)
2. It maps that category to a station tag via `CATEGORY_STATION_MAP` env var (JSON)  
   e.g. `CATEGORY_STATION_MAP={"Seafood": "grill", "Drinks": "bar"}`
3. It finds the printer whose `tags` array contains that station tag
4. If no match, the `fallback_printer_id` printer is used
5. For bar orders, the printer is also selected by floor (using `table_floor_rules`)

### Printer backends

| `PRINT_BACKEND` | Behaviour |
|---|---|
| `raw` | Sends ESC/POS bytes directly over TCP to `ip:port` |
| `mock` | Writes formatted receipt text to `PRINT_MOCK_DIR` (or logs it) |

### Testing printers

```bash
# Scan your subnet for thermal printers (port 9100)
python scripts/printer_scan.py 10.0.0.0/24

# Send a test page to a specific printer
python scripts/printer_test.py --ip 10.0.0.10
```

---

## User roles

| Role | Permissions |
|---|---|
| `admin` | Full access including admin tools, analytics, layout editor, menu editor, user management |
| `cashier` | Table management, orders, billing, takeaway, transactions view |
| `waiter` | Table viewing, add orders, view kitchen chits |
| `viewer` | Read-only dashboard |

Role checks are enforced in `app/authz.py` via Flask `before_request` hooks.

### Creating users

```bash
python scripts/create_user.py
# Follow the prompts to set username, password, and role
```

---

## Real-time events (Socket.IO)

The frontend connects to the `/pos` Socket.IO namespace.

### Client → server

| Event | Payload | Effect |
|---|---|---|
| `hello` | `{outlet, floor}` | Joins `outlet:{code}` and `outlet:{code}:floor:{n}` rooms |
| `watch.table` | `{table_number}` | Joins `table:{n}` room for table-specific updates |
| `watch.session` | `{session_id}` | Joins `session:{id}` room |

### Server → client

| Event | When fired |
|---|---|
| `table.state.changed` | Any change to table occupancy, billing, or order count |
| `session_created` | New session opened |
| `session_closed` | Session closed / paid |
| `session_items_changed` | Items added, edited, or voided |
| `session_billing` | Billing started on a session |
| `table_moved` | Table merge or move operation |

All payloads include `ts` (ISO timestamp) and `event_id` (UUID).

---

## QR ordering integration

The POS can receive orders from an external QR-ordering web app via:

- **`POST /api/qr/order`** — webhook that inserts a row into `qr.qr_orders`
- **Floor plan badge** — tables with pending QR orders show an orange indicator
- **Absorb button** — waiter or cashier clicks to merge QR items into the active session

Authentication uses HMAC-SHA256:
```
X-Hub-Signature: sha256=<hex(HMAC(QR_SHARED_SECRET, body))>
```

Set `QR_USER_ID` to the `users.id` of a dedicated service account so the system can identify QR-created items.

---

## Demo mode

When `DEMO_MODE=1`:

1. The login page shows a clickable credential panel (reads `DEMO_USERS` from `app/config.py`)
2. `docker-entrypoint.sh` runs `scripts/demo_seed.py --if-empty` on startup to populate the DB
3. A `POST /demo/reset` endpoint (token-protected by `DEMO_RESET_SECRET`) wipes and re-seeds all data — suitable for a nightly cron job on a public demo instance

To re-seed manually:

```bash
python scripts/demo_seed.py
```

---

## Running tests

```bash
pip install pytest
pytest
```

Tests are in `tests/` and cover:
- Session status flow transitions
- Table reservation logic
- Auto-seat from reservation
- Reservations lookup filtering
- Floor-based Socket.IO routing

---

## Deployment

### Docker (recommended)

```bash
docker build -t open-pos .
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  -e DEMO_MODE=1 \
  open-pos
```

The container runs gunicorn with eventlet worker (required for Socket.IO).

### Railway (one-click)

See README for Railway deployment steps. The `railway.json` and `Dockerfile` are pre-configured.

### Bare metal / Raspberry Pi

For on-premise deployment with real thermal printers:

```bash
pip install -r requirements.txt   # or requirements_pi.txt on Raspberry Pi
export DATABASE_URL=...
export PRINT_BACKEND=raw
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8080 wsgi:app
```

> **Single worker required** — Socket.IO with eventlet requires exactly 1 gunicorn worker.
