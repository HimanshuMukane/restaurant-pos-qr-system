from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Jakarta")
except Exception:
    TZ = None

def qtyfmt(q):
    try: d = Decimal(str(q))
    except Exception: return q
    return f"{int(d)}" if d == d.to_integral() else f"{d:.1f}"

def idr(n):
    try: x = int(round(n or 0))
    except Exception: x = 0
    return f"Rp\u00A0{x:,}"

def idr_plain(n):
    try: x = int(round(n or 0))
    except Exception: x = 0
    return f"{x:,}"

def fmt_dt(value, fmt="%d-%m-%y %H:%M"):
    if value is None: return "-"
    if isinstance(value, datetime): dt = value
    else:
        try: dt = datetime.fromisoformat(str(value))
        except Exception: return str(value)
    return dt.strftime(fmt)

def register_filters(app):
    app.add_template_filter(qtyfmt, "qtyfmt")
    app.add_template_filter(idr, "idr")
    app.add_template_filter(idr_plain, "idr_plain")
    app.add_template_filter(fmt_dt, "fmt_dt")
