#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Etape 5 : HSRP

TELNET GNS3 uniquement.

IMPORTANT
---------
HSRP exige que les deux routeurs d'un même groupe soient dans le
même segment L2 / même VLAN. La topologie fournie montre R1/R5,
R2/R5, R3/R6 et R4/R6 comme couples Active/Standby, mais il faut
que chaque couple partage réellement le VLAN concerné.

Ce script NE tente donc pas de masquer cette contrainte :
il configure uniquement les paramètres HSRP sur les interfaces
indiquées ci-dessous. Vérifie le câblage/L2 avant exécution.

Plan prévu :
    VLAN 10 : R1 Active,  R5 Standby, VIP 192.168.10.254
    VLAN 20 : R2 Active,  R5 Standby, VIP 192.168.20.254
    VLAN 30 : R3 Active,  R6 Standby, VIP 192.168.30.254
    VLAN 40 : R4 Active,  R6 Standby, VIP 192.168.40.254

Adresses physiques proposées :
    R1 VLAN10 : 192.168.10.252/24
    R5 VLAN10 : 192.168.10.253/24

    R2 VLAN20 : 192.168.20.252/24
    R5 VLAN20 : 192.168.20.253/24

    R3 VLAN30 : 192.168.30.252/24
    R6 VLAN30 : 192.168.30.253/24

    R4 VLAN40 : 192.168.40.252/24
    R6 VLAN40 : 192.168.40.253/24

Telnet :
    R1 5000
    R2 5001
    R3 5002
    R4 5003
    R5 5004
    R6 5005

Installation :
    pip install netmiko PySide6

Lancement :
    python configure_tp17_hsrp.py
"""

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
    "R1": 5000,
    "R2": 5001,
    "R3": 5002,
    "R4": 5003,
    "R5": 5004,
    "R6": 5005,
}

# IMPORTANT :
# Adapte UNIQUEMENT les noms d'interfaces si ton image IOS/GNS3
# utilise un autre nom.
#
# Chaque entrée contient :
#   interface = interface L3 qui doit porter le VLAN
#   ip        = adresse physique du routeur
#   vlan      = groupe HSRP
#   vip       = adresse virtuelle HSRP
#   priority  = priorité HSRP
#
# Les interfaces sont volontairement explicites afin d'éviter
# une configuration automatique dangereuse sur le mauvais port.
HSRP = {
    "R1": {
        "interface": "Ethernet0/2.10",
        "ip": "192.168.10.252",
        "vlan": 10,
        "vip": "192.168.10.254",
        "priority": 110,
    },
    "R2": {
        "interface": "Ethernet0/2.20",
        "ip": "192.168.20.252",
        "vlan": 20,
        "vip": "192.168.20.254",
        "priority": 110,
    },
    "R3": {
        "interface": "Ethernet0/2.30",
        "ip": "192.168.30.252",
        "vlan": 30,
        "vip": "192.168.30.254",
        "priority": 110,
    },
    "R4": {
        "interface": "Ethernet0/2.40",
        "ip": "192.168.40.252",
        "vlan": 40,
        "vip": "192.168.40.254",
        "priority": 110,
    },
    "R5": {
        # R5 doit disposer d'une interface/subinterface L3
        # réellement présente dans le même VLAN que le routeur actif.
        "interface": "Ethernet0/2.10",
        "ip": "192.168.10.253",
        "vlan": 10,
        "vip": "192.168.10.254",
        "priority": 100,
    },
    "R6": {
        "interface": "Ethernet0/2.30",
        "ip": "192.168.30.253",
        "vlan": 30,
        "vip": "192.168.30.254",
        "priority": 100,
    },
}

# Les deux groupes supplémentaires sur R5/R6 pour VLAN 20/40
# nécessitent une seconde interface/subinterface L3 réellement
# connectée au même domaine L2 que le VLAN correspondant.
SECONDARY = {
    "R5": {
        "interface": "Ethernet0/3.20",
        "ip": "192.168.20.253",
        "vlan": 20,
        "vip": "192.168.20.254",
        "priority": 100,
    },
    "R6": {
        "interface": "Ethernet0/3.40",
        "ip": "192.168.40.253",
        "vlan": 40,
        "vip": "192.168.40.254",
        "priority": 100,
    },
}

PAIRS = {
    "VLAN 10": ("R1", "R5"),
    "VLAN 20": ("R2", "R5"),
    "VLAN 30": ("R3", "R6"),
    "VLAN 40": ("R4", "R6"),
}

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"tp17_hsrp_{datetime.now():%Y%m%d_%H%M%S}.log"

def log(text):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {text}\n")

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
    for error in (
        "% invalid input",
        "% incomplete command",
        "% ambiguous command",
        "% command rejected",
    ):
        if error in low:
            raise RuntimeError(f"Commande rejetée : {command}\n{output}")
    return output

def entry_for(router):
    if router in SECONDARY:
        return SECONDARY[router]
    return HSRP[router]

def configure_router(name, write_log):
    conn = None
    item = entry_for(name)

    try:
        write_log(f"[{name}] Connexion Telnet localhost:{ROUTERS[name]}")
        conn = connect(name)

        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception:
            conn.enable()

        write_log(f"[{name}] Mode privilégié OK")

        interface = item["interface"]
        ip = item["ip"]
        vlan = item["vlan"]
        vip = item["vip"]
        priority = item["priority"]

        commands = [
            "configure terminal",
            "no ip domain lookup",
            f"interface {interface}",
            f"ip address {ip} 255.255.255.0",
            "no shutdown",
            f"standby {vlan} ip {vip}",
            f"standby {vlan} priority {priority}",
            f"standby {vlan} preempt",
            "exit",
            "end",
        ]

        for command in commands:
            write_log(f"[{name}] {command}")
            send(conn, command)

        output = send(conn, "show standby brief")
        log(f"===== {name} / show standby brief =====\n{output}")

        # Vérification IP également utile pour détecter une interface
        # mal choisie avant de tester HSRP.
        ip_output = send(conn, "show ip interface brief")
        log(f"===== {name} / show ip interface brief =====\n{ip_output}")

        save = conn.send_command_timing(
            "copy running-config startup-config",
            read_timeout=45,
            strip_prompt=False,
            strip_command=False,
        )
        if "destination filename" in save.lower():
            save += conn.send_command_timing(
                "\n",
                read_timeout=45,
                strip_prompt=False,
                strip_command=False,
            )

        log(f"===== {name} / sauvegarde =====\n{save}")

        return output + "\n\n===== show ip interface brief =====\n" + ip_output

    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP17 — Étape 5 — HSRP")
        self.resize(900, 700)
        self.checks = {}

        root = QVBoxLayout(self)

        title = QLabel("TP17 — Étape 5 : HSRP")
        title.setStyleSheet("font-size:25px;font-weight:bold;")
        root.addWidget(title)

        warning = QLabel(
            "R1/R2/R3/R4 = Active  •  R5/R6 = Standby  •  "
            "HSRP nécessite le même domaine L2"
        )
        warning.setStyleSheet("color:#ffb000;font-size:14px;")
        root.addWidget(warning)

        group = QGroupBox("Groupes HSRP")
        gl = QVBoxLayout(group)

        descriptions = {
            "VLAN 10": "R1 Active / R5 Standby / VIP 192.168.10.254",
            "VLAN 20": "R2 Active / R5 Standby / VIP 192.168.20.254",
            "VLAN 30": "R3 Active / R6 Standby / VIP 192.168.30.254",
            "VLAN 40": "R4 Active / R6 Standby / VIP 192.168.40.254",
        }

        for key, text in descriptions.items():
            cb = QCheckBox(text)
            cb.setMinimumHeight(38)
            self.checks[key] = cb
            gl.addWidget(cb)

        root.addWidget(group)

        row = QHBoxLayout()
        all_btn = QPushButton("Tout sélectionner")
        all_btn.clicked.connect(
            lambda: [c.setChecked(True) for c in self.checks.values()]
        )
        row.addWidget(all_btn)

        none_btn = QPushButton("Tout désélectionner")
        none_btn.clicked.connect(
            lambda: [c.setChecked(False) for c in self.checks.values()]
        )
        row.addWidget(none_btn)
        root.addLayout(row)

        self.start = QPushButton("Configurer HSRP")
        self.start.clicked.connect(self.run)
        root.addWidget(self.start)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        root.addWidget(self.console)

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
        selected_groups = [
            group for group, cb in self.checks.items() if cb.isChecked()
        ]

        if not selected_groups:
            QMessageBox.warning(
                self, "Aucun groupe",
                "Sélectionne au moins un groupe HSRP."
            )
            return

        routers = []
        for group in selected_groups:
            for router in PAIRS[group]:
                if router not in routers:
                    routers.append(router)

        answer = QMessageBox.question(
            self,
            "Confirmation HSRP",
            "Groupes sélectionnés :\n"
            + "\n".join(selected_groups)
            + "\n\nRouteurs concernés : "
            + ", ".join(routers)
            + "\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.start.setEnabled(False)
        completed = []

        try:
            for router in routers:
                try:
                    self.write_log(f"\n========== {router} ==========")
                    output = configure_router(router, self.write_log)
                    completed.append(router)

                    box = QMessageBox(self)
                    box.setWindowTitle(f"Vérification HSRP — {router}")
                    box.setIcon(QMessageBox.Information)
                    box.setText(
                        f"{router} configuré.\n\n"
                        "Vérifie la sortie avant de continuer."
                    )
                    box.setDetailedText(output)
                    box.setStandardButtons(QMessageBox.Ok)
                    box.exec()

                except Exception as exc:
                    log(f"ERREUR {router}: {exc}")
                    QMessageBox.critical(
                        self,
                        "Configuration interrompue",
                        f"Erreur sur {router} :\n\n{exc}\n\n"
                        f"Routeurs terminés : "
                        f"{', '.join(completed) or 'aucun'}"
                    )
                    return

            QMessageBox.information(
                self,
                "Terminé",
                "Configuration HSRP terminée.\n\n"
                f"Routeurs : {', '.join(completed)}\n\n"
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
