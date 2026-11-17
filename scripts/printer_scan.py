#!/usr/bin/env python3
import argparse
import ipaddress
import json
import os
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

RAW_PORTS_DEFAULT = [9100, 9101, 9102, 9103, 9104, 9105]
LPD_PORT = 515
IPP_PORT = 631

PRINTERS_JSON = os.getenv("PRINTERS_JSON", "static/printers.json")


def parse_ports(raw: str) -> list[int]:
    out = []
    for p in (raw or "").split(","):
        p = p.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            pass
    return out


def protocol_for_port(port: int) -> str:
    if port in RAW_PORTS_DEFAULT:
        return "jetdirect"
    if port == LPD_PORT:
        return "lpd"
    if port == IPP_PORT:
        return "ipp"
    return "tcp"


def scan_port(ip: str, port: int, timeout_s: float) -> dict | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout_s)
    try:
        s.connect((ip, port))
        return {"ip": ip, "port": port, "protocol": protocol_for_port(port)}
    except Exception:
        return None
    finally:
        try:
            s.close()
        except Exception:
            pass


def default_subnet() -> str:
    return os.getenv("POS_SCAN_SUBNET", "10.0.0.0/24")


def iter_hosts(subnet: str):
    net = ipaddress.ip_network(subnet, strict=False)
    for host in net.hosts():
        yield str(host)


def make_id(prefix: str, ip: str, port: int) -> str:
    ip_part = ip.replace(".", "-")
    if port == 9100:
        return f"{prefix}-{ip_part}"
    return f"{prefix}-{ip_part}-p{port}"


def load_printers_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_printers_cfg(path: str, cfg: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description="Scan network for printers (raw/LPD/IPP).")
    ap.add_argument("--subnet", default=default_subnet(), help="CIDR, e.g. 10.0.0.0/24")
    ap.add_argument("--ports", default="", help="Comma list of ports to scan (default: raw+LPD+IPP)")
    ap.add_argument("--timeout", type=float, default=0.6, help="TCP connect timeout (seconds)")
    ap.add_argument("--workers", type=int, default=128, help="Concurrent scan workers")
    ap.add_argument("--json", action="store_true", help="Output JSON results")
    ap.add_argument("--save", action="store_true", help="Append raw printers to printers.json")
    ap.add_argument("--id-prefix", default="printer", help="ID prefix when saving")
    ap.add_argument("--tag", action="append", default=[], help="Tag to apply on saved entries")
    ap.add_argument("--emit-lpadmin", action="store_true", help="Print lpadmin commands (no execution)")
    args = ap.parse_args()

    ports = parse_ports(args.ports)
    if not ports:
        ports = RAW_PORTS_DEFAULT + [LPD_PORT, IPP_PORT]

    tasks = []
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for ip in iter_hosts(args.subnet):
            for port in ports:
                tasks.append(ex.submit(scan_port, ip, port, args.timeout))
        for fut in as_completed(tasks):
            res = fut.result()
            if res:
                results.append(res)

    results.sort(key=lambda r: (ipaddress.ip_address(r["ip"]), r["port"]))

    if args.save:
        raw_hits = [r for r in results if r["protocol"] == "jetdirect"]
        if raw_hits:
            cfg = load_printers_cfg(PRINTERS_JSON)
            printers = cfg.get("printers", [])
            existing = {(p.get("ip"), int(p.get("port") or 0)) for p in printers}
            added = 0
            for r in raw_hits:
                key = (r["ip"], int(r["port"]))
                if key in existing:
                    continue
                printers.append({
                    "id": make_id(args.id_prefix, r["ip"], int(r["port"])),
                    "ip": r["ip"],
                    "port": int(r["port"]),
                    "tags": [t for t in args.tag if t],
                })
                added += 1
            cfg["printers"] = printers
            save_printers_cfg(PRINTERS_JSON, cfg)
            if not args.json:
                print(f"Saved {added} printers to {PRINTERS_JSON}")
        elif not args.json:
            print("No raw printers found to save.")

    if args.emit_lpadmin:
        for r in results:
            if r["protocol"] != "jetdirect":
                continue
            pid = make_id(args.id_prefix, r["ip"], int(r["port"]))
            print(f"sudo lpadmin -p {pid} -E -v socket://{r['ip']}:{r['port']} -m raw")

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        if not results:
            print("No open printer ports found.")
            return
        print("Found:")
        for r in results:
            print(f"- {r['ip']}:{r['port']} ({r['protocol']})")


if __name__ == "__main__":
    main()
