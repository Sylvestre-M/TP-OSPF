#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TP17 - Etape 4 : routage inter-VLAN
# Telnet GNS3 uniquement.
#
# R5 : e0/2 -> VLAN10 (192.168.10.254/24)
#      e0/3 -> VLAN20 (192.168.20.254/24)
# R6 : e0/2 -> VLAN30 (192.168.30.254/24)
#      e0/3 -> VLAN40 (192.168.40.254/24)

import sys
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QPushButton, QGroupBox, QMessageBox, QPlainTextEdit
)

HOST = "127.0.0.1"

ROUTERS = {
    "R5": 5004,
    "R6": 5005,
}

CONFIG = {
    "R5": [
        ("Ethernet0/2", "Ethernet0/2.10", 10, "192.168.10.254"),
        ("Ethernet0/3", "Ethernet0/3.20", 20, "192.168.20.254"),
    ],
    "R6": [
        ("Ethernet0/2", "Ethernet0/2.30", 30, "192.168.30.254"),
        ("Ethernet0/3", "Ethernet0/3.40", 40, "192.168.40.254"),
    ],
}

MASK = "255.255.255.0"
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"tp17_intervlan_{datetime.now():%Y%m%d_%H%M%S}.log"

def log(text):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {text}"
    LOG_FILE.open("a", encoding="utf-8").write(line + "\n")

def connect(name):
    return ConnectHandler(
        device_type="cisco_ios_telnet",
        host=HOST,
        port=ROUTERS[name],
        username="",
        password="",
        secret="",
        conn_timeout=30,
        auth_timeout=30,
        banner_timeout=60,
        fast_cli=False,
    )

def send(conn, command):
    output = conn.send_command_timing(
        command,
        read_timeout=45,
        strip_prompt=False,
        strip_command=False,
    )
    low = output.lower()
    for error in ("% invalid input", "% incomplete command",
                  "% ambiguous command", "% command rejected"):
        if error in low:
            raise RuntimeError(f"Commande rejetée : {command}\n{output}")
    return output

def configure(name, write_log):
    conn = None
    try:
        write_log(f"[{name}] Connexion Telnet localhost:{ROUTERS[name]}")
        conn = connect(name)

        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception:
            conn.enable()

        commands = ["configure terminal", "no ip domain lookup"]

        for physical, sub, vlan, ip in CONFIG[name]:
            commands += [
                f"interface {physical}",
                "no ip address",
                "no shutdown",
                "exit",
                f"interface {sub}",
                f"encapsulation dot1Q {vlan}",
                f"ip address {ip} {MASK}",
                "no shutdown",
                "exit",
            ]

        commands.append("end")

        for command in commands:
            write_log(f"[{name}] {command}")
            send(conn, command)

        output = send(conn, "show ip interface brief")
        log(f"===== {name} =====\n{output}")

        save = conn.send_command_timing(
            "copy running-config startup-config",
            read_timeout=45,
            strip_prompt=False,
            strip_command=False,
        )
        if "destination filename" in save.lower():
            save += conn.send_command_timing(
                "\n", read_timeout=45,
                strip_prompt=False, strip_command=False
            )
        log(f"{name} - sauvegarde :\n{save}")

        return output

    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP17 — Etape 4 — Routage inter-VLAN")
        self.resize(850, 650)
        self.checks = {}

        layout = QVBoxLayout(self)

        title = QLabel("TP17 — Routage inter-VLAN")
        title.setStyleSheet("font-size:25px;font-weight:bold;")
        layout.addWidget(title)

        info = QLabel("R5 : VLAN 10 / 20    •    R6 : VLAN 30 / 40    •    Telnet")
        info.setStyleSheet("color:#00a0d1;font-size:14px;")
        layout.addWidget(info)

        group = QGroupBox("Routeurs à configurer")
        gl = QVBoxLayout(group)

        for name in ROUTERS:
            text = "R5 — VLAN 10 / VLAN 20" if name == "R5" else "R6 — VLAN 30 / VLAN 40"
            cb = QCheckBox(text)
            cb.setMinimumHeight(40)
            self.checks[name] = cb
            gl.addWidget(cb)

        layout.addWidget(group)

        buttons = QHBoxLayout()
        all_btn = QPushButton("Tout sélectionner")
        all_btn.clicked.connect(lambda: [c.setChecked(True) for c in self.checks.values()])
        buttons.addWidget(all_btn)

        none_btn = QPushButton("Tout désélectionner")
        none_btn.clicked.connect(lambda: [c.setChecked(False) for c in self.checks.values()])
        buttons.addWidget(none_btn)
        layout.addLayout(buttons)

        self.start = QPushButton("Configurer")
        self.start.clicked.connect(self.run)
        layout.addWidget(self.start)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        self.setStyleSheet("""
        QWidget { background:#101820; color:#f2f5f7; }
        QGroupBox { border:1px solid #3a4856; border-radius:8px;
                    margin-top:8px; padding:12px; font-weight:bold; }
        QCheckBox { font-size:15px; padding:4px; }
        QPlainTextEdit { background:#080d12; color:#d7e0e8;
                         border:1px solid #33404d; border-radius:8px;
                         font-family:monospace; padding:10px; }
        QPushButton { background:#00a0d1; color:white; border:none;
                      border-radius:7px; padding:12px; font-weight:bold; }
        QPushButton:hover { background:#19b3df; }
        QPushButton:disabled { background:#3d474f; }
        """)

    def write_log(self, text):
        self.console.appendPlainText(text)
        log(text)
        QApplication.processEvents()

    def run(self):
        selected = [n for n, c in self.checks.items() if c.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Aucun routeur", "Sélectionne au moins un routeur.")
            return

        if QMessageBox.question(
            self, "Confirmation",
            "Configurer : " + ", ".join(selected) + " ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return

        self.start.setEnabled(False)
        completed = []

        try:
            for name in selected:
                try:
                    self.write_log(f"\n========== {name} ==========")
                    output = configure(name, self.write_log)
                    completed.append(name)

                    box = QMessageBox(self)
                    box.setWindowTitle(f"Vérification — {name}")
                    box.setIcon(QMessageBox.Information)
                    box.setText(
                        f"{name} configuré.\n\n"
                        "Vérifie la sortie avant de continuer."
                    )
                    box.setDetailedText(output)
                    box.setStandardButtons(QMessageBox.Ok)
                    box.exec()

                except Exception as exc:
                    log(f"ERREUR {name}: {exc}")
                    QMessageBox.critical(
                        self, "Configuration interrompue",
                        f"Erreur sur {name} :\n\n{exc}\n\n"
                        f"Routeurs terminés : {', '.join(completed) or 'aucun'}"
                    )
                    return

            QMessageBox.information(
                self, "Terminé",
                "Routage inter-VLAN terminé.\n\n"
                f"Routeurs : {', '.join(completed)}\n"
                f"Log : {LOG_FILE}"
            )
        finally:
            self.start.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
