#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TP17 - Configuration des VPCS via TELNET uniquement."""

import socket
import time
from pathlib import Path
from datetime import datetime

HOST = "127.0.0.1"
TIMEOUT = 15

VPCS = {
    "PC1":  (5010, "192.168.10.1/24", "192.168.10.254"),
    "PC2":  (5012, "192.168.10.2/24", "192.168.10.254"),
    "PC3":  (5014, "192.168.10.3/24", "192.168.10.254"),
    "PC4":  (5020, "192.168.20.1/24", "192.168.20.254"),
    "PC5":  (5016, "192.168.20.2/24", "192.168.20.254"),
    "PC6":  (5018, "192.168.20.3/24", "192.168.20.254"),
    "PC7":  (5022, "192.168.40.1/24", "192.168.40.254"),
    "PC8":  (5024, "192.168.40.2/24", "192.168.40.254"),
    "PC9":  (5026, "192.168.40.3/24", "192.168.40.254"),
    "PC10": (5032, "192.168.30.1/24", "192.168.30.254"),
    "PC11": (5028, "192.168.30.2/24", "192.168.30.254"),
    "PC12": (5030, "192.168.30.3/24", "192.168.30.254"),
}

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"vpcs_{datetime.now():%Y%m%d_%H%M%S}.log"

def log(msg):
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def recv(sock, delay=1):
    time.sleep(delay)
    sock.settimeout(2)
    data = bytearray()
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
        except socket.timeout:
            break
    return bytes(data).decode("utf-8", errors="ignore")

def configure(name, port, ip, gateway):
    log(f"\n===== {name} | TELNET {HOST}:{port} =====")
    with socket.create_connection((HOST, port), timeout=TIMEOUT) as sock:
        # Réveil de la console VPCS.
        sock.sendall(b"\r\n")
        output = recv(sock)
        if output:
            log(output.strip())

        for command in (f"ip {ip} {gateway}", "save"):
            log(f"> {command}")
            sock.sendall((command + "\r\n").encode())
            result = recv(sock)
            if result:
                log(result.strip())

        log("> show ip")
        sock.sendall(b"show ip\r\n")
        result = recv(sock)
        log(result.strip())

        if ip.split("/")[0] not in result:
            raise RuntimeError(
                f"Adresse {ip.split('/')[0]} non détectée dans la sortie de show ip."
            )

def main():
    log("TP17 - Configuration VPCS via TELNET")
    log("SSH n'est pas utilisé.")
    done = []

    for name, (port, ip, gateway) in VPCS.items():
        try:
            configure(name, port, ip, gateway)
            done.append(name)
            log(f"[OK] {name}")
        except Exception as exc:
            log(f"[ERREUR] {name}: {exc}")
            log("ARRÊT DU SCRIPT.")
            print(f"\nConfiguration interrompue sur {name}: {exc}")
            print("VPCS terminés :", ", ".join(done) or "aucun")
            print("Journal :", LOG_FILE)
            return 1

    log("\nConfiguration terminée.")
    log("VPCS configurés : " + ", ".join(done))
    print("\nConfiguration terminée.")
    print("Journal :", LOG_FILE)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
