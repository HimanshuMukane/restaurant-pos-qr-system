import time, os, tempfile, subprocess, shutil
from contextlib import contextmanager
from weasyprint import HTML, CSS
from ..config_store import get_printing_config

def _mock_on() -> bool:
    return (os.getenv("PRINT_BACKEND","").lower() == "mock") or (os.getenv("MOCK_PRINTING") == "1")

MOCK_DIR = os.getenv("PRINT_MOCK_DIR", "/tmp/pos_mock_prints")

def _mock_job(kind: str, printer: str | None, payload_path: str | None = None) -> str:
    import time, os
    try:
        os.makedirs(MOCK_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        if payload_path and os.path.exists(payload_path):
            with open(payload_path, "rb") as fsrc, open(
                os.path.join(MOCK_DIR, f"{ts}-{kind}-{(printer or 'default')}.bin"), "wb"
            ) as fdst:
                fdst.write(fsrc.read())
        return f"mock://{kind}/{printer or 'default'}/{ts}"
    except Exception:
        return f"mock://{kind}/{printer or 'default'}"



def _parse_printers(env):
    out = {}
    for kv in (env or "").split(","):
        kv = kv.strip()
        if not kv or "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def _get_printer_map():
    # read env each call so we don't depend on import order
    return _parse_printers(os.getenv("CUPS_PRINTERS"))

def _get_default_printer():
    pm = _get_printer_map()
    # new sane default: kitchen (you have it in CUPS_PRINTERS)
    return os.getenv("CUPS_DEFAULT_PRINTER") or pm.get("kitchen")

def _lp_options() -> dict:
    cfg = get_printing_config()
    opts = dict(cfg.get("lp_options") or {})
    media = (cfg.get("cups_media") or "").strip()
    if media:
        opts["media"] = media
    return opts


def _lp_qr_options() -> dict:
    opts = _lp_options()
    cfg = get_printing_config()
    media = (cfg.get("cups_qr_media") or "").strip()
    if media:
        opts["media"] = media
    return opts

def _lp_binary():
    """
    Resolve the `lp` executable early so we can surface a clearer error
    when CUPS is not installed or not on PATH. Supports override via env.
    """
    override = os.getenv("LP_BIN") or os.getenv("CUPS_LP_BIN")
    if override and os.path.exists(override):
        return override

    lp = shutil.which("lp")
    if lp:
        return lp

    # Fallback to common locations even if PATH is stripped (e.g., systemd)
    for p in ("/usr/bin/lp", "/usr/sbin/lp", "/bin/lp"):
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p

    raise RuntimeError("CUPS 'lp' command not found. Install cups-client or set PRINT_BACKEND=mock for testing.")

@contextmanager
def _tmpfile(suffix):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.close()
    try:
        yield f.name
    finally:
        try: os.remove(f.name)
        except OSError: pass

def _lp_print(path, printer=None, options=None):
    if _mock_on():
        return _mock_job("cups", printer, payload_path=path)
    lp = _lp_binary()
    printer = printer or _get_default_printer()
    if not printer:
        raise RuntimeError("No CUPS printer configured (set CUPS_DEFAULT_PRINTER or CUPS_PRINTERS)")
    cmd = [lp, "-d", printer]
    for k, v in (options or _lp_options()).items():
        cmd += ["-o", f"{k}={v}"]
    cmd.append(path)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"lp failed: {res.stderr.strip()}")
    return res.stdout.strip()

def html_to_pdf_bytes(html: str) -> bytes:
    cfg = get_printing_config()
    width = int(cfg.get("paper_width_mm") or 80)
    css = CSS(string=f"@page {{ size: {width}mm auto; margin: 0 }} body {{ margin:0 }}")
    with _tmpfile(".pdf") as pdf_path:
        HTML(string=html, base_url=".").write_pdf(pdf_path, stylesheets=[css])
        with open(pdf_path, "rb") as f:
            return f.read()

def print_html_receipt(html: str, printer_key: str | None = None):
    pdf_bytes = html_to_pdf_bytes(html)
    with _tmpfile(".pdf") as pdf_path:
        open(pdf_path, "wb").write(pdf_bytes)

        if _mock_on():
            return _lp_print(pdf_path, printer=printer_key)

        pm = _get_printer_map()
        printer_name = pm.get(printer_key) if printer_key else None
        if printer_key and printer_name is None:
            raise RuntimeError(f"Unknown printer_key '{printer_key}'. Check CUPS_PRINTERS mapping.")
        return _lp_print(pdf_path, printer=printer_name)


def print_png_bytes(png_bytes: bytes, printer_key: str | None = None):
    with _tmpfile(".png") as img_path:
        open(img_path, "wb").write(png_bytes)
        opts = _lp_qr_options()

        # <-- bypass mapping when mocking
        if _mock_on():
            return _lp_print(img_path, printer=printer_key, options=opts)

        pm = _get_printer_map()
        printer_name = pm.get(printer_key) if printer_key else None
        if printer_key and printer_name is None:
            raise RuntimeError(f"Unknown printer_key '{printer_key}'. Check CUPS_PRINTERS mapping.")
        return _lp_print(img_path, printer=printer_name, options=opts)
