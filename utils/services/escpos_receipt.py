from ..config_store import get_billing_config, get_escpos_config, get_receipt_config

DEFAULT_STORE_HEADER_LINES = [
    "DEMO RESTAURANT",
    "123 Demo Street",
    "City, 12345",
]
DEFAULT_FOOTER_NOTE = "Thank you for dining with us!"

def get_receipt_cols() -> int:
    cfg = get_escpos_config()
    return int(cfg.get("receipt_cols") or 48)


def get_feed_lines() -> int:
    cfg = get_escpos_config()
    return int(cfg.get("feed_lines") or 6)


def get_right_guard() -> int:
    cfg = get_escpos_config()
    return int(cfg.get("right_guard") or 0)


def get_header_lines() -> list[str]:
    cfg = get_receipt_config()
    lines = cfg.get("header_lines") if isinstance(cfg, dict) else None
    if isinstance(lines, list) and any(str(x).strip() for x in lines):
        return [str(x).strip() for x in lines if str(x).strip()]
    return list(DEFAULT_STORE_HEADER_LINES)


def get_footer_note() -> str:
    cfg = get_receipt_config()
    note = cfg.get("footer_note") if isinstance(cfg, dict) else None
    if isinstance(note, str) and note.strip():
        return note.strip()
    return DEFAULT_FOOTER_NOTE


DEFAULT_WIDTH = get_receipt_cols()

ESC = b"\x1b"
GS = b"\x1d"
FONT_A_DOTS = 12


def _init() -> bytes:
    return ESC + b"@"


def _align(n: int) -> bytes:
    return ESC + b"a" + bytes([n])


def _bold(on: bool) -> bytes:
    return ESC + b"E" + (b"\x01" if on else b"\x00")


def _font(which: str = "B") -> bytes:
    return ESC + b"M" + (b"\x00" if str(which).upper() == "A" else b"\x01")


def _scale(wmul: int = 1, hmul: int = 1) -> bytes:
    w = max(1, min(8, int(wmul)))
    h = max(1, min(8, int(hmul)))
    return GS + b"!" + bytes([(w - 1) | ((h - 1) << 4)])


def _double_height(on: bool) -> bytes:
    return ESC + b"!" + (b"\x10" if on else b"\x00")


def format_idr(value: int) -> str:
    try:
        n = int(round(value or 0))
    except Exception:
        n = 0
    return "Rp " + f"{n:,}"


def format_idr_plain(value: int) -> str:
    try:
        n = int(round(value or 0))
    except Exception:
        n = 0
    return f"{n:,}"


def _wrap_words(text: str, width: int) -> list[str]:
    text = str(text or "").strip()
    if not text or width <= 0:
        return [text] if text else []
    out = []
    line = ""
    for word in text.split():
        candidate = word if not line else f"{line} {word}"
        if len(candidate) <= width:
            line = candidate
        else:
            if line:
                out.append(line)
            while len(word) > width:
                out.append(word[:width])
                word = word[width:]
            line = word
    if line:
        out.append(line)
    return out


def _line_lr(left: str, right: str, width: int) -> str:
    left = str(left or "")
    right = str(right or "")
    if not right:
        return left[:width]
    space = max(1, width - len(left) - len(right))
    if space <= 0:
        return (left[: max(0, width - len(right) - 1)] + " " + right)[-width:]
    return f"{left}{' ' * space}{right}"


def _abs_pos(pos: int) -> bytes:
    pos = max(0, min(65535, int(pos)))
    return ESC + b"$" + bytes([pos & 0xFF, (pos >> 8) & 0xFF])


def _line_lr_abs(left: str, right: str, width: int, *, char_width: int = FONT_A_DOTS, wmul: int = 1) -> bytes:
    left = str(left or "")
    right = str(right or "")
    if not right:
        return (left[:width] + "\n").encode("utf-8", "replace")
    pos_cols = max(0, width - len(right))
    if pos_cols <= len(left):
        return (_line_lr(left, right, width) + "\n").encode("utf-8", "replace")
    pos = pos_cols * max(1, char_width) * max(1, wmul)
    buf = bytearray()
    buf.extend(left.encode("utf-8", "replace"))
    buf.extend(_abs_pos(pos))
    buf.extend(right.encode("utf-8", "replace"))
    buf.extend(b"\n")
    return bytes(buf)


def _center(text: str, width: int) -> str:
    text = str(text or "")
    if not text or width <= 0:
        return text
    if len(text) >= width:
        return text[:width]
    pad = (width - len(text)) // 2
    return (" " * pad) + text


def _format_item_lines(item: dict, width: int) -> list[str]:
    qty = item.get("qty", 1)
    name = str(item.get("name") or "")
    total = format_idr_plain(item.get("line_total", 0))
    unit = str(item.get("unit") or "").strip()
    prefix = f"{qty:g} {unit} " if unit else f"{qty:g} "
    avail = width - len(total) - 1 - len(prefix)
    if avail <= 0:
        lines = _wrap_words(prefix + name, width)
        lines.append(_line_lr("", total, width))
        return lines
    name_lines = _wrap_words(name, avail) or [""]
    lines = [_line_lr(prefix + name_lines[0], total, width)]
    for extra in name_lines[1:]:
        lines.append((" " * len(prefix)) + extra)
    return lines


def build_receipt_bytes(
    header: dict,
    items: list[dict],
    totals: dict,
    *,
    title: str | None = None,
    width: int | None = None,
) -> bytes:
    buf = bytearray()
    buf += _init() + _font("A")

    def add(line: str = ""):
        buf.extend(str(line).encode("utf-8", "replace"))
        buf.extend(b"\n")

    if width is None:
        width = get_receipt_cols()
    right_guard = get_right_guard()
    header_lines = get_header_lines()
    footer_note = get_footer_note()
    billing_cfg = get_billing_config()

    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(header_lines[0])
    add("")
    buf += _bold(False) + _scale(1, 1)
    for line in header_lines[1:]:
        add(line)
    buf += _align(0)

    table = header.get("table_number") or "-"
    bill_label = header.get("bill_label") or "BILL"
    pax = header.get("pax") or "-"
    opened = header.get("opened_at") or "-"
    printed = header.get("printed_at") or "-"
    prepared_by = header.get("prepared_by") or "-"
    guest = header.get("guest_name") or ""

    big_width = max(1, width - right_guard)
    buf += _bold(True) + _double_height(True)
    add(_line_lr("TABLE", table, big_width))
    buf += _double_height(False) + _bold(False)
    add(_line_lr("Bill", bill_label, width))
    add(_line_lr("PAX", pax, width))
    add(_line_lr("Opened", opened, width))
    add(_line_lr("Printed", printed, width))
    add(_line_lr("Prepared", prepared_by, width))
    if guest:
        add(_line_lr("Guest", guest, width))
    add("-" * width)

    for it in items or []:
        for line in _format_item_lines(it, width):
            add(line)

    add("-" * width)

    subtotal = totals.get("subtotal", 0)
    discount_amount = totals.get("discount_amount", 0)
    discount_percent = totals.get("discount_percent", 0)
    packaging_fee = totals.get("packaging_fee", 0)
    service = totals.get("service", 0)
    service_percent = totals.get("service_percent")
    if service_percent is None:
        service_percent = billing_cfg.get("service_percent", 0)
    tax = totals.get("tax", 0)
    tax_percent = totals.get("tax_percent")
    if tax_percent is None:
        tax_percent = billing_cfg.get("tax_percent", 0)
    rounding = totals.get("rounding", 0)
    total = totals.get("total", 0)
    dp_applied = totals.get("dp_applied", 0)
    total_after_dp = totals.get("total_after_dp", total - dp_applied)
    payment = totals.get("payment") or {}

    add(_line_lr("Subtotal", format_idr(subtotal), width))
    if discount_amount:
        label = f"Discount ({discount_percent}%)" if discount_percent else "Discount"
        add(_line_lr(label, "- " + format_idr(discount_amount), width))
    if packaging_fee:
        add(_line_lr("Packaging", format_idr(packaging_fee), width))
    if service:
        label = f"Service ({service_percent}%)" if service_percent else "Service"
        add(_line_lr(label, format_idr(service), width))
    if tax:
        label = f"Tax ({tax_percent}%)" if tax_percent else "Tax"
        add(_line_lr(label, format_idr(tax), width))
    if rounding and not totals.get("is_final"):
        add(_line_lr("Rounding", format_idr(rounding), width))
    buf += _bold(True) + _double_height(True)
    add(_line_lr("Total", format_idr(total), big_width))
    buf += _double_height(False) + _bold(False)
    if dp_applied:
        buf += _bold(True) + _double_height(True)
        add(_line_lr("DP", "- " + format_idr(dp_applied), big_width))
        add(_line_lr("Final Total", format_idr(total_after_dp), big_width))
        buf += _double_height(False) + _bold(False)

    if payment:
        method = payment.get("method_label") or payment.get("method") or ""
        paid_amount = payment.get("paid_amount")
        change = payment.get("change")
        if method and paid_amount is not None:
            add(_line_lr(f"Paid via {method}", format_idr(paid_amount), width))
        if change:
            add(_line_lr("Change", format_idr(change), width))

    buf += _align(1)
    add("")
    if totals.get("is_final"):
        closed = header.get("closed_at") or ""
        if closed:
            add(f"Closed: {closed}")
    if footer_note:
        add(footer_note)
    buf += _align(0)
    add("")
    buf += b"\n" * max(2, get_feed_lines())
    buf += b"\x1dV\x00"
    return bytes(buf)


def build_receipt_bytes_from_ctx(ctx: dict, *, width: int | None = None) -> bytes:
    if not isinstance(ctx, dict):
        return build_receipt_bytes({}, [], {}, title="Receipt", width=width)

    blocks = ctx.get("blocks") or []
    if not blocks:
        blocks = [{
            "header": ctx.get("header") or {},
            "lines": ctx.get("lines") or [],
            "subtotal": ctx.get("subtotal"),
            "discount_amount": ctx.get("discount_amount"),
            "discount_percent": ctx.get("discount_percent"),
            "service": ctx.get("service"),
            "tax": ctx.get("tax"),
            "total": ctx.get("total"),
            "dp_applied": ctx.get("dp_applied"),
            "dp_remaining": ctx.get("dp_remaining"),
            "service_percent": ctx.get("service_percent"),
            "packaging_fee": ctx.get("packaging_fee"),
            "rounding_down": ctx.get("rounding_down"),
            "payment": ctx.get("payment"),
        }]

    title = ctx.get("title") or ""
    primary = blocks[0]
    header = primary.get("header") or {}
    is_final = bool(ctx.get("is_final"))

    if width is None:
        width = get_receipt_cols()
    right_guard = get_right_guard()
    header_lines = get_header_lines()
    footer_note = get_footer_note()
    billing_cfg = get_billing_config()

    buf = bytearray()
    buf += _init() + _font("A")

    def add(line: str = ""):
        buf.extend(str(line).encode("utf-8", "replace"))
        buf.extend(b"\n")

    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(header_lines[0])
    add("")
    buf += _bold(False) + _scale(1, 1)
    for line in header_lines[1:]:
        add(line)
    buf += _align(0)

    table = header.get("table_number") or "-"
    bill_label = header.get("bill_label") or "BILL"
    pax = header.get("pax") or "-"
    opened = header.get("opened_at_fmt") or header.get("opened_at") or "-"
    printed = header.get("printed_at") or "-"
    closed = header.get("closed_at_fmt") or ""
    prepared_by = header.get("prepared_by") or "-"
    guest = header.get("guest_name") or ""

    big_width = max(1, width - right_guard)
    buf += _bold(True) + _double_height(True)
    add(_line_lr("TABLE", table, big_width))
    buf += _double_height(False) + _bold(False)
    add(_line_lr("Bill", bill_label, width))
    add(_line_lr("PAX", pax, width))
    add(_line_lr("Opened", opened, width))
    add(_line_lr("Printed", printed, width))
    add(_line_lr("Prepared", prepared_by, width))
    if guest:
        add(_line_lr("Guest", guest, width))
    add("-" * width)

    for idx, block in enumerate(blocks):
        if idx > 0:
            label = block.get("header", {}).get("bill_label") or f"BLOCK {idx + 1}"
            add(_center(f"[{label}]", width))
        if len(blocks) > 1:
            svc_type = (block.get("service_type") or "dine_in").strip().lower()
            block_is_takeaway = svc_type == "takeaway" or str(block.get("header", {}).get("table_number", "")).upper() in ("TA", "TAKE AWAY")
            add(_center("TAKE AWAY" if block_is_takeaway else "DINE IN", width))
        for it in block.get("lines") or []:
            for line in _format_item_lines(it, width):
                add(line)
            note = (it.get("note") or "").strip()
            if note:
                for ln in _wrap_words(note, max(8, width - 4)):
                    add("  " + ln)
        if idx < len(blocks) - 1:
            add("-" * width)

    add("-" * width)

    combined_totals = ctx.get("combined_totals") or None
    if combined_totals:
        service_pct = combined_totals.get("service_percent")
        if service_pct is None:
            service_pct = billing_cfg.get("service_percent", 0)
        tax_pct = combined_totals.get("tax_percent")
        if tax_pct is None:
            tax_pct = billing_cfg.get("tax_percent", 0)
        if combined_totals.get("packaging", 0):
            add(_line_lr("Take Away Charge", format_idr(combined_totals["packaging"]), width))
        add(_line_lr("Subtotal (Dine In)", format_idr(combined_totals.get("subtotal_dine", 0)), width))
        add(_line_lr("Subtotal (Take Away)", format_idr(combined_totals.get("subtotal_takeaway", 0)), width))
        service_label = f"Service ({service_pct}%)" if service_pct else "Service"
        tax_label = f"Tax ({tax_pct}%)" if tax_pct else "Tax"
        add(_line_lr(service_label, format_idr(combined_totals.get("service", 0)), width))
        add(_line_lr(tax_label, format_idr(combined_totals.get("tax", 0)), width))
        buf += _bold(True) + _double_height(True)
        add(_line_lr("Total", format_idr(combined_totals.get("total", 0)), big_width))
        buf += _double_height(False) + _bold(False)
        dp_applied = combined_totals.get("dp_applied", 0)
        if dp_applied:
            buf += _bold(True) + _double_height(True)
            add(_line_lr("DP", "- " + format_idr(dp_applied), big_width))
            add(_line_lr("Final Total", format_idr(combined_totals.get("after_dp", 0)), big_width))
            buf += _double_height(False) + _bold(False)
    else:
        service_pct = primary.get("service_percent")
        if service_pct is None:
            service_pct = billing_cfg.get("service_percent", 0)
        tax_pct = primary.get("tax_percent")
        if tax_pct is None:
            tax_pct = billing_cfg.get("tax_percent", 0)
        totals = {
            "subtotal": primary.get("subtotal", 0),
            "discount_amount": primary.get("discount_amount", 0),
            "discount_percent": primary.get("discount_percent", 0),
            "packaging_fee": primary.get("packaging_fee", 0),
            "service": primary.get("service", 0),
            "service_percent": service_pct or 0,
            "tax": primary.get("tax", 0),
            "tax_percent": tax_pct or 0,
            "rounding": primary.get("rounding_down", 0),
            "total": primary.get("total", 0),
            "dp_applied": primary.get("dp_applied", 0),
            "total_after_dp": (primary.get("total", 0) or 0) - (primary.get("dp_applied", 0) or 0),
            "payment": primary.get("payment") or ctx.get("payment") or {},
        }
        add(_line_lr("Subtotal", format_idr(totals["subtotal"]), width))
        if totals["discount_amount"]:
            label = f"Discount ({totals['discount_percent']}%)" if totals["discount_percent"] else "Discount"
            add(_line_lr(label, "- " + format_idr(totals["discount_amount"]), width))
        if totals["packaging_fee"]:
            add(_line_lr("Packaging", format_idr(totals["packaging_fee"]), width))
        if totals["service"]:
            label = f"Service ({totals['service_percent']}%)" if totals["service_percent"] else "Service"
            add(_line_lr(label, format_idr(totals["service"]), width))
        if totals["tax"]:
            label = f"Pajak ({totals['tax_percent']}%)" if totals["tax_percent"] else "Pajak"
            add(_line_lr(label, format_idr(totals["tax"]), width))
        buf += _bold(True) + _double_height(True)
        add(_line_lr("Total", format_idr(totals["total"]), big_width))
        buf += _double_height(False) + _bold(False)
        if totals["dp_applied"]:
            buf += _bold(True) + _double_height(True)
            add(_line_lr("DP", "- " + format_idr(totals["dp_applied"]), big_width))
            add(_line_lr("Final Total", format_idr(totals["total_after_dp"]), big_width))
            buf += _double_height(False) + _bold(False)

        payment = totals.get("payment") or {}
        if payment:
            method = payment.get("method_label") or payment.get("method") or ""
            paid_amount = payment.get("paid_amount")
            change = payment.get("change")
            if method and paid_amount is not None:
                add(_line_lr(f"Paid via {method}", format_idr(paid_amount), width))
            if change:
                add(_line_lr("Change", format_idr(change), width))

    add("")
    buf += _align(1)
    if is_final:
        dp_applied = primary.get("dp_applied") or 0
        dp_remaining = primary.get("dp_remaining")
        if dp_applied:
            add(f"DP diterapkan: {format_idr(dp_applied)}")
        if dp_remaining is not None and dp_remaining > 0:
            add(f"Sisa DP: {format_idr(dp_remaining)}")
        if closed:
            add(f"Closed: {closed}")
    if footer_note:
        add(footer_note)
    buf += _align(0)
    buf += b"\n" * max(2, get_feed_lines())
    buf += b"\x1dV\x00"
    return bytes(buf)
