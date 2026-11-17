import json, os, socket, re, glob
from dataclasses import dataclass
from typing import Dict, List, Optional

CONFIG_PATH = os.getenv("PRINTERS_JSON", "static/printers.json")

MOCK_PRINTING = (os.getenv("PRINT_BACKEND","").lower() == "mock") or (os.getenv("MOCK_PRINTING") == "1")

def _mock_on() -> bool:
    return (os.getenv("PRINT_BACKEND","").lower() == "mock") or (os.getenv("MOCK_PRINTING") == "1")

MOCK_DIR = os.getenv("PRINT_MOCK_DIR", "/tmp/pos_mock_prints")

# NEW: simple disk spool
SPOOL_DIR = os.getenv("PRINT_SPOOL_DIR", "/tmp/pos_print_spool")
os.makedirs(SPOOL_DIR, exist_ok=True)

def _spool_dir_for(pid: str) -> str:
    d = os.path.join(SPOOL_DIR, pid)
    os.makedirs(d, exist_ok=True)
    return d

def _is_bar_printer(printer_id: str) -> bool:
    # Treat ids like "bar", "bar-1f", "bar-2f" as bar printers
    return bool(re.search(r'\bbar\b', str(printer_id or ''), re.I))

def print_bar_grouped(printer_id: str, header: Dict, items: List[Dict]) -> str:
    """
    For bar printers: print all drinks for this table in a single slip.
    Non-drinks are ignored. If no drinks, skip.
    """
    drinks = [it for it in items if is_drink(it)]
    if not drinks:
        return "skip://no-drinks"
    return print_kitchen_raw(printer_id, header, drinks)

def _wrap_words(s: str, width: int) -> List[str]:
    """Simple word wrap that avoids breaking words."""
    s = str(s or "").strip()
    if not s or width <= 0:
        return [s] if s else []
    out, line = [], ""
    for w in s.split():
        cand = (w if not line else line + " " + w)
        if len(cand) <= width:
            line = cand
        else:
            if line:
                out.append(line)
            # if a single word is longer than width, hard-break it
            while len(w) > width:
                out.append(w[:width])
                w = w[width:]
            line = w
    if line:
        out.append(line)
    return out

def _fmt_qty_name_wrapped(it: Dict, width=32, indent="  ") -> str:
    """
    First line: 'QTY [UNIT] <part of name>' without breaking words.
    Next lines: indented, continue name (word-wrapped).
    """
    qty  = it.get("qty", 1)
    name = str(it.get("name") or "")
    unit = _unit_for_item(it)

    qtxt = f"{qty:g}" + (f" {unit}" if unit else "")
    left = f"{qtxt} "
    room = max(0, width - len(left))
    if room <= 0:
        # degenerate: put name on next wrapped lines
        wrapped = _wrap_words(name, max(1, width - len(indent)))
        return left.rstrip() + "\n" + "\n".join(indent + ln for ln in wrapped)

    # fill first line with as many words as fit
    words = name.split()
    first, rest = [], words
    tmp = ""
    for i, w in enumerate(words):
        cand = (w if not tmp else tmp + " " + w)
        if len(cand) <= room:
            tmp = cand
        else:
            first = [tmp] if tmp else []
            rest  = words[i:]
            break
    else:
        first = [tmp] if tmp else []
        rest  = []

    lines = []
    first_line = left + (first[0] if first else "")
    lines.append(first_line)

    if rest:
        wrapped_rest = _wrap_words(" ".join(rest), max(1, width - len(indent)))
        lines.extend(indent + ln for ln in wrapped_rest)

    return "\n".join(lines)

def _spool_enqueue(pid: str, payload: bytes) -> str:
    import time, uuid
    d = _spool_dir_for(pid)
    name = f"{int(time.time())}-{uuid.uuid4().hex}.bin"
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(payload)
    return p

def _spool_list(pid: str) -> List[str]:
    d = _spool_dir_for(pid)
    return sorted(glob.glob(os.path.join(d, "*.bin")))

def _spool_flush(pid: str, ip: str, port: int, timeout=4) -> int:
    """Try to flush queued jobs for this printer. Returns count flushed."""
    paths = _spool_list(pid)
    ok = 0
    for p in paths:
        try:
            with open(p, "rb") as f:
                data = f.read()
            # send; if it fails, stop flushing (printer still down)
            send_raw(ip, port, data, timeout=timeout)
            os.remove(p)
            ok += 1
        except Exception:
            break
    return ok

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

# All known drink/dessert names from your "Minuman" menu (lowercased)
_KNOWN_DRINK_NAMES = {
    "teh tawar",
    "soda",
    "es teh tawar",
    "teh manis",
    "es teh manis",
    "teh botol",
    "mineral water biasa",
    "mineral water dingin",
    "air putih hangat",
    "air putih biasa",
    "air putih es",
    "jeruk hangat",
    "jeruk murni",
    "es jeruk",
    "nipis hangat",
    "es jeruk nipis",
    "kelapa muda",
    "kelapa jeruk",
    "kelapa kopyor",
    "kelapa kopyor jeruk",
    "kelapa susu",
    "kopyor kerok",
    "es buah campur",
    "es cendol durian",
    "es cendol tanpa durian",
    "es kacang merah",
    "es lemon tea",
    "coca cola",
    "fanta",
    "sprite",
    "kopi",
    "kopi susu",
    "lychee tea es",
    "lemon squash",
    "lemon tea hangat",
    "orange juice",
    "orange juice spesial",
    "susu coklat es",
    "susu coklat hangat",
    "susu putih es",
    "susu putih hangat",
    "timun serut",
    "juice alpukat",
    "juice belimbing",
    "juice jambu",
    "juice mangga",
    "juice melon",
    "juice mix",
    "juice nanas",
    "juice pepaya",
    "juice semangka",
    "juice sirsak",
    "juice strawberry",
    "juice timun",
    "juice tomat",
    "jahe sereh hangat",
    "buah campur potong",
    "juice buah naga",
    "juice wortel",
    "es batu",
    "aqua 600ml",
    "aqua 330ml",
    "es teh manis pitcher",
    "es teh tawar pitcher",
    "teh tawar pitcher",
    "teh manis pitcher",
    "soda gembira",
    "fruit tea",
    "es durian",
    "salad buah",
    "jahe susu",
    "puding mangga",
    "puding strawberry",
    "puding melon",
    "puding coklat",
    "jus durian",
}

def _is_plain_rice(it: Dict) -> bool:
    """
    Detect plain 'Nasi Putih' items that should NOT go to masak station.
    They will still go to the expediter.
    """
    name = _norm(it.get("name"))
    if not name:
        return False
    # Covers 'nasi putih', 'nasi putih refill', etc.
    return name.startswith("nasi putih")


def is_drink(it: Dict) -> bool:
    cat = _norm(it.get("category") or it.get("cat"))
    name = _norm(it.get("name"))

    # 1) Category: anything under "Minuman" is definitely a drink
    if "minuman" in cat:
        return True

    # 2) Exact match against your known menu drink names
    if name in _KNOWN_DRINK_NAMES:
        return True

    # 3) Fallback by keywords for future/new drinks
    drink_kw = (
        "teh", "kopi", "latte", "americano", "espresso", "cappuccino", "capuccino",
        "matcha", "thai tea", "milk", "susu", "coklat", "cokelat", "milo",
        "chocolate", "es ", "es-", "jus", "juice", "sirup", "lemon",
        "jahe", "bandrek", "wedang", "soda", "sparkling", "mocktail", "cocktail",
        "beer", "bir", "wine", "spritzer", "aqua", "air", "mineral",
        "cola", "fanta", "sprite", "lychee", "pitcher", "kelapa",
        "fruit tea", "cendol", "kacang", "timun", "durian", "puding",
        "salad", "squash"
    )
    return any(k in name for k in drink_kw)



@dataclass
class NetPrinter:
    id: str
    ip: str
    port: int

def _load_printers() -> Dict[str, NetPrinter]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    out: Dict[str, NetPrinter] = {}
    for p in cfg.get("printers", []):
        pid = p["id"]
        out[pid] = NetPrinter(id=pid, ip=p["ip"], port=int(p.get("port", 9100)))
    return out
    
def _safe_send_with_spool(printer_id: str, ip: str, port: int, payload: bytes, timeout=4) -> str:
    # try flush older jobs first
    _spool_flush(printer_id, ip, port, timeout=timeout)
    # now try this job
    try:
        send_raw(ip, port, payload, timeout=timeout)
        return f"raw://{ip}:{port}"
    except Exception:
        _spool_enqueue(printer_id, payload)
        return f"spooled://{printer_id}"

def _mock_dump(printer_id: str, payload: bytes) -> str:
    try:
        os.makedirs(MOCK_DIR, exist_ok=True)
        ts = __import__("time").strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(MOCK_DIR, f"{ts}-raw-{printer_id}.bin"), "wb") as f:
            f.write(payload)
        return f"mock://raw/{printer_id}/{ts}"
    except Exception:
        return f"mock://raw/{printer_id}"

# --- minimal ESC/POS ---
ESC = b"\x1b"
GS  = b"\x1d"

# Common Epson-compatible code pages (ESC t n)
_CODEPAGES = {
    "cp437": 0,    # USA, default safe
    "cp850": 2,    # Latin-1-ish
    "cp852": 18,   # Central/Eastern Europe
    "cp858": 19,   # 850 + Euro
    "cp1252": 16,  # Windows Latin-1 (good default for ID/EN)
}

def _codepage(name: str = "cp1252") -> bytes:
    n = _CODEPAGES.get(name.lower(), 16)
    return ESC + b"t" + bytes([n])

def _font_A() -> bytes:
    # Font A is wider/taller (more legible) than Font B on many printers
    return ESC + b"M" + b"\x00"   # 0=Font A, 1=Font B

def _sanitize(s: str) -> str:
    # Normalize a few problematic glyphs that often show up on copy/paste
    return (
        str(s or "")
        .replace("\u2013", "-")   # en dash
        .replace("\u2014", "-")   # em dash
        .replace("\u2212", "-")   # minus sign
        .replace("\xa0", " ")     # non-breaking space
    )

def _unit_for_item(it: Dict) -> str:
    """
    Use explicit unit if provided; otherwise, infer "ons" for fish/kepiting categories.
    """
    unit = str(it.get("unit") or "").strip()
    if unit:
        return unit

    cat = str(it.get("category") or it.get("cat") or "").lower()
    name = str(it.get("name") or "").lower()
    text = f"{cat} {name}"

    # Only fish / kepiting as requested
    if ("gurame" in text) or ("baronang" in text) or ("bawal" in text) or ("kuwe" in text) or ("kakap" in text) or ("krapu" in text) or ("kepiting telor" in text) or ("kepiting jantan" in text):
        return "ons"

    return ""

def _fmt_qty_name_with_unit(it: Dict, width=32) -> str:
    qty  = it.get("qty", 1)
    name = str(it.get("name") or "")
    unit = _unit_for_item(it)

    qtxt = f"{qty:g}" + (f" {unit}" if unit else "")
    left = f"{qtxt} "
    room = max(0, width - len(left))

    if len(name) <= room:
        return left + name
    # wrap the name onto the next line under the quantity
    return left + name[:room] + "\n" + " " * len(left) + name[room:]


def _init() -> bytes:
    # Initialize + pick font + pick code page BEFORE any text
    return ESC + b"@" + _font_A() + _codepage("cp1252")

def _text(s: str) -> bytes:
    # Encode in the same codepage we selected (cp1252 here).
    # Avoid UTF-8: many thermal printers don't expect it unless explicitly set.
    return _sanitize(s).encode("cp1252", "replace")

def _align(n: int) -> bytes:            # 0=left,1=center,2=right
    return ESC + b"a" + bytes([n])

def _bold(on: bool) -> bytes:
    return ESC + b"E" + (b"\x01" if on else b"\x00")

# --- sizing & fonts ---
def _scale(wmul: int = 1, hmul: int = 1) -> bytes:
    # ESC/POS supports 1..8 integer multiples per axis
    w = max(1, min(8, int(wmul)))
    h = max(1, min(8, int(hmul)))
    return GS + b"!" + bytes([ (w - 1) | ((h - 1) << 4) ])

def _font(which: str = "A") -> bytes:
    # A = larger/wider; B = narrower (more cols)
    return ESC + b"M" + (b"\x00" if str(which).upper() == "A" else b"\x01")

def _double_h(dw: bool, dh: bool) -> bytes:
    # character scaling: width bit0, height bit4
    sz = (1 if dw else 0) | ((1 if dh else 0) << 4)
    return GS + b"!" + bytes([sz])

def _cut() -> bytes:
    return GS + b"V" + b"\x00"

def _lf(n: int = 1) -> bytes:
    return b"\n" * max(1, n)

def _split_notes(note: str) -> list[str]:
    s = str(note or "").strip()
    if not s:
        return []
    # split on our joiner " | " and common separators/newlines
    parts = re.split(r"[|;\n]+", s)
    # keep non-empty trimmed lines
    return [p.strip() for p in parts if p and p.strip()]


def _hr(width=32, ch="-") -> bytes:
    return _text(ch * width) + _lf()

def _fmt_qty_name(qty, name, width=32) -> str:
    q = f"{qty:g}"
    left = f"{q} "
    room = max(0, width - len(left))
    name = str(name or "")
    if len(name) <= room:
        return left + name
    return left + name[:room] + "\n" + " " * len(left) + name[room:]

def build_kitchen_ticket(header: Dict, items: List[Dict], width=32) -> bytes:
    title = str(header.get("title") or "KITCHEN")
    table = str(header.get("table_number") or "")
    when  = str(header.get("printed_at") or "")
    split_label = str(header.get("split_label") or "").strip()
    res_time = str(header.get("reservation_time") or "").strip()

    buf = bytearray()
    buf += _init()

    # ===== Title (center, big & bold) =====
    buf += _align(1) + _bold(True) + _double_h(True, True)
    buf += _text(title) + _lf()
    buf += _bold(False) + _double_h(False, False)

    # ===== Reservation line (big) =====
    if header.get("is_reservation"):
        buf += _align(1) + _bold(True) + _double_h(True, True)
        label = "RESERVASI" + (f" ({res_time})" if res_time else "")
        buf += _text(label) + _lf()
        buf += _bold(False) + _double_h(False, False)
        buf += _lf()

    # ===== Table number + split label (extra emphasis) =====
    if table or split_label:
        if table:
            if table.strip().upper() == "TA":
                table = "Take Away"  # Rename "MEJA TA" to just "TA"
        buf += _align(1) + _bold(True) + _double_h(True, True)
        if table:
            buf += _text(f"MEJA {table}") + _lf()
        if split_label:
            buf += _text(f"SPLIT: {split_label}") + _lf()
        buf += _lf()  # extra spacing after the block
        buf += _align(0) + _bold(False) + _double_h(False, False)

    # When (BIGGER than before)
    if when:
        buf += _bold(True) + _scale(2, 2)
        buf += _text(when) + _lf()
        buf += _scale(1, 1) + _bold(False)

    guest = str(header.get("guest_name") or "").strip()
    try:
        pax = int(header.get("pax") or 1)
    except Exception:
        pax = 1
    sender = str(header.get("prepared_by") or "").strip()

    if guest:
        buf += _bold(True) + _scale(2, 2)  # Make guest name slightly bigger
        buf += _text(f"TAMU: {guest}") + _lf()
        buf += _scale(1, 1) + _bold(False)
    buf += _text(f"PAX: {pax}") + _lf()
    if sender:
        buf += _font("A") + _scale(1, 1) + _bold(False)
        buf += _text(f"Dikirim oleh: {sender}") + _lf()

    # Global table note lines
    tnl = header.get("table_note_lines") or []
    if tnl:
        note_width = max(10, width // 2)
        buf += _bold(True) + _scale(3, 3)  # big
        for nl in tnl:
            for ln in _wrap_words(nl, note_width):
                buf += _text(ln) + _lf()
            buf += _lf()  # a little space between notes
        buf += _scale(1, 1) + _bold(False)


    buf += _hr(width)

    # ===== Items (slightly smaller than before) =====
    # Previously _scale(2,4); drop to (2,3) ~ "2 px smaller" feel
    # Use a reduced working width when scaled wide (~half the cols)
    item_width = max(10, width // 2)

    for it in items:
        note = it.get("note", "")

        # qty+name large (but a bit smaller than before)
        buf += _bold(True) + _font("B") + _scale(2, 3)
        buf += _text(_fmt_qty_name_wrapped(it, item_width)) + _lf()
        buf += _bold(False) + _font("A") + _scale(1, 1)

        notes_list = _split_notes(note)
        if notes_list:
            buf += _lf()  # Add spacing between notes and item name
            buf += _font("A") + _scale(1, 2)
            for nl in notes_list:
                buf += _text(f"  - {nl}") + _lf()
                buf += _lf()  # Add spacing between notes
            buf += _scale(1, 1) + _font("A")

        # extra space between items
        buf += _lf()

    buf += _hr(width)
    buf += _lf(3)
    buf += _cut()
    return bytes(buf)


def send_raw(ip: str, port: int, payload: bytes, timeout=4):
    with socket.create_connection((ip, port), timeout=timeout) as s:
        s.sendall(payload)

def print_kitchen_raw(printer_id: str, header: Dict, items: List[Dict]) -> str:
    """
    Generic kitchen ticket.

    Special rule:
    - For MASAK station printers (id contains 'masak'), we never print plain 'Nasi Putih'.
      Nasi Putih is handled by expediter only.
    """
    pid_lower = str(printer_id or "").lower()
    if "masak" in pid_lower:
        filtered = [it for it in items if not _is_plain_rice(it)]
        if not filtered:
            return "skip://plain-rice-only"
        items = filtered

    payload = build_kitchen_ticket(header, items)

    if _mock_on():
        return _mock_dump(printer_id, payload)

    printers = _load_printers()
    tgt = printers.get(printer_id)
    if not tgt:
        raise RuntimeError(f"Unknown printer id '{printer_id}' (check static/printers.json)")
    return _safe_send_with_spool(printer_id, tgt.ip, tgt.port, payload)


def print_expediter_raw(printer_id: str, header: Dict, items: List[Dict]) -> str:
    """
    Expediter gets only non-drinks. If all items are drinks, skip quietly.
    """
    non_drinks = [it for it in items if not is_drink(it)]
    if not non_drinks:
        return "skip://drinks-only"
    return print_kitchen_raw(printer_id, header, non_drinks)

def print_station_per_item(printer_id: str, header: Dict, items: List[Dict]) -> List[str]:
    """
    For special stations (e.g., bakaran), print one item per slip.
    Returns list of targets for logging.

    NOTE: 'Nasi Putih' is never printed here; it only goes to expediter.
    """
    # Remove plain rice from station printers; expediter will handle it.
    items = [it for it in items if not _is_plain_rice(it)]
    if not items:
        return []

    if _mock_on():
        out = []
        for it in items:
            payload = build_kitchen_ticket(header, [it])
            out.append(_mock_dump(printer_id, payload))
        return out

    printers = _load_printers()
    tgt = printers.get(printer_id)
    if not tgt:
        raise RuntimeError(f"Unknown printer id '{printer_id}' (check static/printers.json)")

    out = []
    for it in items:
        payload = build_kitchen_ticket(header, [it])
        out.append(_safe_send_with_spool(printer_id, tgt.ip, tgt.port, payload))
    return out
