import json, os
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, jsonify, request
from flask_login import login_required
from ..authz import roles_required
from .. import printing as printer_lib

bp = Blueprint("printers_api", __name__)

CFG_PATH = os.getenv("PRINTERS_JSON", "static/printers.json")
DEFAULT_SCAN_SUBNET = os.getenv("POS_SCAN_SUBNET", "10.0.0.0/24")
DEFAULT_SCAN_PORTS = [9100, 9101, 9102, 9103, 9104, 9105, 515, 631]
MAX_SCAN_HOSTS = int(os.getenv("POS_SCAN_MAX_HOSTS", "1024"))


def _load_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_cfg(cfg):
    tmp = CFG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, CFG_PATH)


def _parse_ports(raw: str | None) -> list[int]:
    if not raw:
        return list(DEFAULT_SCAN_PORTS)
    ports = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            val = int(part)
        except ValueError:
            continue
        if 1 <= val <= 65535:
            ports.append(val)
    if not ports:
        return list(DEFAULT_SCAN_PORTS)
    return sorted(set(ports))


def _protocol_for_port(port: int) -> str:
    if port in (9100, 9101, 9102, 9103, 9104, 9105):
        return "jetdirect"
    if port == 515:
        return "lpd"
    if port == 631:
        return "ipp"
    return "tcp"


def _probe(ip: str, port: int, timeout_s: float):
    try:
        with socket.create_connection((ip, port), timeout=timeout_s):
            return {"ip": ip, "port": port, "protocol": _protocol_for_port(port)}
    except Exception:
        return None


def _scan_subnet(subnet: str, ports: list[int], timeout_s: float, workers: int):
    net = ipaddress.ip_network(subnet, strict=False)
    host_count = max(int(net.num_addresses) - 2, 0)
    if host_count > MAX_SCAN_HOSTS:
        raise ValueError(f"subnet too large ({host_count} hosts), limit={MAX_SCAN_HOSTS}")

    results = []
    futures = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for host in net.hosts():
            ip = str(host)
            for port in ports:
                futures.append(ex.submit(_probe, ip, port, timeout_s))
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)
    results.sort(key=lambda r: (ipaddress.ip_address(r["ip"]), r["port"]))
    return results


def _printer_index(cfg):
    printers = cfg.get("printers", []) if isinstance(cfg, dict) else []
    by_key = {}
    for p in printers:
        ip = p.get("ip")
        port = int(p.get("port") or 0)
        if ip and port:
            by_key[(ip, port)] = p
    return by_key


@bp.get("/api/printers")
@login_required
@roles_required("admin", "cashier")
def api_list_printers():
    cfg = _load_cfg()
    return jsonify(cfg)


@bp.patch("/api/printers/<printer_id>")
@login_required
@roles_required("admin")
def api_update_printer(printer_id):
    body = request.get_json() or {}
    cfg = _load_cfg()
    printers = cfg.get("printers", [])
    target = next((p for p in printers if p.get("id") == printer_id), None)
    if not target:
        return jsonify({"status": "error", "message": "printer not found"}), 404

    if "name" in body:
        name = body.get("name")
        if name is None or str(name).strip() == "":
            target.pop("name", None)
        else:
            target["name"] = str(name).strip()
    if "tags" in body:
        tags_raw = body.get("tags") or []
        if isinstance(tags_raw, str):
            tags_raw = [t.strip() for t in tags_raw.split(",")]
        tags = [str(t).strip() for t in tags_raw if str(t).strip()]
        target["tags"] = tags

    _write_cfg(cfg)
    return jsonify({"status": "ok", "printer": target})


@bp.post("/api/printers/<printer_id>/mock")
@login_required
@roles_required("admin")
def api_printer_mock(printer_id):
    cfg, printers, idx = printer_lib.load_config(CFG_PATH)
    pr = idx.get(printer_id)
    if not pr:
        return jsonify({"status": "error", "message": "printer not found"}), 404

    lines = [
        "*** PRINTER TEST ***",
        f"Printer ID : {pr.id}",
        f"Name       : {pr.name or '-'}",
        f"IP         : {pr.ip}:{pr.port}",
        f"Tags       : {', '.join(pr.tags) or '-'}",
        f"Floors     : {', '.join(pr.floors) or 'all'}",
    ]
    payload = ("\n".join(lines) + "\n\n").encode("utf-8", errors="replace")

    try:
        if printer_lib.IS_MOCK:
            job = printer_lib._mock_save(pr.id, payload)
            mocked = True
        else:
            use_cups = (os.getenv("PRINT_BACKEND","").lower() == "cups")
            if use_cups:
                cups_map = printer_lib._parse_cups_printers_env()
                queue = cups_map.get(pr.id)
                if not queue:
                    raise RuntimeError(f"No CUPS queue mapped for '{pr.id}' (set CUPS_PRINTERS)")
                printer_lib.send_via_cups(queue, payload)
                job = f"cups://{queue}"
            else:
                printer_lib.send_raw(pr.ip, pr.port, payload)
                job = f"raw://{pr.ip}:{pr.port}"
            mocked = False
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "ok",
        "job": job,
        "mocked": mocked,
        "printer": {
            "id": pr.id, "name": pr.name, "ip": pr.ip, "port": pr.port,
            "tags": pr.tags, "floors": pr.floors
        }
    })


@bp.get("/api/printers/scan")
@login_required
@roles_required("admin")
def api_scan_printers():
    subnet = (request.args.get("subnet") or DEFAULT_SCAN_SUBNET).strip()
    ports = _parse_ports(request.args.get("ports"))
    try:
        timeout_s = float(request.args.get("timeout") or 0.6)
    except Exception:
        timeout_s = 0.6
    try:
        workers = int(request.args.get("workers") or 128)
    except Exception:
        workers = 128
    workers = max(8, min(workers, 512))

    try:
        results = _scan_subnet(subnet, ports, timeout_s, workers)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

    cfg = _load_cfg()
    by_key = _printer_index(cfg)
    out = []
    for r in results:
        hit = by_key.get((r["ip"], int(r["port"])))
        name = None
        pid = None
        if hit:
            name = hit.get("name") or hit.get("id")
            pid = hit.get("id")
        out.append({
            "ip": r["ip"],
            "port": int(r["port"]),
            "protocol": r["protocol"],
            "name": name,
            "id": pid,
        })
    return jsonify({"status": "ok", "subnet": subnet, "ports": ports, "results": out})


@bp.post("/api/printers/scan/test")
@login_required
@roles_required("admin")
def api_scan_test_print():
    data = request.get_json(silent=True) or {}
    ip = (data.get("ip") or "").strip()
    try:
        port = int(data.get("port") or 0)
    except Exception:
        port = 0
    name = (data.get("name") or "").strip()
    pid = (data.get("id") or "").strip()
    if not ip or not port:
        return jsonify({"status": "error", "message": "ip/port required"}), 400

    ESC = b"\x1b"
    GS = b"\x1d"
    INIT = ESC + b"@"
    CUT = GS + b"V" + b"\x42" + b"\x00"

    lines = [
        "*** PRINTER IDENTIFY ***",
        f"IP: {ip}:{port}",
        f"Name: {name or '-'}",
        f"ID: {pid or '-'}",
        "Tolong beritahu kasir lokasi printer ini.",
        "",
    ]
    payload = INIT + ("\n".join(lines)).encode("ascii", errors="ignore") + CUT

    try:
        printer_lib.send_raw(ip, port, payload, timeout=3)
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({"status": "ok"})
