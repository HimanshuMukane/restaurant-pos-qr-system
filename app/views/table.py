from flask import Blueprint, jsonify, abort
from flask_login import login_required
from datetime import datetime          
from utils import db
from utils.data.splits import normalize_split_meta, split_meta_labels

bp = Blueprint("table", __name__)

def _norm_group(v):
    if v is None:
        return "main"
    s = str(v).strip()
    if s == "" or s.lower() in ("null", "none"):
        return "main"
    return s

@bp.get("/api/session_state/<session_id>")
@login_required
def api_session_state(session_id):
    sess_min = db.get_session_by_id(None, session_id)
    if not sess_min:
        abort(404)

    # ---------- RAW rows (no combine) ----------
    raw = db.get_all_order_items_by_session(None, session_id) or []
    rows = []
    group_subtotals = {}
    group_status = {}

    def _num(x):
        try: return float(x or 0)
        except: return 0.0

    for r in raw:
        status = (r[7] or "").lower()
        grp       = _norm_group(r[9])

        if status != "cancelled":
            s = group_status.setdefault(grp, {"paid": 0, "unpaid": 0})
            if status == "paid":
                s["paid"] += 1
            else:
                s["unpaid"] += 1
        else:
            continue
        gross_q   = _num(r[2])         # qty
        void_q    = _num(r[10])        # COALESCE(void_qty, 0) from your SELECT
        net_q     = max(0.0, gross_q - void_q)
        unit      = int(_num(r[3]))
        line_net  = int(net_q * unit)  # recompute from net

        group_subtotals[grp] = group_subtotals.get(grp, 0) + line_net

        rows.append({
            "id": int(r[0]) if r[0] is not None else None,
            "item_name": r[1],
            "name": r[1],
            "qty": net_q,                  # <<--- send NET for rendering
            "net_qty": net_q,              # explicit for robust clients
            "gross_qty": gross_q,
            "void_qty": void_q,
            "unit_price": unit,
            "price": unit,
            "subtotal": line_net,          # keep fields your UI reads
            "total_price": line_net,
            "note": r[6] or None,
            "bill_group": None if grp == "main" else grp,

            # status flags your renderer uses
            "status": status,
            "print_state": "printed" if status in ("printed", "printed_all") else (
                "printed_partial" if status in ("partial", "printed_partial") else ""
            ),
            "wasPrinted": status in ("printed", "printed_all"),
            "hasPending": status in ("partial", "printed_partial"),
            "ids": [int(r[0])] if r[0] is not None else [],
        })

    present_groups = sorted(
        [g for g in group_subtotals if g != "main"],
        key=lambda x: (len(x), x)
    )
    raw_labels = db.get_split_labels(None, session_id) or []
    split_meta = normalize_split_meta(raw_labels)
    config_labels = [m["key"] for m in split_meta]


    # group status (derived from the same rows)
    labels = config_labels
    for g, s in group_status.items():
        s["all_paid"] = (s["unpaid"] == 0 and s["paid"] > 0)
    for lbl in labels:
        group_status.setdefault(lbl, {"paid": 0, "unpaid": 0, "all_paid": False})
    group_status.setdefault("main", {"paid": 0, "unpaid": 0, "all_paid": False})

    # DP
    dp_total = db.get_dp_amount(None, session_id) or 0
    dp_used  = db.get_dp_used(None, session_id) or 0
    dp_remaining = max(int(dp_total) - int(dp_used), 0)

    return jsonify({
        "rows_shape": "raw_v1",          # <--- tell client it's raw
        "session_id": session_id,
        "rows": rows,
        "group_subtotals": group_subtotals,
        "split_labels": config_labels,
        "split_meta": split_meta,
        "present_groups": present_groups,
        "group_status": group_status,
        "dp_amount": int(dp_total),
        "dp_remaining": int(dp_remaining),
        "ts": datetime.utcnow().isoformat() + "Z",
    })


@bp.get("/session/<session_id>/state")
@login_required
def session_state(session_id):
    rows = []
    group_subtotals = {}

    raw = db.get_all_order_items_by_session(None, session_id) or []
    # Columns you’ve used before:
    # r[1]=name, r[2]=qty, r[3]=unit_price, r[4]=line_total, r[6]=note, r[7]=status, r[9]=bill_group

    for r in raw:
        status = (r[7] or "").lower()
        if status == "cancelled":
            continue
        grp = _norm_group(r[9])
        group_subtotals.setdefault(grp, 0)
        group_subtotals[grp] += int(r[4] or 0)

        # row shape that your renderer understands
        row = {
            "item_name": r[1],
            "name": r[1],
            "qty": float(r[2] or 0),
            "price": int(r[3] or 0),
            "subtotal": int(r[4] or 0),      # used by getSubtotal()
            "total_price": int(r[4] or 0),
            "note": r[6] or None,
            "bill_group": None if grp == "main" else grp,

            # simple print-state mapping; tweak if you have richer states
            "print_state": "printed" if status in ("printed", "printed_all") else (
                "printed_partial" if status in ("partial", "printed_partial") else ""
            ),
            "wasPrinted": status in ("printed", "printed_all"),
            "hasPending": status in ("partial", "printed_partial"),
            "ids": [],
        }
        try:
            # if your query includes the row id at r[0]
            if r[0] is not None:
                row["ids"] = [int(r[0])]
        except Exception:
            pass

        rows.append(row)

    # split labels = present non-main groups
    present_groups = sorted(
        [g for g in group_subtotals if g != "main"],
        key=lambda x: (len(x), x)
    )
    raw_labels = db.get_split_labels(None, session_id) or []
    split_meta = normalize_split_meta(raw_labels)
    config_labels = [m["key"] for m in split_meta]

    dp_total = db.get_dp_amount(None, session_id) or 0
    dp_used  = db.get_dp_used(None, session_id) or 0
    dp_remaining = max(dp_total - dp_used, 0)

    return jsonify({
        "session_id": session_id,
        "rows": rows,
        "group_subtotals": group_subtotals,
        "split_labels": config_labels,
        "split_meta": split_meta,
        "present_groups": present_groups,
        "dp_amount": int(dp_total),
        "dp_remaining": int(dp_remaining),
        "ts": datetime.utcnow().isoformat() + "Z",
    })
