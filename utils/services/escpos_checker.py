import os
from .escpos_receipt import get_feed_lines, get_receipt_cols, _center, _line_lr, _wrap_words, _init, _align, _bold, _scale, _font
from ..config_store import get_escpos_config


def _checker_width() -> int:
    cfg = get_escpos_config()
    return int(cfg.get("checker_cols") or cfg.get("receipt_cols") or get_receipt_cols())


DEFAULT_WIDTH = _checker_width()
DEFAULT_FEED_LINES = int(os.getenv("CHECKER_FEED_LINES", str(get_feed_lines())))


def _format_qty_name(qty: float, name: str, width: int) -> list[str]:
    qty_txt = f"{qty:g}"
    left = f"{qty_txt} "
    avail = max(6, width - len(left))
    name_lines = _wrap_words(name, avail) or [""]
    lines = [left + name_lines[0]]
    for extra in name_lines[1:]:
        lines.append(" " * len(left) + extra)
    return lines


def _wrap_prefixed(label: str, text: str, width: int) -> list[str]:
    prefix = f"{label}: "
    avail = max(8, width - len(prefix))
    wrapped = _wrap_words(text or "", avail) or [""]
    lines = [prefix + wrapped[0]]
    pad = " " * len(prefix)
    for extra in wrapped[1:]:
        lines.append(pad + extra)
    return lines


def _format_staff_summary(name: str, meta: str, width: int) -> list[str]:
    meta = (meta or "").strip()
    if not meta:
        return _wrap_words(name or "", width) or [""]
    right = f" {meta}"
    avail = max(10, width - len(right))
    wrapped = _wrap_words(name or "", avail) or [""]
    lines = []
    for idx, part in enumerate(wrapped):
        if idx == 0:
            pad = max(1, width - len(part) - len(right))
            lines.append(part + (" " * pad) + right.strip())
        else:
            lines.append(part)
    return lines


def build_checker_bytes(header: dict, items: list[dict], *, width: int | None = None) -> bytes:
    if width is None:
        width = _checker_width()
    buf = bytearray()
    buf += _init() + _font("A")

    def add(line: str = ""):
        buf.extend(str(line).encode("utf-8", "replace"))
        buf.extend(b"\n")

    title = header.get("title") or "CHECKER"
    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(title)
    buf += _bold(False) + _scale(1, 1) + _align(0)

    table = header.get("table_number") or header.get("table_label") or "-"
    printed = header.get("printed_at") or "-"
    guest = header.get("guest_name") or ""
    pax = header.get("pax") or "-"
    split_label = (header.get("split_label") or "").strip()

    add(_line_lr("Printed", printed, width))
    add(_line_lr("PAX", pax, width))
    if guest:
        add(_line_lr("Guest", guest, width))
    if split_label:
        add(_line_lr("Split", split_label, width))

    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(str(table))
    buf += _align(0) + _bold(False) + _scale(1, 1)
    add("-" * width)

    for it in items or []:
        name = str(it.get("name") or "")
        qty = float(it.get("qty") or 0)
        is_void = bool(it.get("_void")) or qty < 0
        if is_void and qty > 0:
            qty = -abs(qty)

        if is_void:
            buf += _align(1) + _bold(True)
            add("VOID")
            buf += _align(0) + _bold(False)

        buf += _bold(True) + _scale(1, 2)
        for ln in _format_qty_name(qty, name, width):
            add(ln)
        buf += _bold(False) + _scale(1, 1)

        note_lines = it.get("note_lines") or []
        if note_lines and not is_void:
            add("")
            buf += _bold(True)
            add("CATATAN:")
            buf += _bold(False) + _scale(1, 2)
            for nl in note_lines:
                for ln in _wrap_words(nl, max(8, width - 4)):
                    add(" - " + ln)
            buf += _scale(1, 1)
        add("")

    add("-" * width)
    buf += b"\n" * max(2, DEFAULT_FEED_LINES)
    buf += b"\x1dV\x00"
    return bytes(buf)


def build_admin_checker_bytes(
    header: dict,
    sections: list[dict],
    details: list[dict],
    *,
    width: int | None = None,
) -> bytes:
    if width is None:
        width = _checker_width()
    buf = bytearray()
    buf += _init() + _font("A")

    def add(line: str = ""):
        buf.extend(str(line).encode("utf-8", "replace"))
        buf.extend(b"\n")

    title = header.get("title") or "ADMIN CHECKER"
    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(title)
    buf += _bold(False) + _scale(1, 1) + _align(0)

    table = header.get("table_number") or header.get("table_label") or "-"
    printed = header.get("printed_at") or "-"
    guest = header.get("guest_name") or ""
    pax = header.get("pax") or "-"
    split_label = (header.get("split_label") or "").strip()

    add(_line_lr("Printed", printed, width))
    add(_line_lr("PAX", pax, width))
    if guest:
        add(_line_lr("Guest", guest, width))
    if split_label:
        add(_line_lr("Split", split_label, width))

    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(str(table))
    buf += _align(0) + _bold(False) + _scale(1, 1)
    add("-" * width)

    for section in sections or []:
        title_txt = (section.get("title") or "").strip()
        rows = section.get("rows") or []
        if not title_txt or not rows:
            continue
        buf += _bold(True)
        add(title_txt)
        buf += _bold(False)
        for row in rows:
            for ln in _format_staff_summary(row.get("name") or "", row.get("meta") or "", width):
                add(ln)
        add("-" * width)

    if details:
        buf += _bold(True)
        add("DETAIL")
        buf += _bold(False)
        for item in details:
            qty = float(item.get("qty") or 0)
            for ln in _format_qty_name(qty, item.get("name") or "", width):
                add(ln)

            added_by = (item.get("added_by") or "").strip()
            if added_by:
                for ln in _wrap_prefixed("ADD", added_by, width):
                    add(ln)

            edited_by = (item.get("edited_by") or "").strip()
            if edited_by:
                for ln in _wrap_prefixed("EDIT", edited_by, width):
                    add(ln)

            void_qty = float(item.get("void_qty") or 0)
            void_by = (item.get("void_by") or "").strip()
            if void_qty > 0 or void_by:
                void_label = f"{void_qty:g} by {void_by}".strip() if void_by else f"{void_qty:g}"
                for ln in _wrap_prefixed("VOID", void_label, width):
                    add(ln)

            for note in item.get("note_lines") or []:
                for ln in _wrap_prefixed("NOTE", note, width):
                    add(ln)
            add("")

        add("-" * width)

    buf += b"\n" * max(2, DEFAULT_FEED_LINES)
    buf += b"\x1dV\x00"
    return bytes(buf)
