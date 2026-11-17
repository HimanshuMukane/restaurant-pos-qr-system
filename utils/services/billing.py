from collections import defaultdict
from decimal import Decimal
from ..data.core import connect_db, UNPAID_STATUSES
from ..data.payments import get_dp_amount, get_dp_used
from ..config_store import get_billing_config

def compute_prebill(session_id:str, group_label:str | None) -> dict:
    with connect_db() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT id, table_number, pax, guest_name, created_at
                FROM sessions
                WHERE id = %s
            """, (session_id,))
            row = c.fetchone()
            if not row:
                raise ValueError("Session not found")

            sess = {
                "id": row[0],
                "table_number": row[1],
                "pax": row[2],
                "guest_name": row[3],
                "created_at": row[4],
            }

            g = (group_label or "").strip().lower()
            want_main = (g in ("", "main"))

            sql = """
                SELECT id, item_name, qty, price, total_price, sauce, note, status, "timestamp", bill_group
                FROM order_items
                WHERE session_id = %s
                    AND status = ANY(%s)
            """
            params = [session_id, list(UNPAID_STATUSES)]
            if want_main:
                sql += "AND bill_group IS NULL"
            else:
                sql += "AND bill_group = %s"
                params.append(group_label)

            sql += ' ORDER BY "timestamp", id'
            c.execute(sql, params)
            items = c.fetchall()

            bucket = defaultdict(lambda: {"qty": 0, "unit_price": 0, "line_total": 0, "name": "", "sauce": None, "note": None})
            for r in items:
                _id, name, qty, unit_price, _tp, sauce, note, _st, _ts, _grp = r
                qdec = Decimal(str(qty or 0)).quantize(Decimal('0.1'))
                key = (name, unit_price, sauce or None, note or None)
                b = bucket[key]
                b["name"] = name
                b["unit_price"] = int(unit_price or 0)
                b["qty"] = Decimal(str(b["qty"])) + qdec
                b["sauce"] = sauce or None
                b["note"] = note or None
                b["line_total"] += int(_tp or (int(unit_price or 0) * float(qdec)))

            lines = list(bucket.values())
            lines.sort(key=lambda x: (x["name"].lower(), x["unit_price"]))
            for x in lines:
                x["qty"] = float(Decimal(str(x["qty"])).quantize(Decimal('0.1')))

            subtotal = sum(int(x["line_total"]) for x in lines)
            discount_percent = 0
            discount_amount = round(subtotal * (discount_percent / 100))
            after_discount = subtotal - discount_amount
            billing_cfg = get_billing_config()
            service_pct = int(billing_cfg.get("service_percent", 5))
            tax_pct = int(billing_cfg.get("tax_percent", 10))
            tax_on_service = bool(billing_cfg.get("tax_on_service"))
            service = round(after_discount * (service_pct / 100.0))
            tax_base = after_discount + service if tax_on_service else after_discount
            tax = round(tax_base * (tax_pct / 100.0))
            total = after_discount + service + tax

            dp_total = get_dp_amount(None, session_id) or 0
            dp_used = get_dp_used(None, session_id) or 0
            dp_remaining = max(dp_total - dp_used, 0)

    bill_label = ("MAIN" if want_main else str(group_label))
    return {
        "header": {
            "session_id": sess["id"],
            "table_number": sess["table_number"],
            "pax": sess["pax"],
            "guest_name": sess["guest_name"],
            "opened_at": sess["created_at"],
            "bill_label": bill_label
        },
        "lines": lines,
        "summary": {
            "subtotal": subtotal,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "service": service,
            "tax": tax,
            "total": total
        },
        "dp_available": dp_remaining
    }

def combine_items(orders):
    combined = {}
    for order in orders:
        for item in order["items"]:
            key = (item["name"], item["price"])
            if key in combined:
                combined[key]["qty"] += item["qty"]
            else:
                combined[key] = {
                    "name": item["name"],
                    "price": item["price"],
                    "qty": item["qty"],
                }
    return list(combined.values())
