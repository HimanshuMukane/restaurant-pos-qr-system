import os
from datetime import datetime
from .escpos_receipt import (
    get_receipt_cols,
    _center,
    _line_lr,
    _wrap_words,
    _init,
    _align,
    _bold,
    _scale,
    _font,
)
from .escpos_images import png_bytes_to_raster


DEFAULT_QR_MAX_WIDTH = int(os.getenv("QR_MAX_WIDTH_DOTS", "576"))
DEFAULT_FEED_LINES = int(os.getenv("QR_FEED_LINES", "6"))


def build_qr_ticket_bytes(
    *,
    table: str,
    session_id: str,
    qr_url: str,
    qr_png_bytes: bytes,
    brand_name: str,
    wifi_ssid: str | None = None,
    wifi_pass: str | None = None,
    issued_at: str | None = None,
    width: int | None = None,
) -> bytes:
    if width is None:
        width = get_receipt_cols()
    buf = bytearray()
    buf += _init() + _font("B")

    def add(line: str = ""):
        buf.extend(str(line).encode("utf-8", "replace"))
        buf.extend(b"\n")

    buf += _align(1) + _bold(True) + _scale(2, 2)
    add(brand_name or "QR")
    buf += _bold(False) + _scale(1, 1)
    add("Scan & pesan dari ponsel Anda")
    add("")

    buf += _bold(True) + _scale(2, 2)
    add(f"MEJA {table}")
    buf += _bold(False) + _scale(1, 1)
    add("")

    try:
        buf += _align(1)
        raster = png_bytes_to_raster(qr_png_bytes, max_width=DEFAULT_QR_MAX_WIDTH)
        buf += raster
        buf += b"\n"
    except Exception:
        add("QR ERROR")
    finally:
        buf += _align(1)

    add("SCAN UNTUK PESAN")
    add("")

    if wifi_ssid:
        buf += _align(0)
        add("Wi-Fi Tamu")
        add(_line_lr("SSID", wifi_ssid, width))
        if wifi_pass:
            add(_line_lr("Pass", wifi_pass, width))
        add("")
        buf += _align(1)

    issued = issued_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    code_source = session_id or table or ""
    short_code = str(code_source)[:8].upper()
    add(f"Kode: {short_code} - {issued}")
    for ln in _wrap_words(qr_url, width):
        add(ln)

    add("")
    buf += b"\n" * max(2, DEFAULT_FEED_LINES)
    buf += b"\x1dV\x00"
    return bytes(buf)
