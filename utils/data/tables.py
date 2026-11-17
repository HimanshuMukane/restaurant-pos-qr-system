import json
from decimal import Decimal
from .core import connect_db

def _layout_has_gap_column(conn) -> bool:
    try:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'floor_layouts'
                  AND column_name = 'grid_gap_px'
                LIMIT 1
                """
            )
            return c.fetchone() is not None
    except Exception:
        return False

def load_tables(json_path="static/tables.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        tables = json.load(f)
    for t in tables:
        if "floor" in t and t["floor"] is not None:
            t["floor"] = str(t["floor"])
    return tables

def group_order_items(order_items):
    """
    order_items: list of tuples
      (id, name, qty, price, total_price, sauce, note, status, timestamp, bill_group)

    Returns list of dicts with:
      item_name, sauce, note, qty, price, total_price, bill_group, ids, all_paid,
      qty_printed, qty_unprinted, print_state
    """
    grouped = {}
    for item in order_items:
        item_id, name, qty, price, total_price, sauce, note, status, timestamp, bill_group = item

        key = (name, sauce, note, bill_group)
        if key not in grouped:
            grouped[key] = {
                "item_name": name,
                "sauce": sauce,
                "note": note,
                "qty": Decimal('0.0'),
                "price": price,
                "total_price": 0,
                "bill_group": bill_group,
                "ids": [],
                "all_paid": (status == "paid"),
                "qty_printed": Decimal('0.0'),
                "qty_unprinted": Decimal('0.0'),
            }

        g = grouped[key]
        qd = Decimal(str(qty or 0))
        g["qty"] += qd
        g["total_price"] += int(total_price or 0)
        g["ids"].append(item_id)
        g["all_paid"] = g["all_paid"] and (status == "paid")

        if status in ("printed", "served", "paid"):
            g["qty_printed"] += qd
        elif status in ("new", "edited"):
            g["qty_unprinted"] += qd
        # (cancelled rows are filtered before we get here)

    out = []
    for g in grouped.values():
        if g["qty_unprinted"] == 0 and g["qty_printed"] > 0:
            g["print_state"] = "printed_all"
        elif g["qty_unprinted"] > 0 and g["qty_printed"] > 0:
            g["print_state"] = "printed_partial"
        else:
            g["print_state"] = "unprinted"
        # cast totals/qty for templating convenience
        g["qty"] = float(g["qty"])
        g["qty_printed"] = float(g["qty_printed"])
        g["qty_unprinted"] = float(g["qty_unprinted"])
        out.append(g)

    return out

def get_floor_layouts():

    result = {}
    with connect_db() as conn, conn.cursor() as c:
        has_gap = _layout_has_gap_column(conn)
        if has_gap:
            c.execute("SELECT floor, grid_cols, grid_row_px, grid_gap_px, boxes FROM floor_layouts")
        else:
            c.execute("SELECT floor, grid_cols, grid_row_px, boxes FROM floor_layouts")
        for row in c.fetchall():
            try:
                if has_gap:
                    floor, cols, row_px, gap_px, boxes = row
                else:
                    floor, cols, row_px, boxes = row
                    gap_px = 6
                result[str(floor)] = {
                    "grid_cols": cols or 12,
                    "grid_row_px": row_px or 90,
                    "grid_gap_px": gap_px or 6,
                    "boxes": json.loads(boxes) if isinstance(boxes, str) else (boxes or {})
                }
            except Exception:
                result[str(floor)] = {"grid_cols": 12, "grid_row_px": 90, "grid_gap_px": 6, "boxes": {}}
    return result
    
