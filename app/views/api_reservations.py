from flask import Blueprint, jsonify
from flask_login import login_required
from psycopg.rows import dict_row
from utils.db import connect_db

bp = Blueprint("api_resv", __name__)

@bp.get("/api/reservations/hints")
@login_required
def api_reservation_hints():
    # next 6 hours; tweak as needed
    q = """
      SELECT table_number,
            (date::date + "time"::time) AS ts
      FROM public.reservations
      WHERE status IN ('pending','confirmed')
        AND table_number IS NOT NULL
        AND (date::date + "time"::time) >= (now() AT TIME ZONE 'Asia/Jakarta')
        AND (date::date + "time"::time) <= (now() AT TIME ZONE 'Asia/Jakarta') + INTERVAL '6 hours'
      ORDER BY date, "time"
    """
    out = []
    with connect_db() as conn, conn.cursor(row_factory=dict_row) as c:
        c.execute(q)
        for r in c.fetchall():
            ts = r["ts"]  # datetime from psycopg
            out.append({
                "table_number": r["table_number"],
                "ts_iso": ts.strftime("%Y-%m-%dT%H:%M")
            })
    return jsonify({"items": out})

