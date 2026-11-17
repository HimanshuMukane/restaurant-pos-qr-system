import json
from .core import connect_db

def normalize_group(value):
    if value is None:
        return None
    g = str(value).strip()
    if g == "" or g.lower() == "main":
        return None
    if g.isdigit() and int(g) > 0:
        return str(int(g))  # '01' -> '1'
    return None


def normalize_split_meta(raw):
    meta = []
    if not isinstance(raw, list):
        return meta
    for entry in raw:
        if isinstance(entry, dict):
            key = (
                entry.get("key")
                or entry.get("label")
                or entry.get("id")
                or entry.get("group")
            )
            name = entry.get("name") or entry.get("title") or ""
        else:
            key = entry
            name = ""
        key = str(key or "").strip()
        if not key.isdigit():
            continue
        meta.append({"key": str(int(key)), "name": str(name or "").strip()})
    meta.sort(key=lambda m: int(m["key"]))
    return meta


def split_meta_labels(raw):
    return [m["key"] for m in normalize_split_meta(raw)]


def split_meta_map(raw):
    return {m["key"]: m.get("name") or "" for m in normalize_split_meta(raw)}


def get_split_labels(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("SELECT split_labels FROM sessions WHERE id=%s", (session_id,))
        row = c.fetchone()
        if not row or row[0] is None:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

def set_split_labels(_ignored, session_id, labels):
    import json as _json
    with connect_db() as conn, conn.cursor() as c:
        c.execute("UPDATE sessions SET split_labels=%s WHERE id=%s", (_json.dumps(labels), session_id,))

def clear_split_labels(_ignored, session_id):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("UPDATE order_items SET bill_group=NULL WHERE session_id=%s", (session_id,))
        c.execute("UPDATE sessions SET split_labels=NULL WHERE id=%s", (session_id,))

def set_item_bill_group(_ignored, item_id, bill_group, by_user_id=None):
    with connect_db() as conn, conn.cursor() as c:
        c.execute("""
            UPDATE order_items
            SET bill_group = %s, updated_by_user_id = %s
            WHERE id = %s
        """, (bill_group, by_user_id, item_id))

def set_items_bill_group(_ignored, item_ids, bill_group, by_user_id=None):
    if not item_ids:
        return
    placeholders = ",".join(["%s"] * len(item_ids))
    params = [bill_group, by_user_id] + list(item_ids)
    with connect_db() as conn, conn.cursor() as c:
        c.execute(f"""
            UPDATE order_items
            SET bill_group = %s, updated_by_user_id = %s
            WHERE id IN ({placeholders})
        """, params)
