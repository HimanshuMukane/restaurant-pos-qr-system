import os
import re
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from ..authz import roles_required
from ..helpers import load_menu, split_item_and_dish
from utils import db
from psycopg.rows import dict_row

bp = Blueprint("analytics", __name__)

JAKARTA_TZ = 'Asia/Jakarta'

# Keep in sync with modifier presets in static/js/edit.js and static/js/menu.js
MODIFIER_PRESETS = {
    "bar": [
        "Ekstra Es",
        "Gula Pisah",
        "Gula Sedikit",
        "Di Gelas",
        "Pakai Es",
        "Panas",
        "Sedikit Es",
        "Tanpa Gula",
        "Tanpa Susu",
        "Es Gula Dikit",
        "Es Gula Pisah",
        "Tanpa Es",
        "Biasa",
        "Hangat",
        "Gula Merah",
        "Es Pisah",
        "Murni",
    ],
    "kitchen": [
        "Pedas",
        "Dibatok",
        "1 Ekor",
        "2 Ekor",
        "3 Ekor",
        "4 Ekor",
        "Kuah Banyak",
        "Tanpa Terasi",
        "1/2 Porsi",
        "1 Porsi",
        "2 Porsi",
        "3 Porsi",
        "4 Porsi",
        "Tanpa Cabe",
        "Tidak Pedas",
        "Cabe Dikit",
        "Piring",
        "Tambahan",
        "Kuah Pisah",
        "Rebus",
        "Saus Padang",
        "Saus Tiram",
        "Lada Hitam",
        "Tauco",
        "Jadi 2 Piring",
        "Tanpa Kepala",
        "Tanpa Tauco",
        "Kupas Tanpa Micin",
        "Bungkus",
        "Murni",
        "Spesial",
        "Wes Mileh",
        "Kecil",
        "Besar",
        "Wes Metu",
        "Bumbu Tebel",
        "Kepitingnya Campur",
        "Asem Manis",
        "Nyisain",
        "Kipas",
        "Bakar Rica",
        "Masak",
        "Steam",
        "Nunggu Orangnya",
    ],
}

_MOD_WS_RE = re.compile(r"\s+")
_MOD_SPLIT_RE = re.compile(r"(?:\u2022|[,;|]+|\s+/\s+)")
_MOD_STATION_RE = re.compile(r"\[\[station:[^\]]+\]\]", re.IGNORECASE)

def _normalize_modifier_token(token: str) -> str:
    cleaned = _MOD_WS_RE.sub(" ", (token or "").strip())
    return cleaned.casefold()

def _split_modifier_tokens(note: str) -> list[str]:
    if not note:
        return []
    clean = _MOD_STATION_RE.sub(" ", note).strip()
    if not clean:
        return []
    parts = _MOD_SPLIT_RE.split(clean)
    tokens = []
    for part in parts:
        cleaned = _MOD_WS_RE.sub(" ", (part or "").strip())
        if cleaned:
            tokens.append(cleaned)
    return tokens

_PRESET_MODIFIER_DISPLAY: dict[str, str] = {}
for _items in MODIFIER_PRESETS.values():
    for _item in _items:
        _key = _normalize_modifier_token(_item)
        if _key and _key not in _PRESET_MODIFIER_DISPLAY:
            _PRESET_MODIFIER_DISPLAY[_key] = _item

def _date_range_from_request(args):
    """Return (from_date_str, to_date_str) in ISO (YYYY-MM-DD). Default = today..today."""
    try:
        fr = (args.get("from") or "").strip()
        to = (args.get("to") or "").strip()
        today = datetime.now().date()
        if not fr: fr = today.isoformat()
        if not to: to = today.isoformat()
        if fr > to:
            fr, to = to, fr
        return fr, to
    except Exception:
        today = datetime.now().date()
        return today.isoformat(), today.isoformat()

def _utc_bounds(fr_date_iso: str, to_date_iso: str, tzname: str = JAKARTA_TZ):
    """
    Convert local-date [fr..to] (inclusive) in tzname to UTC bounds:
      start_utc = fr 00:00 local
      end_utc   = (to+1) 00:00 local (exclusive)
    """
    tz = ZoneInfo(tzname)
    try:
        fr_date = date.fromisoformat(fr_date_iso)
        to_date = date.fromisoformat(to_date_iso)
    except Exception:
        today = datetime.now(tz).date()
        fr_date = today
        to_date = today
    start_local = datetime.combine(fr_date, time.min, tzinfo=tz)
    end_local = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

def _tz_bounds(fr_date_iso: str, to_date_iso: str, tzname: str = JAKARTA_TZ):
    """
    Convert local-date [fr..to] (inclusive) in tzname to UTC timestamp bounds:
      start = fr 00:00 tz -> UTC
      end   = (to+1) 00:00 tz -> UTC   (exclusive)
    We pass fr/to and tz to SQL and compute there with AT TIME ZONE.
    """
    return fr_date_iso, to_date_iso, tzname

def _qr_creator_clauses(alias="oi"):
    """
    Reuse the QR attribution rule (same as sessions/print):
    match by QR_USER_ID env and/or username 'qr_service' (QR_USERNAME override).
    """
    clauses = []
    params = []
    qr_uid_env = os.getenv("QR_USER_ID", "").strip()
    try:
        qr_uid = int(qr_uid_env) if qr_uid_env else None
    except ValueError:
        qr_uid = None
    if qr_uid:
        clauses.append(f"{alias}.created_by_user_id = %s")
        params.append(qr_uid)

    qr_uname = (os.getenv("QR_USERNAME") or "qr_service").strip()
    if qr_uname:
        clauses.append(
            f"EXISTS (SELECT 1 FROM public.users u WHERE u.id = {alias}.created_by_user_id AND LOWER(u.username) = LOWER(%s))"
        )
        params.append(qr_uname)

    if not clauses:
        return "", []
    return " AND (" + " OR ".join(clauses) + ")", params


def _menu_bucket_lookup():
    """
    Build a lookup of item/dish name -> rollup bucket using menu.json.
    - If a subcategory has dishes, roll up to the subcategory name.
    - If it has no dishes and uses unit 'ons' (weight-based), roll up to the category name.
    - Otherwise keep the subcategory itself.
    """
    menu = load_menu()
    mapping = {}
    for cat, subs in (menu or {}).items():
        if not isinstance(subs, dict):
            continue
        for sub, meta in (subs or {}).items():
            if not isinstance(meta, dict):
                continue
            unit = (meta.get("unit") or "").strip() or None
            dishes = meta.get("dishes") or []
            unit_norm = (unit or "").casefold()

            bucket_label = sub
            if not dishes and unit_norm == "ons":
                bucket_label = cat

            info = {
                "bucket": bucket_label,
                "category": cat,
                "subcategory": sub,
                "unit": unit,
            }

            key_sub = (sub or "").strip().casefold()
            if key_sub:
                mapping[key_sub] = info

            for d in dishes:
                name = d.get("name") if isinstance(d, dict) else str(d)
                key_d = (name or "").strip().casefold()
                if key_d:
                    mapping[key_d] = info
    return mapping


def _resolve_bucket(item_name: str, lookup: dict[str, dict]):
    """
    Given an order item label, pick the rollup bucket using lookup with a dash-aware fallback.
    Returns (bucket_label, unit, category, subcategory).
    """
    label = (item_name or "").strip()
    base, _ = split_item_and_dish(label)

    for key in (
        label.casefold() if label else "",
        base.casefold() if base else "",
    ):
        if key and key in lookup:
            info = lookup[key]
            return (
                info.get("bucket") or base or label,
                info.get("unit"),
                info.get("category"),
                info.get("subcategory"),
            )

    bucket = base or label or "(Unknown)"
    return bucket, None, None, None


def _is_crab_or_fish(category: str | None, item_name: str | None) -> bool:
    cat = (category or "").strip().casefold()
    if cat == "ikan" or cat.startswith("kepiting"):
        return True
    label = (item_name or "").strip().casefold()
    return ("kepiting" in label) or ("ikan" in label)

@bp.get("/api/analytics/overview")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_overview():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # ---- Per-day totals from NON-REFUND payments + refunds & reversal per-day ----
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      ),
      nonref AS (
        SELECT p.*
        FROM payments p, bounds b
        WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
          AND COALESCE(p.is_refund,false) = false
          AND COALESCE(p.is_dp,false)     = false
      ),
      days AS (
        SELECT generate_series(%s::date, %s::date, INTERVAL '1 day')::date AS d
      ),
      refunds_by_day AS (
        SELECT
          (COALESCE(orig.paid_at, p.paid_at) AT TIME ZONE %s)::date AS d,
          SUM(ABS(COALESCE(p.amount,0)))::bigint AS refunds_abs
        FROM payments p
        LEFT JOIN payments orig ON orig.id = p.refund_of,
        bounds b
        WHERE COALESCE(p.is_refund,false) = true
          AND LOWER(COALESCE(p.method,'refund')) = 'refund'
          AND COALESCE(orig.is_dp,false) = false   -- ignore DP refunds
          -- filter by ORIGINAL transaction date (fallback refund date)
          AND COALESCE(orig.paid_at, p.paid_at) >= b.start_utc
          AND COALESCE(orig.paid_at, p.paid_at) <  b.end_utc
        GROUP BY 1
      ),
      reopens_by_day AS (
        SELECT
          (COALESCE(orig.paid_at, p.paid_at) AT TIME ZONE %s)::date AS d,
          SUM(ABS(COALESCE(p.amount,0)))::bigint AS reopens_abs
        FROM payments p
        LEFT JOIN payments orig ON orig.id = p.refund_of,
        bounds b
        WHERE COALESCE(p.is_refund,false) = true
          AND LOWER(COALESCE(p.method,'')) <> 'refund'
          AND COALESCE(orig.is_dp,false) = false   -- ignore DP refunds/reopens
          -- same: attribute to original payment date
          AND COALESCE(orig.paid_at, p.paid_at) >= b.start_utc
          AND COALESCE(orig.paid_at, p.paid_at) <  b.end_utc
        GROUP BY 1
      )
      SELECT
        d.d AS d,
        COALESCE(SUM(COALESCE(n.total_before_discount,0)),0)::bigint AS subtotal,
        COALESCE(SUM(COALESCE(n.discount_amount,0)),0)::bigint       AS discount,
        COALESCE(SUM(COALESCE(n.service,0)),0)::bigint               AS service,
        COALESCE(SUM(COALESCE(n.tax,0)),0)::bigint                   AS tax,
        COALESCE(SUM(COALESCE(n.dp_applied_amount,0)),0)::bigint     AS dp_used,
        COALESCE(SUM(COALESCE(n.amount,0)),0)::bigint                AS net_amount,
        -- NEW: sum of FINAL bill totals (after rounding) = amount + DP used
        COALESCE(
          SUM(
            COALESCE(n.amount,0) + COALESCE(n.dp_applied_amount,0)
          ),
          0
        )::bigint                                                   AS gross_rounded,
        COALESCE(rb.refunds_abs,0)::bigint                           AS refunds_abs_day,
        COALESCE(rpb.reopens_abs,0)::bigint                          AS reopens_abs_day
      FROM days d
      LEFT JOIN nonref n           ON ((n.paid_at AT TIME ZONE %s)::date = d.d)
      LEFT JOIN refunds_by_day rb  ON rb.d = d.d
      LEFT JOIN reopens_by_day rpb ON rpb.d = d.d
      GROUP BY d.d, rb.refunds_abs, rpb.reopens_abs
      ORDER BY d.d
    """, (start_utc, end_utc, fr_iso, to_iso, tzname, tzname, tzname))
    times = c.fetchall()

    # ---- Book totals from NON-REFUND payments ----
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      ),
      nonref AS (
        SELECT p.*
        FROM payments p, bounds b
        WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
          AND COALESCE(p.is_refund,false) = false
          AND COALESCE(p.is_dp,false)     = false
      )
      SELECT
        SUM(COALESCE(nonref.total_before_discount,0))::bigint AS subtotal,
        SUM(COALESCE(nonref.discount_amount,0))::bigint       AS discount,
        SUM(COALESCE(nonref.service,0))::bigint               AS service,
        SUM(COALESCE(nonref.tax,0))::bigint                   AS tax,
        SUM(COALESCE(nonref.dp_applied_amount,0))::bigint     AS dp_used,
        SUM(COALESCE(nonref.amount,0))::bigint                AS net_amount_nonrefund,
        -- NEW: sum of FINAL bill totals (after rounding) = amount + DP
        SUM(
          COALESCE(nonref.amount,0) + COALESCE(nonref.dp_applied_amount,0)
        )::bigint                                             AS gross_rounded_total,
        COUNT(*)::int                                         AS payments_cnt_eff,
        COUNT(DISTINCT nonref.session_id)::int                AS sessions_eff
      FROM nonref
    """, (start_utc, end_utc))
    tot = c.fetchone() or {}

    # ---- Refunds ABS (method='refund'); Reversal ABS (method!='refund') ----
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT COALESCE(SUM(ABS(COALESCE(p.amount,0))),0)::bigint AS refunds_abs
      FROM payments p
      LEFT JOIN payments orig ON orig.id = p.refund_of,
      bounds b
      WHERE COALESCE(p.is_refund,false) = true
        AND LOWER(COALESCE(p.method,'refund')) = 'refund'
        AND COALESCE(orig.is_dp,false) = false   -- ignore DP refunds
        -- filter by ORIGINAL transaction date
        AND COALESCE(orig.paid_at, p.paid_at) >= b.start_utc
        AND COALESCE(orig.paid_at, p.paid_at) <  b.end_utc
    """, (start_utc, end_utc))
    refunds_abs = int((c.fetchone() or {"refunds_abs": 0})["refunds_abs"] or 0)

    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT COALESCE(SUM(ABS(COALESCE(p.amount,0))),0)::bigint AS reopens_abs
      FROM payments p
      LEFT JOIN payments orig ON orig.id = p.refund_of,
      bounds b
      WHERE COALESCE(p.is_refund,false) = true
        AND LOWER(COALESCE(p.method,'')) <> 'refund'
        AND COALESCE(orig.is_dp,false) = false   -- ignore DP refunds/reopens
        -- filter by ORIGINAL transaction date
        AND COALESCE(orig.paid_at, p.paid_at) >= b.start_utc
        AND COALESCE(orig.paid_at, p.paid_at) <  b.end_utc
    """, (start_utc, end_utc))
    reopens_abs = int((c.fetchone() or {"reopens_abs": 0})["reopens_abs"] or 0)

    conn.close()

    subtotal_total  = int(tot.get("subtotal") or 0)
    discount_total  = int(tot.get("discount") or 0)
    service_total   = int(tot.get("service")  or 0)
    tax_total       = int(tot.get("tax")      or 0)
    dp_used_total   = int(tot.get("dp_used")  or 0)

    net_amount_nonrefund = int(tot.get("net_amount_nonrefund") or 0)
    gross_rounded_total  = int(tot.get("gross_rounded_total")  or 0)

    payments_count  = int(tot.get("payments_cnt_eff") or 0)
    sessions_closed = int(tot.get("sessions_eff") or 0)

    # Book/theoretical gross from components (before Rp 100 floor)
    book_gross = (subtotal_total - discount_total) + service_total + tax_total

    # Total pembulatan (= book minus sum of FINAL bill totals from payments)
    pembulatan_total = book_gross - gross_rounded_total

    # Kas Masuk: USE FINAL TRANSACTIONS (after rounding, DP applied)
    # This matches the "Total" line on final receipts summed over the period.
    kas_masuk = gross_rounded_total

    # Refunds / Reversal as negatives
    refunds_net = -refunds_abs
    reopen_net  = -reopens_abs

    # Final Gross = Kas Masuk - Refunds - Reversal
    gross = kas_masuk + refunds_net + reopen_net

    aov_per_session = (kas_masuk / max(1, sessions_closed)) if sessions_closed else 0

    # Daily series: include both refunds and reversal as negatives
    times_out = []
    for r in times:
        d = r["d"]

        # Book/day gross (before Rp 100 floor)
        book_gross_day = (
            int(r["subtotal"] or 0)
            - int(r["discount"] or 0)
            + int(r["service"]  or 0)
            + int(r["tax"]      or 0)
        )

        # Sum of FINAL bill totals for that day
        gross_rounded_day = int(r.get("gross_rounded") or 0)

        pembulatan_day = book_gross_day - gross_rounded_day

        # Kas Masuk per day = FINAL totals (rounded) before refunds
        kas_day = gross_rounded_day

        refunds_day  = -(int(r.get("refunds_abs_day")  or 0))
        reversal_day = -(int(r.get("reopens_abs_day")  or 0))

        times_out.append({
            "date": getattr(d, "isoformat", lambda: str(d))(),
            "subtotal":   int(r["subtotal"] or 0),
            "discount":   int(r["discount"] or 0),
            "service":    int(r["service"]  or 0),
            "tax":        int(r["tax"]      or 0),
            "dp_used":    int(r["dp_used"]  or 0),
            "pembulatan": pembulatan_day,
            "kas_masuk":  kas_day,
            "refunds":    refunds_day,     # negative
            "reversal":   reversal_day,    # negative
            "gross":      kas_day + refunds_day + reversal_day
        })


    return jsonify({
        "timeseries": times_out,
        "kpi": {
            "subtotal_total":  subtotal_total,
            "discount_total":  discount_total,
            "service_total":   service_total,
            "tax_total":       tax_total,
            "dp_used_total":   dp_used_total,

            # NEW: total rounding difference for the period
            "pembulatan_total": pembulatan_total,

            "kas_masuk":       kas_masuk,
            "refunds_net":     refunds_net,    # negative
            "reopen_net":      reopen_net,     # negative
            "gross":           gross,          # now based on FINAL bills
            "gross_after_refunds": gross,      # kept for compatibility

            "payments_count":  payments_count,
            "sessions_closed": sessions_closed,
            "aov_per_session": aov_per_session,
        }
    })



@bp.get("/api/analytics/trends")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_trends():
    """
    Return trend data grouped by:
      group=hour  →  0–23 (jam)
      group=dow   →  0–6  (Minggu..Sabtu)
      group=month →  1–12 (Jan..Des)
      group=year  →  tahun
    Metrics:
      - money_tx: average & total Kas Masuk per slot
      - arrivals: pattern of waktu masuk (sessions.created_at)
    """
    from math import floor

    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    group = (request.args.get("group") or "hour").lower()
    if group not in ("hour", "dow", "month", "year"):
        group = "hour"

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # ---------- MONEY + TRANSACTIONS ----------
    money_slots = []

    if group == "hour":
        # Per jam: avg & total kas + tx per jam-of-day
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          nonref AS (
            SELECT
              (p.paid_at AT TIME ZONE %s) AS paid_local,
              COALESCE(p.amount,0) + COALESCE(p.dp_applied_amount,0) AS kas
            FROM payments p, bounds b
            WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
              AND COALESCE(p.is_refund,false) = false
              AND COALESCE(p.is_dp,false)     = false
          ),
          per_day_hour AS (
            SELECT
              date_trunc('day', paid_local)::date AS d,
              EXTRACT(HOUR FROM paid_local)::int AS hh,
              SUM(kas)::bigint AS kas_sum,
              COUNT(*)::int    AS tx_count
            FROM nonref
            GROUP BY 1,2
          )
          SELECT
            hh,
            AVG(kas_sum)::bigint   AS avg_kas,
            SUM(kas_sum)::bigint   AS total_kas,
            AVG(tx_count)::numeric AS avg_tx,
            SUM(tx_count)::bigint  AS total_tx,
            COUNT(*)::int          AS slot_days
          FROM per_day_hour
          GROUP BY hh
          ORDER BY hh
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        for r in rows:
            hh = int(r["hh"])
            label = f"{hh:02d}:00"
            money_slots.append({
                "key": hh,
                "label": label,
                "avg_amount": int(r["avg_kas"] or 0),
                "total_amount": int(r["total_kas"] or 0),
                "avg_tx": float(r["avg_tx"] or 0),
                "total_tx": int(r["total_tx"] or 0),
                "sample_cnt": int(r["slot_days"] or 0),
            })

    elif group == "dow":
        # Per hari (Senin..Minggu), pakai rata-rata per-hari
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          nonref AS (
            SELECT
              (p.paid_at AT TIME ZONE %s)::date AS paid_date,
              COALESCE(p.amount,0) + COALESCE(p.dp_applied_amount,0) AS kas
            FROM payments p, bounds b
            WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
              AND COALESCE(p.is_refund,false) = false
              AND COALESCE(p.is_dp,false)     = false
          ),
          per_day AS (
            SELECT
              paid_date AS d,
              SUM(kas)::bigint AS kas_sum,
              COUNT(*)::int    AS tx_count
            FROM nonref
            GROUP BY 1
          )
          SELECT
            EXTRACT(DOW FROM d)::int AS dow,
            AVG(kas_sum)::bigint     AS avg_kas,
            SUM(kas_sum)::bigint     AS total_kas,
            AVG(tx_count)::numeric   AS avg_tx,
            SUM(tx_count)::bigint    AS total_tx,
            COUNT(*)::int            AS days_cnt
          FROM per_day
          GROUP BY 1
          ORDER BY 1
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        # 0=Min,1=Sen,...,6=Sab
        dow_labels = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"]
        for r in rows:
            dow = int(r["dow"])
            label = dow_labels[dow] if 0 <= dow < len(dow_labels) else str(dow)
            money_slots.append({
                "key": dow,
                "label": label,
                "avg_amount": int(r["avg_kas"] or 0),
                "total_amount": int(r["total_kas"] or 0),
                "avg_tx": float(r["avg_tx"] or 0),
                "total_tx": int(r["total_tx"] or 0),
                "sample_cnt": int(r["days_cnt"] or 0),
            })

    elif group == "month":
        # Per bulan (Jan..Des), pakai rata-rata per-bulan
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          nonref AS (
            SELECT
              (p.paid_at AT TIME ZONE %s) AS paid_local,
              COALESCE(p.amount,0) + COALESCE(p.dp_applied_amount,0) AS kas
            FROM payments p, bounds b
            WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
              AND COALESCE(p.is_refund,false) = false
              AND COALESCE(p.is_dp,false)     = false
          ),
          per_month AS (
            SELECT
              date_trunc('month', paid_local)::date AS ym,
              SUM(kas)::bigint AS kas_sum,
              COUNT(*)::int    AS tx_count
            FROM nonref
            GROUP BY 1
          )
          SELECT
            EXTRACT(MONTH FROM ym)::int AS mm,
            AVG(kas_sum)::bigint        AS avg_kas,
            SUM(kas_sum)::bigint        AS total_kas,
            AVG(tx_count)::numeric      AS avg_tx,
            SUM(tx_count)::bigint       AS total_tx,
            COUNT(*)::int               AS months_cnt
          FROM per_month
          GROUP BY 1
          ORDER BY 1
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        month_labels = [None, "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                        "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        for r in rows:
            mm = int(r["mm"])
            label = month_labels[mm] if 1 <= mm < len(month_labels) else str(mm)
            money_slots.append({
                "key": mm,
                "label": label,
                "avg_amount": int(r["avg_kas"] or 0),
                "total_amount": int(r["total_kas"] or 0),
                "avg_tx": float(r["avg_tx"] or 0),
                "total_tx": int(r["total_tx"] or 0),
                "sample_cnt": int(r["months_cnt"] or 0),
            })

    elif group == "year":
        # Per tahun – di sini total per tahun cukup, avg == total (1 sample per tahun)
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          nonref AS (
            SELECT
              (p.paid_at AT TIME ZONE %s) AS paid_local,
              COALESCE(p.amount,0) + COALESCE(p.dp_applied_amount,0) AS kas
            FROM payments p, bounds b
            WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
              AND COALESCE(p.is_refund,false) = false
              AND COALESCE(p.is_dp,false)     = false
          )
          SELECT
            EXTRACT(YEAR FROM paid_local)::int AS yy,
            SUM(kas)::bigint                   AS total_kas,
            COUNT(*)::bigint                   AS total_tx
          FROM nonref
          GROUP BY 1
          ORDER BY 1
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        for r in rows:
            yy = int(r["yy"])
            total_kas = int(r["total_kas"] or 0)
            total_tx = int(r["total_tx"] or 0)
            money_slots.append({
                "key": yy,
                "label": str(yy),
                "avg_amount": total_kas,   # 1 sample per tahun → avg == total
                "total_amount": total_kas,
                "avg_tx": float(total_tx),
                "total_tx": total_tx,
                "sample_cnt": 1,
            })

    # ---------- ARRIVALS (WAKTU MASUK) ----------
    arrival_slots = []

    if group == "hour":
        # Berapa sesi rata-rata masuk per jam-of-day
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          sess AS (
            SELECT
              (s.created_at AT TIME ZONE %s) AS created_local
            FROM sessions s, bounds b
            WHERE s.created_at >= b.start_utc AND s.created_at < b.end_utc
          ),
          per_day_hour AS (
            SELECT
              date_trunc('day', created_local)::date AS d,
              EXTRACT(HOUR FROM created_local)::int AS hh,
              COUNT(*)::int                          AS sess_cnt
            FROM sess
            GROUP BY 1,2
          )
          SELECT
            hh,
            AVG(sess_cnt)::numeric AS avg_sessions,
            SUM(sess_cnt)::bigint  AS total_sessions,
            COUNT(*)::int          AS days_cnt
          FROM per_day_hour
          GROUP BY hh
          ORDER BY hh
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        for r in rows:
            hh = int(r["hh"])
            label = f"{hh:02d}:00"
            arrival_slots.append({
                "key": hh,
                "label": label,
                "avg_sessions": float(r["avg_sessions"] or 0),
                "total_sessions": int(r["total_sessions"] or 0),
                "sample_cnt": int(r["days_cnt"] or 0),
            })

    elif group == "dow":
        # Rata-rata JAM masuk (time-of-day) per hari (Sen..Minggu)
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          sess AS (
            SELECT
              (s.created_at AT TIME ZONE %s) AS created_local
            FROM sessions s, bounds b
            WHERE s.created_at >= b.start_utc AND s.created_at < b.end_utc
          ),
          per_session AS (
            SELECT
              EXTRACT(DOW FROM created_local)::int    AS dow,
              EXTRACT(EPOCH FROM created_local::time) AS sec_since_midnight
            FROM sess
          )
          SELECT
            dow,
            AVG(sec_since_midnight)::numeric AS avg_sec,
            COUNT(*)::bigint                 AS sessions_cnt
          FROM per_session
          GROUP BY dow
          ORDER BY dow
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        dow_labels = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"]

        for r in rows:
            dow = int(r["dow"])
            label = dow_labels[dow] if 0 <= dow < len(dow_labels) else str(dow)
            avg_sec = float(r["avg_sec"] or 0.0)
            arrival_slots.append({
                "key": dow,
                "label": label,
                "avg_seconds": avg_sec,
                "sessions_cnt": int(r["sessions_cnt"] or 0),
            })

    elif group == "month":
        # Rata-rata jam masuk per bulan (pattern puasa dll)
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          sess AS (
            SELECT
              (s.created_at AT TIME ZONE %s) AS created_local
            FROM sessions s, bounds b
            WHERE s.created_at >= b.start_utc AND s.created_at < b.end_utc
          ),
          per_session AS (
            SELECT
              EXTRACT(MONTH FROM created_local)::int AS mm,
              EXTRACT(EPOCH FROM created_local::time) AS sec_since_midnight
            FROM sess
          )
          SELECT
            mm,
            AVG(sec_since_midnight)::numeric AS avg_sec,
            COUNT(*)::bigint                 AS sessions_cnt
          FROM per_session
          GROUP BY mm
          ORDER BY mm
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        month_labels = [None, "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                        "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

        for r in rows:
            mm = int(r["mm"])
            label = month_labels[mm] if 1 <= mm < len(month_labels) else str(mm)
            avg_sec = float(r["avg_sec"] or 0.0)
            arrival_slots.append({
                "key": mm,
                "label": label,
                "avg_seconds": avg_sec,
                "sessions_cnt": int(r["sessions_cnt"] or 0),
            })

    elif group == "year":
        # Rata-rata jam masuk per tahun (lebih ke curiosity)
        c.execute("""
          WITH bounds AS (
            SELECT
              %s::timestamptz AS start_utc,
              %s::timestamptz AS end_utc
          ),
          sess AS (
            SELECT
              (s.created_at AT TIME ZONE %s) AS created_local
            FROM sessions s, bounds b
            WHERE s.created_at >= b.start_utc AND s.created_at < b.end_utc
          ),
          per_session AS (
            SELECT
              EXTRACT(YEAR FROM created_local)::int AS yy,
              EXTRACT(EPOCH FROM created_local::time) AS sec_since_midnight
            FROM sess
          )
          SELECT
            yy,
            AVG(sec_since_midnight)::numeric AS avg_sec,
            COUNT(*)::bigint                 AS sessions_cnt
          FROM per_session
          GROUP BY yy
          ORDER BY yy
        """, (start_utc, end_utc, tzname))
        rows = c.fetchall()
        for r in rows:
            yy = int(r["yy"])
            avg_sec = float(r["avg_sec"] or 0.0)
            arrival_slots.append({
                "key": yy,
                "label": str(yy),
                "avg_seconds": avg_sec,
                "sessions_cnt": int(r["sessions_cnt"] or 0),
            })

    conn.close()

    # Small helper: also add a preformatted "avg_time" string for arrivals with avg_seconds
    def _fmt_clock(sec: float) -> str:
        if sec is None:
            return "-"
        total_minutes = int(round(sec / 60.0))
        hh = (total_minutes // 60) % 24
        mm = total_minutes % 60
        return f"{hh:02d}:{mm:02d}"

    for slot in arrival_slots:
        if "avg_seconds" in slot:
            slot["avg_time"] = _fmt_clock(slot.get("avg_seconds") or 0)

    return jsonify({
        "group": group,
        "money_tx": money_slots,
        "arrivals": arrival_slots,
    })

@bp.get("/api/analytics/payments_mix")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_payments_mix():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    params = (start_utc, end_utc)

    # 1) METHODS: make it match OVERVIEW.GROSS but broken down by original method.
    #
    # - Positives: final non-DP payments in range (same as overview "Kas Masuk"),
    #   using amount + dp_applied_amount.
    # - Negatives: ALL is_refund=true rows in range (refunds + reopen),
    #   using ABS(amount) as in overview, but attributed back to the
    #   ORIGINAL payment's method via refund_of.
    #
    #   Sum(method.amt) = kas_masuk - refunds_abs - reopens_abs = overview.gross

    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      ),

      -- Final payments (non-refund, non-DP) in range: same population as overview "Kas Masuk"
      final_non_dp AS (
        SELECT p.*
        FROM payments p, bounds b
        WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
          AND COALESCE(p.is_refund,false) = false
          AND COALESCE(p.is_dp,false)     = false
      ),

      -- Base per-method totals: count + sum(Total Final) = amount + dp_applied_amount
      base AS (
        SELECT
          CASE
            WHEN LOWER(COALESCE(method,'')) IN ('card','credit') THEN
              COALESCE(NULLIF(LOWER(card_type),''), 'card')
            WHEN LOWER(COALESCE(method,'')) = 'debit'    THEN 'debit'
            WHEN LOWER(COALESCE(method,'')) = 'transfer' THEN 'transfer'
            WHEN LOWER(COALESCE(method,'')) = 'cash'     THEN 'cash'
            ELSE LOWER(COALESCE(method,'unknown'))
          END AS method,
          COUNT(*)::int AS cnt,
          SUM(
            COALESCE(amount,0) + COALESCE(dp_applied_amount,0)
          )::bigint AS base_amt
        FROM final_non_dp
        GROUP BY 1
      ),

      -- All refund / reopen rows in range, attributed to ORIGINAL payment date
      refund_rows AS (
        SELECT
          r.id,
          r.refund_of,
          r.amount,
          r.method AS refund_method,
          COALESCE(orig.method, r.method, 'unknown') AS eff_method,
          COALESCE(orig.card_type, r.card_type, '') AS eff_card_type,
          CASE
            WHEN LOWER(COALESCE(r.method,'refund')) = 'refund'
              THEN 'refund'
            ELSE 'reopen'
          END AS refund_kind,
          COALESCE(orig.paid_at, r.paid_at) AS eff_paid_at
        FROM payments r
        LEFT JOIN payments orig ON orig.id = r.refund_of,
        bounds b
        WHERE COALESCE(r.is_refund,false) = true
          AND COALESCE(orig.is_dp,false) = false   -- ignore refunds of DP
          -- use ORIGINAL payment date for range filtering
          AND COALESCE(orig.paid_at, r.paid_at) >= b.start_utc
          AND COALESCE(orig.paid_at, r.paid_at) <  b.end_utc
      ),


      -- Negative adjustments per refund/reopen row:
      -- use ABS(amount) (same as overview), and attach to original method (eff_method).
      neg AS (
        SELECT
          CASE
            WHEN LOWER(COALESCE(eff_method,'')) IN ('card','credit') THEN
              COALESCE(NULLIF(LOWER(eff_card_type),''), 'card')
            WHEN LOWER(COALESCE(eff_method,'')) = 'debit'    THEN 'debit'
            WHEN LOWER(COALESCE(eff_method,'')) = 'transfer' THEN 'transfer'
            WHEN LOWER(COALESCE(eff_method,'')) = 'cash'     THEN 'cash'
            ELSE LOWER(COALESCE(eff_method,'unknown'))
          END AS method,
          -ABS(COALESCE(amount,0))::bigint AS adj_amt
        FROM refund_rows
      ),

      neg_agg AS (
        SELECT
          method,
          SUM(adj_amt)::bigint AS adj_amt
        FROM neg
        GROUP BY method
      )

      SELECT
        COALESCE(b.method, n.method) AS method,
        COALESCE(b.cnt, 0)::int      AS cnt,
        (COALESCE(b.base_amt,0) + COALESCE(n.adj_amt,0))::bigint AS amt
      FROM base b
      FULL OUTER JOIN neg_agg n
        ON n.method = b.method
      ORDER BY 1;
    """, params)
    methods = c.fetchall()

    # 2) DISCOUNTS: unchanged, still based on final payments only
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT COALESCE(discount_percent,0)::int AS pct,
             COUNT(*)::int AS cnt,
             SUM(COALESCE(discount_amount,0))::bigint AS rupiah
      FROM payments p, bounds b
      WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
        AND COALESCE(p.is_refund,false) = false
        AND COALESCE(p.is_dp,false)     = false
        AND COALESCE(discount_percent,0) > 0
      GROUP BY 1
      ORDER BY 1
    """, params)
    discounts = c.fetchall()

    # 3) RECON: keep old behaviour for now (non-refund payments, incl. DP top-ups).
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT
        SUM(COALESCE(dp_applied_amount,0))::bigint AS dp_used_total,
        SUM(COALESCE(amount,0))::bigint            AS net_collected
      FROM payments p, bounds b
      WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
        AND COALESCE(p.is_refund,false) = false
    """, params)
    recon = c.fetchone() or {"dp_used_total": 0, "net_collected": 0}

    conn.close()
    return jsonify({"methods": methods, "discounts": discounts, "recon": recon})



@bp.get("/api/analytics/by_hour")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_by_hour():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # Bucket by local hour (WIB); subtract both refund types,
    # but attribute refunds to ORIGINAL transaction time.
    c.execute("""
      WITH hours(hh) AS (SELECT to_char(generate_series(0,23), 'FM00')),
      bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      ),
      tx AS (
        SELECT
          -- effective timestamp for analytics
          CASE
            WHEN COALESCE(p.is_refund,false) = true
              THEN COALESCE(orig.paid_at, p.paid_at)
            ELSE p.paid_at
          END AS eff_paid_at,
          p.is_refund,
          p.is_dp,
          p.method,
          p.amount,
          p.dp_applied_amount,
          COALESCE(orig.is_dp,false) AS orig_is_dp
        FROM payments p
        LEFT JOIN payments orig ON orig.id = p.refund_of,
        bounds b
        WHERE
          CASE
            WHEN COALESCE(p.is_refund,false) = true
              THEN COALESCE(orig.paid_at, p.paid_at)
            ELSE p.paid_at
          END >= b.start_utc
          AND
          CASE
            WHEN COALESCE(p.is_refund,false) = true
              THEN COALESCE(orig.paid_at, p.paid_at)
            ELSE p.paid_at
          END <  b.end_utc
          AND (
            COALESCE(p.is_refund,false) = false
            OR COALESCE(orig.is_dp,false) = false  -- ignore DP refunds/reopens
          )
      )
      SELECT h.hh,
             COALESCE(SUM(
               CASE
                  -- Final bills only: non-refund AND not DP
                  WHEN COALESCE(t.is_refund,false) = false
                       AND COALESCE(t.is_dp,false) = false
                    THEN COALESCE(t.amount,0) + COALESCE(t.dp_applied_amount,0)
                  -- Refunds (non-DP) as negative
                  WHEN COALESCE(t.is_refund,false) = true
                       AND LOWER(COALESCE(t.method,'')) = 'refund'
                       AND COALESCE(t.orig_is_dp,false) = false
                    THEN -ABS(COALESCE(t.amount,0))
                  -- Reopen / reversal (non-DP) as negative
                  WHEN COALESCE(t.is_refund,false) = true
                       AND LOWER(COALESCE(t.method,'')) <> 'refund'
                       AND COALESCE(t.orig_is_dp,false) = false
                   THEN -ABS(COALESCE(t.amount,0))
                 ELSE 0
               END
             ),0)::bigint AS gross
      FROM hours h
      LEFT JOIN tx t
        ON to_char((t.eff_paid_at AT TIME ZONE %s), 'HH24') = h.hh
      GROUP BY h.hh
      ORDER BY h.hh
    """, (start_utc, end_utc, tzname))
    rows = c.fetchall()
    conn.close()
    return jsonify({"hours": rows})

@bp.get("/api/analytics/qr")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_qr():
    """
    QR performance: how many orders came from QR, value, status mix, per-table, and per-hour volume.
    Uses order_items created_by QR user/name as the attribution key.
    """
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    qr_clause, qr_params = _qr_creator_clauses("oi")
    net_qty_expr = "GREATEST(CASE WHEN COALESCE(oi.status,'') <> 'cancelled' THEN COALESCE(oi.qty,0) ELSE 0 END - COALESCE(oi.void_qty,0), 0)"

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    base_params = (start_utc, end_utc, *qr_params)

    # KPI rollup
    c.execute(
        f"""
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        ),
        qr_items AS (
          SELECT oi.*
          FROM public.order_items oi, bounds b
          WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
            {qr_clause}
        )
        SELECT
          COUNT(*)::int AS lines,
          COUNT(DISTINCT session_id)::int AS sessions,
          COUNT(DISTINCT table_number)::int AS tables,
          COALESCE(SUM({net_qty_expr}),0)::numeric AS qty_net,
          COALESCE(SUM({net_qty_expr} * oi.price),0)::bigint AS gross,
          COALESCE(SUM(
            CASE WHEN COALESCE(oi.status,'') IN ('new','edited') THEN {net_qty_expr} ELSE 0 END
          ),0)::numeric AS outstanding_qty,
          COALESCE(SUM(
            CASE WHEN COALESCE(oi.status,'') IN ('new','edited') THEN {net_qty_expr} * oi.price ELSE 0 END
          ),0)::bigint AS outstanding_gross
        FROM qr_items oi
        """,
        base_params,
    )
    k = c.fetchone() or {}

    # Share of revenue (all items in same window)
    c.execute(
        """
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        )
        SELECT COALESCE(SUM(
          GREATEST(CASE WHEN COALESCE(oi.status,'') <> 'cancelled' THEN COALESCE(oi.qty,0) ELSE 0 END - COALESCE(oi.void_qty,0), 0) * oi.price
        ),0)::bigint AS gross_all
        FROM public.order_items oi, bounds b
        WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
        """,
        (start_utc, end_utc),
    )
    gross_all_row = c.fetchone() or {"gross_all": 0}
    gross_all = int(gross_all_row.get("gross_all") or 0)

    def _as_int(v):
        try:
            return int(v)
        except Exception:
            try:
                return int(float(v or 0))
            except Exception:
                return 0

    def _as_float(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    lines = _as_int(k.get("lines"))
    sessions = _as_int(k.get("sessions"))
    tables_cnt = _as_int(k.get("tables"))
    qty_net = _as_float(k.get("qty_net"))
    gross = _as_int(k.get("gross"))
    outstanding_qty = _as_float(k.get("outstanding_qty"))
    outstanding_gross = _as_int(k.get("outstanding_gross"))

    kpi = {
        "lines": lines,
        "sessions": sessions,
        "tables": tables_cnt,
        "qty": qty_net,
        "gross": gross,
        "outstanding_qty": outstanding_qty,
        "outstanding_gross": outstanding_gross,
        "aov_per_session": (gross / sessions) if sessions else 0,
        "share_of_revenue": (gross / gross_all) if gross_all else 0.0,
    }

    # Status mix
    c.execute(
        f"""
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        ),
        qr_items AS (
          SELECT oi.*
          FROM public.order_items oi, bounds b
          WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
            {qr_clause}
        )
        , agg AS (
          SELECT
            COALESCE(oi.status,'(blank)') AS status,
            COUNT(*)::int AS lines,
            COALESCE(SUM({net_qty_expr}),0)::numeric AS qty,
            COALESCE(SUM({net_qty_expr} * oi.price),0)::bigint AS gross
          FROM qr_items oi
          GROUP BY COALESCE(oi.status,'(blank)')
        )
        SELECT *
        FROM agg
        ORDER BY
          CASE WHEN status IN ('new','edited') THEN 0 ELSE 1 END,
          status
        """,
        base_params,
    )
    statuses_raw = c.fetchall() or []
    statuses = [
        {
          "status": row.get("status"),
          "lines": _as_int(row.get("lines")),
          "qty": _as_float(row.get("qty")),
          "gross": _as_int(row.get("gross")),
        }
        for row in statuses_raw
    ]

    # Per-table leaders
    c.execute(
        f"""
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        ),
        qr_items AS (
          SELECT oi.*
          FROM public.order_items oi, bounds b
          WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
            {qr_clause}
        )
        SELECT
          oi.table_number,
          COUNT(DISTINCT oi.session_id)::int AS sessions,
          COUNT(*)::int AS lines,
          COALESCE(SUM({net_qty_expr}),0)::numeric AS qty,
          COALESCE(SUM({net_qty_expr} * oi.price),0)::bigint AS gross
        FROM qr_items oi
        GROUP BY oi.table_number
        ORDER BY gross DESC NULLS LAST, table_number
        LIMIT 12
        """,
        base_params,
    )
    tables_raw = c.fetchall() or []
    tables = [
        {
          "table_number": row.get("table_number"),
          "sessions": _as_int(row.get("sessions")),
          "lines": _as_int(row.get("lines")),
          "qty": _as_float(row.get("qty")),
          "gross": _as_int(row.get("gross")),
        }
        for row in tables_raw
    ]

    # Hourly pattern (local hour)
    c.execute(
        f"""
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        ),
        qr_items AS (
          SELECT oi.*
          FROM public.order_items oi, bounds b
          WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
            {qr_clause}
        )
        SELECT
          to_char((oi."timestamp" AT TIME ZONE %s), 'HH24') AS hh,
          COALESCE(SUM({net_qty_expr}),0)::numeric AS qty,
          COALESCE(SUM({net_qty_expr} * oi.price),0)::bigint AS gross
        FROM qr_items oi
        GROUP BY hh
        ORDER BY hh
        """,
        (*base_params, tzname),
    )
    hours_raw = c.fetchall() or []
    hours = [
        {"hh": row.get("hh"), "qty": _as_float(row.get("qty")), "gross": _as_int(row.get("gross"))}
        for row in hours_raw
    ]

    # Optional: legacy qr.qr_orders queue status (ignore errors if schema missing)
    queue = []
    try:
        c.execute(
            """
        WITH bounds AS (
          SELECT %s::timestamptz AS start_utc,
                 %s::timestamptz AS end_utc
        )
            SELECT
              COALESCE(qo.status,'unknown') AS status,
              COUNT(*)::int AS cnt
            FROM qr.qr_orders qo, bounds b
            WHERE qo.created_at >= b.start_utc AND qo.created_at < b.end_utc
            GROUP BY 1
            ORDER BY 1
            """,
            (start_utc, end_utc),
        )
        queue = [{"status": r.get("status"), "count": _as_int(r.get("cnt"))} for r in (c.fetchall() or [])]
    except Exception:
        queue = []

    conn.close()

    return jsonify({
        "kpi": kpi,
        "statuses": statuses,
        "tables": tables,
        "hours": hours,
        "queue": queue,
    })

@bp.get("/api/analytics/ops")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_ops():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT table_number,
             COUNT(*)::int AS sessions,
             AVG(EXTRACT(EPOCH FROM (COALESCE(closed_at, created_at) - created_at)) / 60.0)::float AS avg_minutes
      FROM sessions s, bounds b
      WHERE s.created_at >= b.start_utc AND s.created_at < b.end_utc
        AND s.status IN ('closed','cancelled','active')
      GROUP BY table_number
      ORDER BY sessions DESC, table_number
    """, (start_utc, end_utc))
    by_table = c.fetchall()

    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT COUNT(DISTINCT session_id)::int AS split_sessions
      FROM payments p, bounds b
      WHERE p.bill_group IS NOT NULL
        AND p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
    """, (start_utc, end_utc))
    split_sessions = (c.fetchone() or {"split_sessions": 0})["split_sessions"] or 0

    conn.close()
    return jsonify({"tables": by_table, "split_sessions": split_sessions})

@bp.get("/api/analytics/items_detail")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_items_detail():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20

    # NEW: attribution mode
    attr = (request.args.get("attr") or "pay").lower()
    if attr == "print":
        attr = "printed"
    if attr not in ("pay", "close", "order", "printed"):
        attr = "pay"

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # Build CTE pieces per attribution mode
    status_filter = ""
    if attr == "pay":
        session_cte = """
          , last_paid AS (
              SELECT p.session_id, MAX(p.paid_at) AS last_paid_at
              FROM public.payments p
              WHERE COALESCE(p.is_refund,false)=false
                AND COALESCE(p.is_dp,false)=false
              GROUP BY p.session_id
            )
          , sessions_in_range AS (
              SELECT lp.session_id AS id
              FROM last_paid lp, bounds b
              WHERE lp.last_paid_at >= b.start_utc AND lp.last_paid_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""  # date comes from last payment, not order time

    elif attr == "close":
        session_cte = """
          , sessions_in_range AS (
              SELECT s.id
              FROM public.sessions s, bounds b
              WHERE s.status IN ('closed','cancelled')
                AND s.closed_at >= b.start_utc AND s.closed_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""  # date comes from closed_at

    elif attr == "order":
        # Keep anti-test filter: only sessions that are closed or have ever had a non-refund payment
        session_cte = """
          , closed_sessions AS (SELECT id FROM public.sessions WHERE status IN ('closed','cancelled'))
          , paid_sessions   AS (
              SELECT DISTINCT session_id AS id
              FROM public.payments
              WHERE COALESCE(is_refund,false)=false
                AND COALESCE(is_dp,false)=false
            )
          , good_sessions   AS (
              SELECT id FROM closed_sessions
              UNION
              SELECT id FROM paid_sessions
            )
        """
        join_sessions = "JOIN good_sessions gs ON gs.id = oi.session_id"
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
    else:  # "printed"
        session_cte = ""
        join_sessions = ""
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
        status_filter = "AND COALESCE(oi.status,'') IN ('printed','served','paid','cancelled')"

    sql = f"""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      {session_cte}
      SELECT
        oi.item_name,
        SUM(CASE WHEN oi.status='cancelled' THEN oi.qty ELSE 0 END)                                                   AS qty_cancelled,
        SUM(CASE WHEN oi.status<>'cancelled' THEN COALESCE(oi.void_qty,0) ELSE 0 END)                                 AS qty_void,
        SUM(CASE WHEN oi.status<>'cancelled' THEN GREATEST(oi.qty-COALESCE(oi.void_qty,0),0) ELSE 0 END)              AS qty_sold,
        SUM((GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0),0))*oi.price)::bigint AS net_revenue
      FROM public.order_items oi
      JOIN bounds b ON TRUE
      {join_sessions}
      WHERE TRUE
      {date_filter}
      {status_filter}
      GROUP BY oi.item_name
      ORDER BY net_revenue DESC NULLS LAST
      LIMIT {limit}
    """
    c.execute(sql, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()
    return jsonify({"items": rows})


@bp.get("/api/analytics/item_buckets")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_item_buckets():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    try:
        limit = int(request.args.get("limit", 50))
    except Exception:
        limit = 50

    attr = (request.args.get("attr") or "pay").lower()
    if attr == "print":
        attr = "printed"
    if attr not in ("pay", "close", "order", "printed"):
        attr = "pay"

    try:
        from datetime import date
        days_count = (date.fromisoformat(to) - date.fromisoformat(fr)).days + 1
        if days_count < 1:
            days_count = 1
    except Exception:
        days_count = 1

    lookup = _menu_bucket_lookup()

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    status_filter = ""
    if attr == "pay":
        session_cte = """
          , last_paid AS (
              SELECT p.session_id, MAX(p.paid_at) AS last_paid_at
              FROM public.payments p
              WHERE COALESCE(p.is_refund,false)=false
                AND COALESCE(p.is_dp,false)=false
              GROUP BY p.session_id
            )
          , sessions_in_range AS (
              SELECT lp.session_id AS id
              FROM last_paid lp, bounds b
              WHERE lp.last_paid_at >= b.start_utc AND lp.last_paid_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "close":
        session_cte = """
          , sessions_in_range AS (
              SELECT s.id
              FROM public.sessions s, bounds b
              WHERE s.status IN ('closed','cancelled')
                AND s.closed_at >= b.start_utc AND s.closed_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "order":
        session_cte = """
          , closed_sessions AS (SELECT id FROM public.sessions WHERE status IN ('closed','cancelled'))
          , paid_sessions   AS (
              SELECT DISTINCT session_id AS id
              FROM public.payments
              WHERE COALESCE(is_refund,false)=false
                AND COALESCE(is_dp,false)=false
            )
          , good_sessions   AS (SELECT id FROM closed_sessions UNION SELECT id FROM paid_sessions)
        """
        join_sessions = "JOIN good_sessions gs ON gs.id = oi.session_id"
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
    else:  # "printed"
        session_cte = ""
        join_sessions = ""
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
        status_filter = "AND COALESCE(oi.status,'') IN ('printed','served','paid','cancelled')"

    sql = f"""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      {session_cte}
      SELECT
        oi.item_name,
        SUM(CASE WHEN oi.status='cancelled' THEN oi.qty ELSE 0 END) AS qty_cancelled,
        SUM(CASE WHEN oi.status<>'cancelled' THEN COALESCE(oi.void_qty,0) ELSE 0 END) AS qty_void,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0)) AS qty_sold,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0) * oi.price)::bigint AS revenue
      FROM public.order_items oi
      JOIN bounds b ON TRUE
      {join_sessions}
      WHERE TRUE
      {date_filter}
      {status_filter}
      GROUP BY oi.item_name
    """
    c.execute(sql, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()

    buckets = {}
    for r in rows:
        qty = float(r.get("qty_sold") or 0)
        qty_void = float(r.get("qty_void") or 0)
        qty_cancelled = float(r.get("qty_cancelled") or 0)
        revenue = int(r.get("revenue") or 0)
        bucket_label, unit, category, subcategory = _resolve_bucket(r.get("item_name"), lookup)
        key = (bucket_label or "").strip().casefold() or (r.get("item_name") or "").strip().casefold()

        if key not in buckets:
            buckets[key] = {
                "bucket": bucket_label,
                "unit": unit,
                "category": category,
                "subcategory": subcategory,
                "qty_sold": 0.0,
                "qty_void": 0.0,
                "qty_cancelled": 0.0,
                "revenue": 0,
            }

        buckets[key]["qty_sold"] += qty
        buckets[key]["qty_void"] += qty_void
        buckets[key]["qty_cancelled"] += qty_cancelled
        buckets[key]["revenue"] += revenue
        if not buckets[key].get("unit"):
            buckets[key]["unit"] = unit

    result = []
    for b in buckets.values():
        avg_per_day = (b["qty_sold"] / days_count) if days_count else 0
        result.append({
            "bucket": b.get("bucket"),
            "category": b.get("category"),
            "subcategory": b.get("subcategory"),
            "unit": b.get("unit"),
            "qty_sold": b.get("qty_sold", 0.0),
            "qty_void": b.get("qty_void", 0.0),
            "qty_cancelled": b.get("qty_cancelled", 0.0),
            "avg_per_day": avg_per_day,
            "revenue": int(b.get("revenue") or 0),
        })

    result.sort(key=lambda x: (x["qty_sold"], x["revenue"]), reverse=True)
    if limit > 0:
        result = result[:limit]

    return jsonify({"buckets": result, "days": days_count})


@bp.get("/api/analytics/items_rollup")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_items_rollup():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    level = (request.args.get("level") or "category").strip().lower()
    if level not in ("category", "subcategory", "dish"):
        level = "category"

    category_filter = (request.args.get("category") or "").strip()
    subcategory_filter = (request.args.get("subcategory") or "").strip()

    attr = (request.args.get("attr") or "pay").lower()
    if attr == "print":
        attr = "printed"
    if attr not in ("pay", "close", "order", "printed"):
        attr = "pay"

    try:
        limit = int(request.args.get("limit", 200))
    except Exception:
        limit = 200

    try:
        from datetime import date
        days_count = (date.fromisoformat(to) - date.fromisoformat(fr)).days + 1
        if days_count < 1:
            days_count = 1
    except Exception:
        days_count = 1

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    status_filter = ""
    if attr == "pay":
        session_cte = """
          , last_paid AS (
              SELECT p.session_id, MAX(p.paid_at) AS last_paid_at
              FROM public.payments p
              WHERE COALESCE(p.is_refund,false)=false
                AND COALESCE(p.is_dp,false)=false
              GROUP BY p.session_id
            )
          , sessions_in_range AS (
              SELECT lp.session_id AS id
              FROM last_paid lp, bounds b
              WHERE lp.last_paid_at >= b.start_utc AND lp.last_paid_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "close":
        session_cte = """
          , sessions_in_range AS (
              SELECT s.id
              FROM public.sessions s, bounds b
              WHERE s.status IN ('closed','cancelled')
                AND s.closed_at >= b.start_utc AND s.closed_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "order":
        session_cte = """
          , closed_sessions AS (SELECT id FROM public.sessions WHERE status IN ('closed','cancelled'))
          , paid_sessions   AS (
              SELECT DISTINCT session_id AS id
              FROM public.payments
              WHERE COALESCE(is_refund,false)=false
                AND COALESCE(is_dp,false)=false
            )
          , good_sessions   AS (SELECT id FROM closed_sessions UNION SELECT id FROM paid_sessions)
        """
        join_sessions = "JOIN good_sessions gs ON gs.id = oi.session_id"
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
    else:  # "printed"
        session_cte = ""
        join_sessions = ""
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
        status_filter = "AND COALESCE(oi.status,'') IN ('printed','served','paid','cancelled')"

    sql = f"""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      {session_cte}
      SELECT
        oi.item_name,
        SUM(CASE WHEN oi.status='cancelled' THEN oi.qty ELSE 0 END) AS qty_cancelled,
        SUM(CASE WHEN oi.status<>'cancelled' THEN COALESCE(oi.void_qty,0) ELSE 0 END) AS qty_void,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0)) AS qty_sold,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0) * oi.price)::bigint AS revenue
      FROM public.order_items oi
      JOIN bounds b ON TRUE
      {join_sessions}
      WHERE TRUE
      {date_filter}
      {status_filter}
      GROUP BY oi.item_name
    """
    c.execute(sql, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()

    lookup = _menu_bucket_lookup()

    categories = {}
    subcategories = {}
    dishes = {}

    category_key = category_filter.strip().casefold()
    subcategory_key = subcategory_filter.strip().casefold()

    for r in rows:
        item_name = r.get("item_name") or ""
        qty_cancelled = float(r.get("qty_cancelled") or 0)
        qty_void = float(r.get("qty_void") or 0)
        qty_sold = float(r.get("qty_sold") or 0)
        revenue = int(r.get("revenue") or 0)

        _, unit, category, subcategory = _resolve_bucket(item_name, lookup)
        base, dish = split_item_and_dish(item_name)
        cat = category or "(Unknown)"
        sub = subcategory or (base or item_name or "(Unknown)")

        if level == "category":
            key = cat.casefold()
            entry = categories.setdefault(key, {
                "category": cat,
                "qty_sold": 0.0,
                "qty_void": 0.0,
                "qty_cancelled": 0.0,
                "revenue": 0,
                "_units": set(),
            })
            entry["qty_sold"] += qty_sold
            entry["qty_void"] += qty_void
            entry["qty_cancelled"] += qty_cancelled
            entry["revenue"] += revenue
            if unit:
                entry["_units"].add(unit)
            continue

        if category_key and cat.casefold() != category_key:
            continue

        if level == "subcategory":
            key = (cat.casefold(), sub.casefold())
            entry = subcategories.setdefault(key, {
                "category": cat,
                "subcategory": sub,
                "unit": unit,
                "qty_sold": 0.0,
                "qty_void": 0.0,
                "qty_cancelled": 0.0,
                "revenue": 0,
                "_dishes": set(),
            })
            entry["qty_sold"] += qty_sold
            entry["qty_void"] += qty_void
            entry["qty_cancelled"] += qty_cancelled
            entry["revenue"] += revenue
            if unit and not entry.get("unit"):
                entry["unit"] = unit
            if dish:
                entry["_dishes"].add(dish.strip().casefold())
            continue

        if level == "dish":
            if subcategory_key and sub.casefold() != subcategory_key:
                continue
            dish_label = dish.strip() if dish else (base or item_name or sub or "(Unknown)")
            key = (cat.casefold(), sub.casefold(), dish_label.casefold())
            entry = dishes.setdefault(key, {
                "category": cat,
                "subcategory": sub,
                "dish": dish_label,
                "unit": unit,
                "qty_sold": 0.0,
                "qty_void": 0.0,
                "qty_cancelled": 0.0,
                "revenue": 0,
            })
            entry["qty_sold"] += qty_sold
            entry["qty_void"] += qty_void
            entry["qty_cancelled"] += qty_cancelled
            entry["revenue"] += revenue
            if unit and not entry.get("unit"):
                entry["unit"] = unit

    if level == "category":
        result = []
        for c in categories.values():
            units = sorted(u for u in c.pop("_units") if u)
            if not units:
                unit_label = "-"
            elif len(units) == 1:
                unit_label = units[0]
            else:
                unit_label = "mix"
            result.append({
                "category": c.get("category"),
                "unit": unit_label,
                "qty_sold": c.get("qty_sold", 0.0),
                "qty_void": c.get("qty_void", 0.0),
                "qty_cancelled": c.get("qty_cancelled", 0.0),
                "revenue": int(c.get("revenue") or 0),
            })
        result.sort(key=lambda x: (x["revenue"], x["qty_sold"]), reverse=True)
        if limit > 0:
            result = result[:limit]
        return jsonify({"level": "category", "rows": result})

    if level == "subcategory":
        result = []
        for s in subcategories.values():
            dish_count = len(s.pop("_dishes") or [])
            result.append({
                "category": s.get("category"),
                "subcategory": s.get("subcategory"),
                "unit": s.get("unit") or "-",
                "qty_sold": s.get("qty_sold", 0.0),
                "qty_void": s.get("qty_void", 0.0),
                "qty_cancelled": s.get("qty_cancelled", 0.0),
                "revenue": int(s.get("revenue") or 0),
                "dish_count": dish_count,
            })
        result.sort(key=lambda x: (x["revenue"], x["qty_sold"]), reverse=True)
        if limit > 0:
            result = result[:limit]
        return jsonify({"level": "subcategory", "rows": result})

    result = []
    for d in dishes.values():
        avg_per_day = (d.get("qty_sold", 0.0) / days_count) if days_count else 0
        result.append({
            "category": d.get("category"),
            "subcategory": d.get("subcategory"),
            "dish": d.get("dish"),
            "unit": d.get("unit") or "-",
            "qty_sold": d.get("qty_sold", 0.0),
            "qty_void": d.get("qty_void", 0.0),
            "qty_cancelled": d.get("qty_cancelled", 0.0),
            "avg_per_day": avg_per_day,
            "revenue": int(d.get("revenue") or 0),
        })
    result.sort(key=lambda x: (x["revenue"], x["qty_sold"]), reverse=True)
    if limit > 0:
        result = result[:limit]
    return jsonify({"level": "dish", "rows": result, "days": days_count})


@bp.get("/api/analytics/modifiers")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_modifiers():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20
    if limit < 1:
        limit = 20
    if limit > 200:
        limit = 200

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT
        oi.note,
        oi.qty,
        oi.void_qty,
        oi.status
      FROM public.order_items oi, bounds b
      WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
        AND COALESCE(oi.note,'') <> ''
    """, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()

    counts: dict[str, dict] = {}
    used_preset_keys = set()

    for r in rows:
        note = r.get("note") or ""
        tokens = _split_modifier_tokens(note)
        if not tokens:
            continue

        try:
            qty_val = float(r.get("qty") or 0)
        except Exception:
            qty_val = 0.0
        try:
            void_val = float(r.get("void_qty") or 0)
        except Exception:
            void_val = 0.0

        status = (r.get("status") or "").lower()
        net_qty = 0.0 if status == "cancelled" else (qty_val - void_val)
        if net_qty <= 0:
            continue

        seen_keys = set()
        for tok in tokens:
            norm = _normalize_modifier_token(tok)
            if not norm or norm in seen_keys:
                continue
            seen_keys.add(norm)

            entry = counts.get(norm)
            if not entry:
                display = _PRESET_MODIFIER_DISPLAY.get(norm) or tok
                entry = {
                    "name": display,
                    "qty": 0.0,
                    "lines": 0,
                    "is_preset": norm in _PRESET_MODIFIER_DISPLAY,
                }
                counts[norm] = entry

            entry["qty"] += net_qty
            entry["lines"] += 1
            if norm in _PRESET_MODIFIER_DISPLAY:
                used_preset_keys.add(norm)

    def _sort_rows(rows_list: list[dict]) -> list[dict]:
        rows_list.sort(
            key=lambda x: (-float(x.get("qty") or 0), -int(x.get("lines") or 0), (x.get("name") or "").casefold())
        )
        if limit > 0:
            return rows_list[:limit]
        return rows_list

    preset_rows = _sort_rows([v for v in counts.values() if v.get("is_preset")])
    custom_rows = _sort_rows([v for v in counts.values() if not v.get("is_preset")])

    all_preset_keys = set(_PRESET_MODIFIER_DISPLAY.keys())
    unused_keys = sorted(
        all_preset_keys - used_preset_keys,
        key=lambda k: _PRESET_MODIFIER_DISPLAY.get(k, "").casefold(),
    )
    unused_presets = [_PRESET_MODIFIER_DISPLAY.get(k) or k for k in unused_keys]

    return jsonify({
        "preset": preset_rows,
        "custom": custom_rows,
        "unused_presets": unused_presets,
    })


@bp.get("/api/analytics/staff")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_staff():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # Cashiers (exclude refunds)
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT
        COALESCE(NULLIF(TRIM(u.full_name),''), u.username) AS name,
        COUNT(p.id)::int AS payments_cnt,
        SUM(COALESCE(p.amount,0))::bigint AS gross_handled   -- DP NOT added
      FROM payments p
      LEFT JOIN public.users u ON u.id = p.created_by_user_id,
      bounds b
      WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
        AND COALESCE(p.is_refund,false) = false
        AND COALESCE(p.is_dp,false)     = false
      GROUP BY name
      ORDER BY gross_handled DESC NULLS LAST
    """, (start_utc, end_utc))
    cashiers = c.fetchall()

    # Waiters (items added)
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT
        COALESCE(NULLIF(TRIM(u.full_name),''), u.username) AS name,
        COUNT(oi.id)::int AS items_added,
        SUM((GREATEST(oi.qty-COALESCE(oi.void_qty,0),0))*oi.price)::bigint AS items_value
      FROM order_items oi
      LEFT JOIN public.users u ON u.id = oi.created_by_user_id,
      bounds b
      WHERE oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc
        AND oi.status IN ('new','edited','served','printed','paid')
      GROUP BY name
      ORDER BY items_value DESC NULLS LAST
    """, (start_utc, end_utc))
    waiters = c.fetchall()

    conn.close()
    return jsonify({"cashiers": cashiers, "waiters": waiters})


@bp.get("/api/analytics/staff_voids")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_staff_voids():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)

    exclude_seafood = (request.args.get("exclude_seafood") or "") == "1"
    try:
        limit = int(request.args.get("limit", 50))
    except Exception:
        limit = 50

    user_id = None
    raw_uid = (request.args.get("user_id") or "").strip()
    if raw_uid:
        try:
            user_id = int(raw_uid)
        except Exception:
            user_id = None

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)
    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      SELECT
        COALESCE(oi.updated_by_user_id, oi.created_by_user_id) AS user_id,
        COALESCE(NULLIF(TRIM(u.full_name),''), u.username, '(Unknown)') AS name,
        oi.item_name,
        SUM(CASE WHEN oi.status='cancelled' THEN COALESCE(oi.qty,0) ELSE 0 END) AS qty_cancelled,
        SUM(CASE WHEN oi.status='cancelled' THEN COALESCE(oi.qty,0) * oi.price ELSE 0 END)::bigint AS value_cancelled,
        SUM(CASE WHEN oi.status<>'cancelled' THEN COALESCE(oi.void_qty,0) ELSE 0 END) AS qty_void,
        SUM(CASE WHEN oi.status<>'cancelled' THEN COALESCE(oi.void_qty,0) * oi.price ELSE 0 END)::bigint AS value_void,
        SUM(CASE WHEN oi.status='cancelled' THEN 1 ELSE 0 END)::int AS cancelled_lines,
        SUM(CASE WHEN oi.status<>'cancelled' AND COALESCE(oi.void_qty,0) > 0 THEN 1 ELSE 0 END)::int AS void_lines
      FROM public.order_items oi
      LEFT JOIN public.users u ON u.id = COALESCE(oi.updated_by_user_id, oi.created_by_user_id),
      bounds b
      WHERE COALESCE(oi.updated_at, oi."timestamp") >= b.start_utc
        AND COALESCE(oi.updated_at, oi."timestamp") < b.end_utc
        AND (COALESCE(oi.void_qty,0) > 0 OR oi.status = 'cancelled')
      GROUP BY user_id, name, oi.item_name
    """, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()

    lookup = _menu_bucket_lookup() if exclude_seafood else None

    if user_id is not None:
        items = {}
        staff_name = None
        for r in rows:
            rid = r.get("user_id")
            if rid != user_id:
                continue
            item_name = r.get("item_name") or ""
            if exclude_seafood:
                _, _, category, _ = _resolve_bucket(item_name, lookup)
                if _is_crab_or_fish(category, item_name):
                    continue
            staff_name = staff_name or r.get("name") or "(Unknown)"
            key = (item_name or "").strip().casefold() or "(unknown)"
            entry = items.setdefault(key, {
                "item_name": item_name or "(Unknown)",
                "qty_void": 0.0,
                "value_void": 0,
                "qty_cancelled": 0.0,
                "value_cancelled": 0,
                "void_lines": 0,
                "cancelled_lines": 0,
            })
            entry["qty_void"] += float(r.get("qty_void") or 0)
            entry["value_void"] += int(r.get("value_void") or 0)
            entry["qty_cancelled"] += float(r.get("qty_cancelled") or 0)
            entry["value_cancelled"] += int(r.get("value_cancelled") or 0)
            entry["void_lines"] += int(r.get("void_lines") or 0)
            entry["cancelled_lines"] += int(r.get("cancelled_lines") or 0)

        result = list(items.values())
        for it in result:
            it["total_value"] = int(it.get("value_void") or 0) + int(it.get("value_cancelled") or 0)
        result.sort(key=lambda x: (x["total_value"], x["qty_void"]), reverse=True)
        if limit > 0:
            result = result[:limit]
        return jsonify({"user_id": user_id, "name": staff_name, "items": result})

    staff = {}
    for r in rows:
        item_name = r.get("item_name") or ""
        if exclude_seafood:
            _, _, category, _ = _resolve_bucket(item_name, lookup)
            if _is_crab_or_fish(category, item_name):
                continue

        uid = r.get("user_id") or 0
        name = r.get("name") or "(Unknown)"
        entry = staff.setdefault(uid, {
            "user_id": uid,
            "name": name,
            "qty_void": 0.0,
            "value_void": 0,
            "qty_cancelled": 0.0,
            "value_cancelled": 0,
            "void_lines": 0,
            "cancelled_lines": 0,
        })
        entry["qty_void"] += float(r.get("qty_void") or 0)
        entry["value_void"] += int(r.get("value_void") or 0)
        entry["qty_cancelled"] += float(r.get("qty_cancelled") or 0)
        entry["value_cancelled"] += int(r.get("value_cancelled") or 0)
        entry["void_lines"] += int(r.get("void_lines") or 0)
        entry["cancelled_lines"] += int(r.get("cancelled_lines") or 0)

    result = list(staff.values())
    for it in result:
        it["total_value"] = int(it.get("value_void") or 0) + int(it.get("value_cancelled") or 0)
    result.sort(key=lambda x: (x["total_value"], x["qty_void"]), reverse=True)
    return jsonify({"staff": result})

@bp.get("/api/analytics/top_items")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_top_items():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20

    attr = (request.args.get("attr") or "pay").lower()
    if attr == "print":
        attr = "printed"
    if attr not in ("pay", "close", "order", "printed"):
        attr = "pay"

    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    status_filter = ""
    if attr == "pay":
        session_cte = """
          , last_paid AS (
              SELECT p.session_id, MAX(p.paid_at) AS last_paid_at
              FROM public.payments p
              WHERE COALESCE(p.is_refund,false)=false
                AND COALESCE(p.is_dp,false)=false
              GROUP BY p.session_id
            )
          , sessions_in_range AS (
              SELECT lp.session_id AS id
              FROM last_paid lp, bounds b
              WHERE lp.last_paid_at >= b.start_utc AND lp.last_paid_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "close":
        session_cte = """
          , sessions_in_range AS (
              SELECT s.id
              FROM public.sessions s, bounds b
              WHERE s.status IN ('closed','cancelled')
                AND s.closed_at >= b.start_utc AND s.closed_at < b.end_utc
            )
        """
        join_sessions = "JOIN sessions_in_range sir ON sir.id = oi.session_id"
        date_filter = ""

    elif attr == "order":
        session_cte = """
          , closed_sessions AS (SELECT id FROM public.sessions WHERE status IN ('closed','cancelled'))
          , paid_sessions   AS (
              SELECT DISTINCT session_id AS id
              FROM public.payments
              WHERE COALESCE(is_refund,false)=false
                AND COALESCE(is_dp,false)=false
            )
          , good_sessions   AS (SELECT id FROM closed_sessions UNION SELECT id FROM paid_sessions)
        """
        join_sessions = "JOIN good_sessions gs ON gs.id = oi.session_id"
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
    else:  # "printed"
        session_cte = ""
        join_sessions = ""
        date_filter = 'AND oi."timestamp" >= b.start_utc AND oi."timestamp" < b.end_utc'
        status_filter = "AND COALESCE(oi.status,'') IN ('printed','served','paid','cancelled')"

    sql = f"""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      )
      {session_cte}
      SELECT
        oi.item_name,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0)) AS qty,
        SUM(GREATEST(CASE WHEN oi.status<>'cancelled' THEN oi.qty ELSE 0 END - COALESCE(oi.void_qty,0), 0) * oi.price)::bigint AS revenue
      FROM public.order_items oi
      JOIN bounds b ON TRUE
      {join_sessions}
      WHERE oi.status <> 'cancelled'
      {date_filter}
      {status_filter}
      GROUP BY oi.item_name
      ORDER BY revenue DESC NULLS LAST
      LIMIT {limit}
    """
    c.execute(sql, (start_utc, end_utc))
    rows = c.fetchall()
    conn.close()
    return jsonify({"items": rows})


@bp.get("/api/analytics/outstanding")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_outstanding():
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    c.execute("""
      WITH open_s AS (
        SELECT id FROM public.sessions WHERE status = 'active'
      ),
      lines AS (
        SELECT
          oi.session_id,
          (GREATEST(oi.qty-COALESCE(oi.void_qty,0),0) * oi.price)::bigint AS line_net
        FROM public.order_items oi
        JOIN open_s s ON s.id = oi.session_id
        WHERE oi.status <> 'cancelled'
      )
      SELECT
        COALESCE(SUM(line_net),0)::bigint AS outstanding_pre_tax_service,
        (SELECT COUNT(*) FROM open_s)::int AS open_sessions
      FROM lines;
    """)
    row = c.fetchone() or {"outstanding_pre_tax_service": 0, "open_sessions": 0}
    conn.close()
    return jsonify(row)

@bp.get("/api/analytics/service_mix")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_service_mix():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    start_utc, end_utc = _utc_bounds(fr, to, tzname)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    c.execute("""
      WITH bounds AS (
        SELECT
          %s::timestamptz AS start_utc,
          %s::timestamptz AS end_utc
      ),
      closed_sessions AS ( SELECT id FROM public.sessions WHERE status IN ('closed','cancelled') ),
      paid_sessions AS (
        SELECT DISTINCT p.session_id
        FROM public.payments p, bounds b
        WHERE p.paid_at >= b.start_utc AND p.paid_at < b.end_utc
          AND COALESCE(p.is_refund,false)=false
          AND COALESCE(p.is_dp,false)=false
      ),
      good_sessions AS (
        SELECT id FROM closed_sessions
        UNION SELECT session_id AS id FROM paid_sessions
      ),
      joined AS (
        SELECT s.service_type,
               (GREATEST(oi.qty-COALESCE(oi.void_qty,0),0)*oi.price)::bigint AS net_value
        FROM public.order_items oi
        JOIN public.sessions s ON s.id = oi.session_id
        JOIN good_sessions gs  ON gs.id = oi.session_id
        WHERE oi.status <> 'cancelled'
      )
      SELECT service_type, SUM(net_value)::bigint AS revenue, COUNT(*)::int AS lines
      FROM joined
      GROUP BY service_type
      ORDER BY revenue DESC NULLS LAST;
    """, (start_utc, end_utc))

    rows = c.fetchall()
    conn.close()
    return jsonify({"service_mix": rows})

@bp.get("/api/analytics/reservations")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_reservations():
    fr, to = _date_range_from_request(request.args)
    fr_iso, to_iso, tzname = _tz_bounds(fr, to)
    conn = db.connect_db(None)
    c = conn.cursor(row_factory=dict_row)

    # By status (local date range)
    c.execute("""
      SELECT status, COUNT(*)::int AS cnt
      FROM reservations
      WHERE date >= %s::date AND date <= %s::date
      GROUP BY status
    """, (fr_iso, to_iso))
    by_status = c.fetchall()

    # No-show: confirmed, not seated (no session), past local datetime
    c.execute("""
      WITH now_local AS (SELECT now() AT TIME ZONE %s AS n)
      SELECT COUNT(*)::int AS noshow
      FROM reservations r, now_local nl
      WHERE r.status='confirmed'
        AND r.session_id IS NULL
        AND ((r.date::timestamp + r."time") AT TIME ZONE %s) < (nl.n AT TIME ZONE %s)
        AND r.date >= %s::date AND r.date <= %s::date
    """, (tzname, tzname, tzname, fr_iso, to_iso))
    noshow = (c.fetchone() or {"noshow": 0})["noshow"] or 0

    conn.close()
    return jsonify({"by_status": by_status, "no_show": noshow})

@bp.get("/admin/analytics")
@login_required
@roles_required("admin", "cashier", "viewer")
def analytics_page():
    return render_template("analytics.html", active_tab="analytics")
