#!/usr/bin/env python3
"""
Send a test page to one or more ESC/POS printers over raw TCP.
Usage:
    python scripts/printer_test.py                  # tries CANDIDATES list
    python scripts/printer_test.py --ip 10.0.0.10  # specific IP
"""
import socket
import sys
import argparse

CANDIDATES = ["10.0.0.10", "10.0.0.11", "10.0.0.12", "10.0.0.13"]

RAW_PORTS = [9100]
TIMEOUT_S = 1.5

ESC  = b'\x1b'
GS   = b'\x1d'
CUT  = GS + b'V' + b'\x42' + b'\x00'
INIT = ESC + b'@'


def test_send(ip, port):
    msg = (
        f"\n\n*** PRINTER IDENTIFY ***\n"
        f"IP: {ip}  PORT: {port}\n"
        f"If you can read this, this printer is reachable.\n\n"
    ).encode('ascii', errors='ignore')
    payload = INIT + msg + CUT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT_S)
    try:
        s.connect((ip, port))
        s.sendall(payload)
        s.close()
        print(f"[OK] Printed on {ip}:{port}")
        return True
    except Exception as e:
        print(f"[--] {ip}:{port} -> {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="Send ESC/POS test page to a printer")
    ap.add_argument("--ip", help="Printer IP address")
    ap.add_argument("--port", type=int, default=9100, help="Printer port (default 9100)")
    args = ap.parse_args()

    targets = [(args.ip, args.port)] if args.ip else [(ip, p) for ip in CANDIDATES for p in RAW_PORTS]

    any_ok = False
    for ip, port in targets:
        if test_send(ip, port):
            any_ok = True
    if not any_ok:
        print("\nNo printers reached. Check IPs in CANDIDATES or pass --ip <addr>.")


if __name__ == "__main__":
    main()
