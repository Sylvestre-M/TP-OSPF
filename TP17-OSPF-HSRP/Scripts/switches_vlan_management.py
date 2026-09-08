#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Étapes 2 et 3 : VLAN, trunks et gestion des switchs.

Connexion : TELNET vers les consoles GNS3 (aucun SSH).

IMPORTANT :
Le câblage a été repris de la capture GNS3 fournie et est défini dans PORTS.
    - ports vers les VPCS : access dans le VLAN correspondant
    - ports e0/0 vers R5/R6 : trunk transportant 10,20,30,40,99

Le script configure :
    1. VLAN 10,20,30,40
    2. VLAN 99 MANAGEMENT
    3. ports access
    4. ports trunk avec VLAN 10,20,30,40,99
    5. SVI VLAN 99
    6. no ip domain lookup
    7. hostname
    8. show vlan brief
    9. show interfaces trunk
   10. show ip interface brief

Après chaque switch, la vérification est affichée et l'utilisateur doit
valider avant de passer au suivant.

Installation :
    pip install netmiko PySide6

Lancement :
    python3 configure_tp17_switches_vlan_management.py
"""

import sys
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

HOST = "127.0.0.1"

# Consoles Telnet GNS3 de la topologie TP17.
SWITCHES = {
    "S1": 5006,
    "S2": 5007,
    "S3": 5008,
    "S4": 5009,
}

# ------------------------------------------------------------
# A MODIFIER SELON LE CABLAGE EXACT DE TA TOPOLOGIE
# ------------------------------------------------------------
#
# Exemple :
# "access": {
#     "Ethernet0/0": 10,
#     "Ethernet0/1": 10,
#     "Ethernet0/2": 20,
# }
#
# "trunk": [
#     "Ethernet0/3",
# ]
#
# Ne mets dans access/trunk QUE les ports réellement présents.
PORTS = {
    # Câblage relevé sur la capture GNS3 fournie :
    #
    # S1 e0/0 <-> R5 e0/2
    # S1 e0/1 <-> PC2
    # S1 e0/2 <-> PC1
    # S1 e0/3 <-> PC3
    #
    # S2 e0/0 <-> R5 e0/3
    # S2 e0/1 <-> PC4
    # S2 e0/2 <-> PC5
    # S2 e0/3 <-> PC6
    #
    # S3 e0/0 <-> R6 e0/2
    # S3 e0/1 <-> PC12
    # S3 e0/2 <-> PC10
    # S3 e0/3 <-> PC11
    #
    # S4 e0/0 <-> R6 e0/3
    # S4 e0/1 <-> PC9
    # S4 e0/2 <-> PC8
    # S4 e0/3 <-> PC7
    #
    # Les ports e0/0 sont donc des trunks vers R5/R6.
    "S1": {
        "access": {
            "Ethernet0/1": 10,  # PC2
            "Ethernet0/2": 10,  # PC1
            "Ethernet0/3": 10,  # PC3
        },
        "trunk": [
            "Ethernet0/0",      # R5 e0/2
        ],
    },
    "S2": {
        "access": {
            "Ethernet0/1": 20,  # PC4
            "Ethernet0/2": 20,  # PC5
            "Ethernet0/3": 20,  # PC6
        },
        "trunk": [
            "Ethernet0/0",      # R5 e0/3
        ],
    },
    "S3": {
        "access": {
            "Ethernet0/1": 30,  # PC12
            "Ethernet0/2": 30,  # PC10
            "Ethernet0/3": 30,  # PC11
        },
        "trunk": [
            "Ethernet0/0",      # R6 e0/2
        ],
    },
    "S4": {
        "access": {
            "Ethernet0/1": 40,  # PC9
            "Ethernet0/2": 40,  # PC8
            "Ethernet0/3": 40,  # PC7
        },
        "trunk": [
            "Ethernet0/0",      # R6 e0/3
        ],
    },
}

# Management VLAN 99.
# Le réseau 192.168.99.0/24 est dédié à la gestion.
# La passerelle .254 devra être créée à l'étape L3/HSRP.
MANAGEMENT = {
    "S1": "192.168.99.11",
    "S2": "192.168.99.12",
    "S3": "192.168.99.13",
    "S4": "192.168.99.14",
}

MASK = "255.255.255.0"
GATEWAY = "192.168.99.254"

CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 30
BANNER_TIMEOUT = 60
READ_TIMEOUT = 45

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"tp17_switches_{datetime.now():%Y%m%d_%H%M%S}.log"


def log(text):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {text}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def connect_switch(name):
    return ConnectHandler(
        device_type="cisco_ios_telnet",
        host=HOST,
        port=SWITCHES[name],
        username="",
        password="",
        secret="",
        conn_timeout=CONNECT_TIMEOUT,
        auth_timeout=AUTH_TIMEOUT,
        banner_timeout=BANNER_TIMEOUT,
        fast_cli=False,
    )


def configure_switch(name, ui_log):
    conn = None

    try:
        ui_log(f"[{name}] Connexion Telnet...")
        conn = connect_switch(name)
        ui_log(f"[{name}] Connexion OK.")

        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception:
            conn.enable()

        commands = [
            "configure terminal",
            f"hostname {name}",
            "no ip domain lookup",
            "vlan 10",
            "name VLAN10",
            "exit",
            "vlan 20",
            "name VLAN20",
            "exit",
            "vlan 30",
            "name VLAN30",
            "exit",
            "vlan 40",
            "name VLAN40",
            "exit",
            "vlan 99",
            "name MANAGEMENT",
            "exit",
        ]

        # Ports access.
        for interface, vlan in PORTS[name]["access"].items():
            if vlan not in (10, 20, 30, 40):
                raise ValueError(
                    f"{name}: VLAN access invalide sur {interface}: {vlan}"
                )

            commands += [
                f"interface {interface}",
                "switchport mode access",
                f"switchport access vlan {vlan}",
                "spanning-tree portfast",
                "no shutdown",
                "exit",
            ]

        # Ports trunk.
        for interface in PORTS[name]["trunk"]:
            commands += [
                f"interface {interface}",
                "switchport mode trunk",
                "switchport trunk allowed vlan 10,20,30,40,99",
                "no shutdown",
                "exit",
            ]

        # SVI de management.
        commands += [
            "interface vlan 99",
            f"ip address {MANAGEMENT[name]} {MASK}",
            "no shutdown",
            "exit",
            f"ip default-gateway {GATEWAY}",
            "end",
        ]

        for command in commands:
            ui_log(f"[{name}] {command}")
            output = conn.send_command_timing(
                command,
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )

            low = output.lower()
            if "% invalid input" in low or "% incomplete command" in low:
                raise RuntimeError(
                    f"Commande rejetée : {command}\n{output}"
                )

        checks = [
            "show vlan brief",
            "show interfaces trunk",
            "show ip interface brief",
        ]

        result = []
        for command in checks:
            ui_log(f"[{name}] {command}")
            output = conn.send_command_timing(
                command,
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )
            result.append(f"\n===== {command} =====\n{output}")

        verification = "".join(result)
        log(f"{name}\n{verification}")

        # Sauvegarde seulement après vérification.
        ui_log(f"[{name}] copy running-config startup-config")
        save_output = conn.send_command_timing(
            "copy running-config startup-config",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

        # Cisco IOS demande généralement Destination filename [startup-config]?
        if "destination filename" in save_output.lower():
            save_output += conn.send_command_timing(
                "\n",
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )

        log(f"{name} - sauvegarde:\n{save_output}")

        return verification

    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass


class VerificationDialog(QMessageBox):
    def __init__(self, parent, name, output):
        super().__init__(parent)
        self.setWindowTitle(f"Vérification — {name}")
        self.setIcon(QMessageBox.Information)
        self.setText(
            f"{name} configuré.\n\n"
            "Vérifie les trois commandes puis clique sur OK."
        )
        self.setDetailedText(output)
        self.setStandardButtons(QMessageBox.Ok)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP17 — VLAN / Trunks / Management")
        self.resize(900, 700)
        self.checks = {}

        root = QVBoxLayout(self)

        title = QLabel("TP17 — Étapes 2 et 3")
        title.setStyleSheet("font-size:25px;font-weight:bold;")
        root.addWidget(title)

        info = QLabel(
            "VLAN 10/20/30/40 + VLAN 99 Management. "
            "Sélectionne les switchs à configurer."
        )
        info.setStyleSheet("color:#00a0d1;font-size:14px;")
        root.addWidget(info)

        buttons = QHBoxLayout()

        all_btn = QPushButton("Tout sélectionner")
        all_btn.clicked.connect(
            lambda: [c.setChecked(True) for c in self.checks.values()]
        )
        buttons.addWidget(all_btn)

        none_btn = QPushButton("Tout désélectionner")
        none_btn.clicked.connect(
            lambda: [c.setChecked(False) for c in self.checks.values()]
        )
        buttons.addWidget(none_btn)

        root.addLayout(buttons)

        group = QGroupBox("Switchs")
        group_layout = QVBoxLayout(group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)

        for name in SWITCHES:
            cb = QCheckBox(f"{name}   —   Switch")
            cb.setMinimumHeight(40)
            self.checks[name] = cb
            layout.addWidget(cb)

        layout.addStretch()
        scroll.setWidget(container)
        group_layout.addWidget(scroll)
        root.addWidget(group)

        self.start = QPushButton("Configurer les switchs sélectionnés")
        self.start.clicked.connect(self.run)
        root.addWidget(self.start)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        root.addWidget(self.console)

        self.setStyleSheet("""
            QWidget { background:#101820; color:#f2f5f7; }
            QGroupBox {
                border:1px solid #3a4856; border-radius:8px;
                margin-top:8px; padding:12px; font-weight:bold;
            }
            QCheckBox { font-size:15px; padding:4px; }
            QPlainTextEdit {
                background:#080d12; color:#d7e0e8;
                border:1px solid #33404d; border-radius:8px;
                font-family:monospace; padding:10px;
            }
            QPushButton {
                background:#00a0d1; color:white; border:none;
                border-radius:7px; padding:12px; font-weight:bold;
            }
            QPushButton:hover { background:#19b3df; }
            QPushButton:disabled { background:#3d474f; }
        """)

    def ui_log(self, msg):
        self.console.appendPlainText(msg)
        log(msg)
        QApplication.processEvents()

    def run(self):
        selected = [
            name for name, cb in self.checks.items() if cb.isChecked()
        ]

        if not selected:
            QMessageBox.warning(
                self, "Aucun switch",
                "Sélectionne au moins un switch."
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmer",
            "Configuration de : " + ", ".join(selected) +
            "\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.start.setEnabled(False)
        done = []

        try:
            for name in selected:
                self.ui_log(f"\n========== {name} ==========")

                try:
                    verification = configure_switch(name, self.ui_log)
                    done.append(name)

                    # L'utilisateur doit valider avant le switch suivant.
                    VerificationDialog(
                        self, name, verification
                    ).exec()

                except Exception as exc:
                    log(f"ERREUR {name}: {exc}")
                    QMessageBox.critical(
                        self,
                        "Configuration interrompue",
                        f"Erreur sur {name} :\n\n{exc}\n\n"
                        f"Switchs terminés : {', '.join(done) or 'aucun'}"
                    )
                    return

            QMessageBox.information(
                self,
                "Terminé",
                "Configuration terminée.\n\n"
                f"Switchs : {', '.join(done)}\n\n"
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
