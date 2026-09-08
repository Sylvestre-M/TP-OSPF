#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Etape 6 : OSPF multi-area

TELNET GNS3 uniquement.

Topologie OSPF :
    Area 0 : R1, R2, R3, R4
    Area 1 : R5 + VLAN 10/20
    Area 2 : R6 + VLAN 30/40

Le script :
- permet de sélectionner un ou plusieurs routeurs ;
- configure OSPF process 1 ;
- configure les Router-ID ;
- annonce les réseaux de transit avec les bonnes areas ;
- annonce les VLAN utilisateurs sur R5/R6 ;
- affiche show ip ospf neighbor après chaque routeur ;
- affiche show ip route ospf ;
- demande une validation avant de continuer ;
- sauvegarde running-config -> startup-config ;
- utilise Telnet, jamais SSH.

Ports GNS3 :
    R1 5000
    R2 5001
    R3 5002
    R4 5003
    R5 5004
    R6 5005

Installation :
    pip install netmiko PySide6

Lancement :
    python configure_tp17_ospf.py
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

# Plan OSPF repris de la topologie.
OSPF = {
    "R1": {
        "router_id": "1.1.1.1",
        "networks": [
            ("10.0.0.0", "0.0.0.3", 0),
            ("10.0.2.0", "0.0.0.3", 0),
            ("10.0.4.0", "0.0.0.3", 0),
            ("10.0.6.0", "0.0.0.3", 0),
        ],
    },
    "R2": {
        "router_id": "2.2.2.2",
        "networks": [
            ("10.0.0.0", "0.0.0.3", 0),
            ("10.0.1.0", "0.0.0.3", 0),
            ("10.0.2.0", "0.0.0.3", 0),
            ("10.0.5.0", "0.0.0.3", 0),
            ("10.0.7.0", "0.0.0.3", 1),
        ],
    },
    "R3": {
        "router_id": "3.3.3.3",
        "networks": [
            ("10.0.0.0", "0.0.0.3", 0),
            ("10.0.3.0", "0.0.0.3", 0),
            ("10.0.5.0", "0.0.0.3", 0),
            ("10.0.9.0", "0.0.0.3", 2),
        ],
    },
    "R4": {
        "router_id": "4.4.4.4",
        "networks": [
            ("10.0.1.0", "0.0.0.3", 0),
            ("10.0.3.0", "0.0.0.3", 0),
            ("10.0.4.0", "0.0.0.3", 0),
            ("10.0.8.0", "0.0.0.3", 2),
        ],
    },
    "R5": {
        "router_id": "5.5.5.5",
        "networks": [
            ("10.0.6.0", "0.0.0.3", 1),
            ("10.0.7.0", "0.0.0.3", 1),
            ("192.168.10.0", "0.0.0.255", 1),
            ("192.168.20.0", "0.0.0.255", 1),
        ],
    },
    "R6": {
        "router_id": "6.6.6.6",
        "networks": [
            ("10.0.8.0", "0.0.0.3", 2),
            ("10.0.9.0", "0.0.0.3", 2),
            ("192.168.30.0", "0.0.0.255", 2),
            ("192.168.40.0", "0.0.0.255", 2),
        ],
    },
}

CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 30
BANNER_TIMEOUT = 60
READ_TIMEOUT = 45

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"tp17_ospf_{datetime.now():%Y%m%d_%H%M%S}.log"


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
        conn_timeout=CONNECT_TIMEOUT,
        auth_timeout=AUTH_TIMEOUT,
        banner_timeout=BANNER_TIMEOUT,
        fast_cli=False,
    )


def send(conn, command):
    output = conn.send_command_timing(
        command,
        read_timeout=READ_TIMEOUT,
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
            raise RuntimeError(
                f"Commande rejetée : {command}\n{output}"
            )

    return output


def configure(name, write_log):
    conn = None

    try:
        write_log(
            f"[{name}] Connexion Telnet localhost:{ROUTERS[name]}"
        )

        conn = connect(name)

        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception:
            conn.enable()

        data = OSPF[name]

        commands = [
            "configure terminal",
            "no ip domain lookup",
            "router ospf 1",
            f"router-id {data['router_id']}",
        ]

        for network, wildcard, area in data["networks"]:
            commands.append(
                f"network {network} {wildcard} area {area}"
            )

        commands += [
            "end",
        ]

        for command in commands:
            write_log(f"[{name}] {command}")
            send(conn, command)

        # Vérification OSPF.
        neighbor = send(conn, "show ip ospf neighbor")
        route = send(conn, "show ip route ospf")
        brief = send(conn, "show ip ospf interface brief")

        verification = (
            "===== show ip ospf neighbor =====\n"
            + neighbor
            + "\n\n===== show ip route ospf =====\n"
            + route
            + "\n\n===== show ip ospf interface brief =====\n"
            + brief
        )

        log(f"\n===== {name} =====\n{verification}")

        # Sauvegarde.
        write_log(
            f"[{name}] copy running-config startup-config"
        )

        save = conn.send_command_timing(
            "copy running-config startup-config",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

        if "destination filename" in save.lower():
            save += conn.send_command_timing(
                "\n",
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )

        log(f"{name} - sauvegarde:\n{save}")

        return verification

    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TP17 — Étape 6 — OSPF multi-area")
        self.resize(950, 720)

        self.checks = {}

        root = QVBoxLayout(self)

        title = QLabel("TP17 — Étape 6 : OSPF multi-area")
        title.setStyleSheet(
            "font-size:25px;font-weight:bold;"
        )
        root.addWidget(title)

        info = QLabel(
            "Area 0 : R1/R2/R3/R4   •   Area 1 : R5   •   Area 2 : R6"
        )
        info.setStyleSheet(
            "color:#00a0d1;font-size:14px;"
        )
        root.addWidget(info)

        group = QGroupBox("Routeurs")
        gl = QVBoxLayout(group)

        labels = {
            "R1": "R1 — Area 0",
            "R2": "R2 — Area 0 / Area 1",
            "R3": "R3 — Area 0 / Area 2",
            "R4": "R4 — Area 0 / Area 2",
            "R5": "R5 — Area 1 + VLAN 10/20",
            "R6": "R6 — Area 2 + VLAN 30/40",
        }

        for name in ROUTERS:
            cb = QCheckBox(labels[name])
            cb.setMinimumHeight(38)
            self.checks[name] = cb
            gl.addWidget(cb)

        root.addWidget(group)

        row = QHBoxLayout()

        all_btn = QPushButton("Tout sélectionner")
        all_btn.clicked.connect(
            lambda: [
                c.setChecked(True)
                for c in self.checks.values()
            ]
        )
        row.addWidget(all_btn)

        none_btn = QPushButton("Tout désélectionner")
        none_btn.clicked.connect(
            lambda: [
                c.setChecked(False)
                for c in self.checks.values()
            ]
        )
        row.addWidget(none_btn)

        root.addLayout(row)

        self.start = QPushButton(
            "Configurer OSPF"
        )
        self.start.clicked.connect(self.run)
        root.addWidget(self.start)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        root.addWidget(self.console)

        self.setStyleSheet("""
            QWidget {
                background:#101820;
                color:#f2f5f7;
            }

            QGroupBox {
                border:1px solid #3a4856;
                border-radius:8px;
                margin-top:8px;
                padding:12px;
                font-weight:bold;
            }

            QCheckBox {
                font-size:15px;
                padding:4px;
            }

            QPlainTextEdit {
                background:#080d12;
                color:#d7e0e8;
                border:1px solid #33404d;
                border-radius:8px;
                font-family:monospace;
                padding:10px;
            }

            QPushButton {
                background:#00a0d1;
                color:white;
                border:none;
                border-radius:7px;
                padding:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#19b3df;
            }

            QPushButton:disabled {
                background:#3d474f;
            }
        """)

    def write_log(self, text):
        self.console.appendPlainText(text)
        log(text)
        QApplication.processEvents()

    def run(self):
        selected = [
            name
            for name, checkbox in self.checks.items()
            if checkbox.isChecked()
        ]

        if not selected:
            QMessageBox.warning(
                self,
                "Aucun routeur",
                "Sélectionne au moins un routeur."
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmation",
            "Configurer OSPF sur :\n\n"
            + ", ".join(selected)
            + "\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.start.setEnabled(False)
        completed = []

        try:
            for name in selected:
                try:
                    self.write_log(
                        f"\n========== {name} =========="
                    )

                    output = configure(
                        name,
                        self.write_log,
                    )

                    completed.append(name)

                    # Validation obligatoire avant le routeur suivant.
                    box = QMessageBox(self)
                    box.setWindowTitle(
                        f"Vérification OSPF — {name}"
                    )
                    box.setIcon(QMessageBox.Information)
                    box.setText(
                        f"{name} configuré.\n\n"
                        "Vérifie les voisinages et les routes, "
                        "puis clique sur OK pour continuer."
                    )
                    box.setDetailedText(output)
                    box.setStandardButtons(QMessageBox.Ok)
                    box.exec()

                except Exception as exc:
                    log(
                        f"ERREUR {name}: {exc}"
                    )

                    QMessageBox.critical(
                        self,
                        "Configuration interrompue",
                        f"Erreur sur {name} :\n\n"
                        f"{exc}\n\n"
                        f"Routeurs terminés : "
                        f"{', '.join(completed) or 'aucun'}"
                    )
                    return

            QMessageBox.information(
                self,
                "Terminé",
                "Configuration OSPF terminée.\n\n"
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
