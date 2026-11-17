import os, json, socket, subprocess, re, shutil
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple

# import your rules
from printing.routing_rules import infer_route_tag
from .helpers import printer_override_for_label

CONFIG_PATH = os.getenv("PRINTERS_JSON", "static/printers.json")
IS_MOCK = (os.getenv("PRINT_BACKEND","").lower() == "mock") or (os.getenv("MOCK_PRINTING") == "1")
MOCK_DIR = os.getenv("PRINT_MOCK_DIR", "/tmp/pos_mock_prints")

def _lp_binary():
    """
    Resolve `lp` up front so we can surface a clearer error instead of FileNotFoundError.
    """
    override = os.getenv("LP_BIN") or os.getenv("CUPS_LP_BIN")
    if override and os.path.exists(override):
        return override

    lp = shutil.which("lp")
    if lp:
        return lp

    for p in ("/usr/bin/lp", "/usr/sbin/lp", "/bin/lp"):
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p

    raise RuntimeError("CUPS 'lp' command not found. Install cups-client or set PRINT_BACKEND=mock for testing.")

def _mock_save(printer_id: str, payload: bytes) -> str:
    import time, os
    try:
        os.makedirs(MOCK_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join(MOCK_DIR, f"{ts}-router-{printer_id}.bin")
        with open(path, "wb") as f:
            f.write(payload)
        return f"mock://router/{printer_id}/{ts}"
    except Exception:
        return f"mock://router/{printer_id}"


@dataclass
class Printer:
    id: str
    ip: str
    port: int
    tags: List[str]
    floors: List[str]
    name: str | None = None

def load_config(path=CONFIG_PATH) -> Tuple[Dict, List[Printer], Dict[str, Printer]]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    printers = []
    idx = {}
    for p in cfg.get("printers", []):
        pr = Printer(
            id=p["id"],
            ip=p["ip"],
            port=int(p.get("port", 9100)),
            tags=list(p.get("tags", [])),
            floors=list(p.get("floors", [])),
            name=p.get("name"),
        )
        printers.append(pr)
        idx[pr.id] = pr
    return cfg, printers, idx

def table_to_floor(table: str|int, cfg: Dict) -> str|None:
    """
    Decide '1' or '2' (or whatever your config says) based on number ranges/prefixes.
    """
    if table is None:
        return None

    s = str(table).strip()
    # by_prefix first (if you ever use it)
    for row in cfg.get("table_floor_rules", {}).get("by_prefix", []):
        pref = str(row.get("prefix",""))
        if s.startswith(pref):
            return str(row.get("floor"))

    # by_range (your current config)
    if re.fullmatch(r"\d+", s):
        n = int(s)
        for row in cfg.get("table_floor_rules", {}).get("by_range", []):
            if int(row["min"]) <= n <= int(row["max"]):
                return str(row["floor"])

    return None

def find_printers_for(tag: str, floor: str|None, printers: List[Printer]) -> List[Printer]:
    """
    Return printers that can handle a given tag, filtered by floor if provided.
    Example: tag='bar', floor='2' --> bar-2f only.
    """
    cands = [p for p in printers if tag in p.tags]
    if floor:
        fl = [p for p in cands if (not p.floors or floor in p.floors)]
        if fl:
            return fl
    return cands

def fallback_printer(cfg: Dict, idx: Dict[str, Printer]) -> Printer|None:
    fid = cfg.get("fallback_printer_id")
    return idx.get(fid) if fid else None

def build_escpos_ticket(order: Dict, items: List[Dict], header: str) -> bytes:
    """
    Minimal ESC/POS payload. Replace with your real template if you have one.
    """
    lines = []
    lines.append(header)
    lines.append(f"Order: {order.get('order_no','')}")
    table = order.get("table")
    if table:
        lines.append(f"Meja: {table}")
    lines.append("------------------------------")
    for it in items:
        nm  = it.get("name","")
        qty = it.get("qty",1)
        lines.append(f"{qty} x {nm}")
    lines.append("------------------------------")
    lines.append("\n\n")
    # VERY basic: printable ASCII + newlines; your real template can use ESC/POS cmds
    return ("\n".join(lines)).encode("utf-8", errors="replace")

def send_raw(ip: str, port: int, payload: bytes, timeout=4):
    with socket.create_connection((ip, port), timeout=timeout) as s:
        s.sendall(payload)

def send_via_cups(queue_name: str, payload: bytes):
    # pipe raw bytes to `lp -d <queue>`
    lp = _lp_binary()
    p = subprocess.Popen([lp, "-d", queue_name], stdin=subprocess.PIPE)
    p.stdin.write(payload)
    p.stdin.close()
    rc = p.wait()
    if rc != 0:
        raise RuntimeError(f"lp to {queue_name} failed with code {rc}")

def _parse_cups_printers_env() -> Dict[str, str]:
    """
    Parse CUPS_PRINTERS env:
      kitchen=EPSON_Kitchen,veg=EPSON_Veg,... -> {"kitchen":"EPSON_Kitchen", ...}
    """
    raw = os.getenv("CUPS_PRINTERS","")
    out = {}
    for part in raw.split(","):
        if "=" in part:
            k,v = part.split("=",1)
            out[k.strip()] = v.strip()
    return out

def _is_res_or_ta(table) -> bool:
    s = str(table or "").strip().upper()
    return s.startswith("RES") or s.startswith("TA")


def route_and_print(order: Dict, cfg_path=CONFIG_PATH) -> Dict[str, Any]:
    """
    order: {
      "order_no": "...",
      "table": "215",      # string or int
      "items": [
         {"name":"Teh Manis", "qty":1, "category_path":["Minuman"]},
         ...
      ]
    }
    Returns: { "<printer-id>": {"ok": True, "target": "..."} | {"ok": False, "error": "..."} }
    """
    cfg, printers, idx = load_config(cfg_path)
    floor = table_to_floor(order.get("table"), cfg)

    # Build per-printer id -> item list
    per_printer: Dict[str, List[Dict]] = {}

    for it in order.get("items", []):
        name = it.get("name","")
        cats = it.get("category_path") or []
        override = (printer_override_for_label(name) or "").strip().lower()
        target = idx.get(override) if override else None
        tag  = (override or None) or infer_route_tag(name, cats) or "dapur"

        if target:
            cand = [target]
        elif tag == "bar":
            # If it's a reservation/TA pseudo-table, force drinks to floor "1"
            drink_floor = "1" if _is_res_or_ta(order.get("table")) else floor
            cand = find_printers_for(tag, drink_floor, printers)
        else:
            cand = find_printers_for(tag, None, printers)

        target = cand[0] if cand else fallback_printer(cfg, idx)
        if not target:
            # skip silently or collect error — here we fallback to skipping
            continue

        per_printer.setdefault(target.id, []).append(it)

    use_cups = (os.getenv("PRINT_BACKEND","").lower() == "cups")
    cups_map = _parse_cups_printers_env()

    results: Dict[str, Any] = {}
    for pid, items in per_printer.items():
        p = idx[pid]
        payload = build_escpos_ticket(order, items, header=f"*** {pid.upper()} ***")
        try:
            if IS_MOCK:
                job = _mock_save(pid, payload)
                results[pid] = {"ok": True, "target": job, "mocked": True}
            else:
                if use_cups:
                    # pid must exist as a key in CUPS_PRINTERS
                    q = cups_map.get(pid)
                    if not q:
                        raise RuntimeError(f"No CUPS queue mapped for '{pid}' (check CUPS_PRINTERS)")
                    send_via_cups(q, payload)
                    results[pid] = {"ok": True, "target": q}
                else:
                    send_raw(p.ip, p.port, payload)
                    results[pid] = {"ok": True, "target": f"{p.ip}:{p.port}"}
        except Exception as e:
            results[pid] = {"ok": False, "error": str(e)}
    return results
