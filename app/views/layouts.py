from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..authz import roles_required
from utils import db
import json

bp = Blueprint("layouts", __name__)

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

@bp.put("/api/layouts/<floor>")
@login_required
@roles_required("admin")
def api_save_layout(floor):
    data = request.get_json(force=True) or {}
    try:
        grid_cols   = int(data.get("grid_cols", 12))
        grid_row_px = int(data.get("grid_row_px", 90))
        grid_gap_px = int(data.get("grid_gap_px", 6))
        boxes       = data.get("boxes") or {}

        conn = db.connect_db(None)
        c = conn.cursor()
        try:
            has_gap = _layout_has_gap_column(conn)
            if has_gap:
                c.execute("""
                    INSERT INTO floor_layouts (floor, grid_cols, grid_row_px, grid_gap_px, boxes, updated_by_user_id)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (floor) DO UPDATE SET
                        grid_cols = EXCLUDED.grid_cols,
                        grid_row_px = EXCLUDED.grid_row_px,
                        grid_gap_px = EXCLUDED.grid_gap_px,
                        boxes = EXCLUDED.boxes,
                        updated_by_user_id = EXCLUDED.updated_by_user_id,
                        updated_at = now()
                """, (str(floor), grid_cols, grid_row_px, grid_gap_px, json.dumps(boxes), current_user.id))
            else:
                c.execute("""
                    INSERT INTO floor_layouts (floor, grid_cols, grid_row_px, boxes, updated_by_user_id)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (floor) DO UPDATE SET
                        grid_cols = EXCLUDED.grid_cols,
                        grid_row_px = EXCLUDED.grid_row_px,
                        boxes = EXCLUDED.boxes,
                        updated_by_user_id = EXCLUDED.updated_by_user_id,
                        updated_at = now()
                """, (str(floor), grid_cols, grid_row_px, json.dumps(boxes), current_user.id))
            conn.commit()
        finally:
            conn.close()

        try:
            from ..socketbus import broadcast
            broadcast("layout_updated", {
                "floor": str(floor),
                "layout": {
                    "grid_cols": grid_cols,
                    "grid_row_px": grid_row_px,
                    "grid_gap_px": grid_gap_px,
                    "boxes": boxes
                }
            }, room="outlet:DEMO:floor:1")
        except Exception:
            pass

        return jsonify(status="ok")
    except Exception as e:
        return jsonify(status="error", message=str(e)), 400
