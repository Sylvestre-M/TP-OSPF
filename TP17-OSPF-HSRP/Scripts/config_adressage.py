#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Adressage des routeurs et switchs GNS3.

- PySide6 : interface sombre.
- Sélection libre des équipements.
- Connexions Telnet internes au script : aucun champ/option Telnet dans l'interface.
- Configure hostname + no ip domain lookup sur les routeurs/switchs.
- Configure les adresses IP indiquées par la topologie sur R1..R6.
- Après chaque équipement : show ip interface brief.
- La sortie est affichée dans une boîte de dialogue et l'utilisateur
  doit cliquer sur OK avant de passer au suivant.
- Journal dans logs/.

Installation :
    pip install netmiko PySide6

Lancement :
    python3 configure_tp17_addressing.py
"""

import sys
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)

HOST = "127.0.0.1"

# Ports GNS3 issus de la capture fournie.
# Ils sont utilisés uniquement en interne : pas d'option Telnet affichée.
DEVICES = {
    "R1": {"port": 5000, "type": "routeur"},
    "R2": {"port": 5001, "type": "routeur"},
    "R3": {"port": 5002, "type": "routeur"},
    "R4": {"port": 5003, "type": "routeur"},
    "R5": {"port": 5004, "type": "routeur"},
    "R6": {"port": 5005, "type": "routeur"},
    "S1": {"port": 5006, "type": "switch"},
    "S2": {"port": 5007, "type": "switch"},
    "S3": {"port": 5008, "type": "switch"},
    "S4": {"port": 5009, "type": "switch"},
}

# Adressage lu sur la topologie TP17.
ROUTER_INTERFACES = {
    "R1": {
        "e0/0": ("10.0.0.1", "255.255.255.252"),
        "e0/1": ("10.0.2.2", "255.255.255.252"),
        "e0/2": ("10.0.6.1", "255.255.255.252"),
        "e0/3": ("10.0.4.1", "255.255.255.252"),
    },
    "R2": {
        "e0/0": ("10.0.7.1", "255.255.255.252"),
        "e0/1": ("10.0.1.1", "255.255.255.252"),
        "e0/2": ("10.0.2.1", "255.255.255.252"),
        "e0/3": ("10.0.5.1", "255.255.255.252"),
    },
    "R3": {
        "e0/0": ("10.0.0.2", "255.255.255.252"),
        "e0/1": ("10.0.3.2", "255.255.255.252"),
        "e0/2": ("10.0.9.1", "255.255.255.252"),
        "e0/3": ("10.0.5.2", "255.255.255.252"),
    },
    "R4": {
        "e0/0": ("10.0.3.1", "255.255.255.252"),
        "e0/1": ("10.0.1.2", "255.255.255.252"),
        "e0/2": ("10.0.8.1", "255.255.255.252"),
        "e0/3": ("10.0.4.2", "255.255.255.252"),
    },
    "R5": {
        "e0/0": ("10.0.6.2", "255.255.255.252"),
        "e0/1": ("10.0.7.2", "255.255.255.252"),
        "e0/2": ("192.168.10.254", "255.255.255.0"),
        "e0/3": ("192.168.20.254", "255.255.255.0"),
    },
    "R6": {
        "e0/0": ("10.0.9.2", "255.255.255.252"),
        "e0/1": ("10.0.8.2", "255.255.255.252"),
        "e0/2": ("192.168.30.254", "255.255.255.0"),
        "e0/3": ("192.168.40.254", "255.255.255.0"),
    },
}

CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 30
BANNER_TIMEOUT = 60
READ_TIMEOUT = 45

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"tp17_addressing_{datetime.now():%Y%m%d_%H%M%S}.log"


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {message}\n")


def connect_device(name):
    d = DEVICES[name]
    return ConnectHandler(
        device_type="cisco_ios_telnet",
        host=HOST,
        port=d["port"],
        username="",
        password="",
        secret="",
        conn_timeout=CONNECT_TIMEOUT,
        auth_timeout=AUTH_TIMEOUT,
        banner_timeout=BANNER_TIMEOUT,
        fast_cli=False,
    )


def enter_enable(connection):
    try:
        if not connection.check_enable_mode():
            connection.enable()
    except Exception:
        connection.enable()


def configure_device(name, ui_log):
    connection = None
    try:
        ui_log(f"[{name}] Connexion...")
        connection = connect_device(name)
        ui_log(f"[{name}] Connexion OK.")

        enter_enable(connection)
        ui_log(f"[{name}] Mode privilégié OK.")

        commands = [
            "configure terminal",
            f"hostname {name}",
            "no ip domain lookup",
        ]

        # Les switchs n'ont aucune adresse de management indiquée
        # sur la topologie : aucune IP n'est inventée pour S1..S4.
        if name in ROUTER_INTERFACES:
            for interface, (ip, mask) in ROUTER_INTERFACES[name].items():
                commands += [
                    f"interface {interface}",
                    f"ip address {ip} {mask}",
                    "no shutdown",
                    "exit",
                ]

        commands.append("end")

        for command in commands:
            ui_log(f"[{name}] {command}")
            output = connection.send_command_timing(
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

        ui_log(f"[{name}] show ip interface brief")
        verification = connection.send_command_timing(
            "show ip interface brief",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )
        log(f"{name} - show ip interface brief:\n{verification}")
        return verification

    finally:
        if connection is not None:
            try:
                connection.disconnect()
            except Exception:
                pass


class VerificationDialog(QMessageBox):
    def __init__(self, parent, name, output):
        super().__init__(parent)
        self.setWindowTitle(f"Vérification — {name}")
        self.setIcon(QMessageBox.Information)
        self.setText(
            f"{name} configuré.\n\n"
            "Vérifie la sortie puis clique sur OK pour continuer."
        )
        self.setDetailedText(output)
        self.setStandardButtons(QMessageBox.Ok)
        self.setMinimumSize(700, 500)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP17 — Configuration de l'adressage")
        self.resize(900, 720)
        self.checkboxes = {}

        root = QVBoxLayout(self)

        title = QLabel("TP17 — Configuration de l'adressage")
        title.setStyleSheet("font-size: 25px; font-weight: bold;")
        root.addWidget(title)

        subtitle = QLabel(
            "Sélectionne un ou plusieurs routeurs/switchs. "
            "Après chaque équipement, valide show ip interface brief."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #00a0d1; font-size: 14px;")
        root.addWidget(subtitle)

        actions = QHBoxLayout()
        select_all = QPushButton("Tout sélectionner")
        select_all.clicked.connect(self.select_all)
        actions.addWidget(select_all)

        clear_all = QPushButton("Tout désélectionner")
        clear_all.clicked.connect(self.clear_all)
        actions.addWidget(clear_all)
        root.addLayout(actions)

        group = QGroupBox("Équipements de la topologie")
        group_layout = QVBoxLayout(group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        device_layout = QVBoxLayout(container)

        for name, data in DEVICES.items():
            cb = QCheckBox(f"{name}   —   {data['type'].capitalize()}")
            cb.setMinimumHeight(38)
            self.checkboxes[name] = cb
            device_layout.addWidget(cb)

        device_layout.addStretch()
        scroll.setWidget(container)
        group_layout.addWidget(scroll)
        root.addWidget(group)

        self.start_button = QPushButton(
            "Configurer les équipements sélectionnés"
        )
        self.start_button.clicked.connect(self.start_configuration)
        root.addWidget(self.start_button)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        root.addWidget(self.console)

        self.setStyleSheet("""
            QWidget { background:#101820; color:#f2f5f7; }
            QGroupBox {
                border:1px solid #3a4856; border-radius:8px;
                margin-top:8px; padding:12px; font-weight:bold;
            }
            QCheckBox { color:#f2f5f7; font-size:15px; padding:4px; }
            QPlainTextEdit {
                background:#080d12; color:#d7e0e8;
                border:1px solid #33404d; border-radius:8px;
                padding:10px; font-family:monospace;
            }
            QPushButton {
                background:#00a0d1; color:white; border:none;
                border-radius:7px; padding:12px; font-weight:bold;
            }
            QPushButton:hover { background:#19b3df; }
            QPushButton:disabled { background:#3d474f; }
        """)

    def ui_log(self, message):
        self.console.appendPlainText(message)
        log(message)
        QApplication.processEvents()

    def select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def clear_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def selected_devices(self):
        return [name for name, cb in self.checkboxes.items() if cb.isChecked()]

    def start_configuration(self):
        selected = self.selected_devices()
        if not selected:
            QMessageBox.warning(
                self, "Aucun équipement",
                "Sélectionne au moins un routeur ou un switch."
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmer",
            "Équipements sélectionnés :\n\n"
            + ", ".join(selected)
            + "\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.start_button.setEnabled(False)
        success = []

        try:
            for name in selected:
                self.ui_log("")
                self.ui_log(f"========== {name} ==========")
                try:
                    verification = configure_device(name, self.ui_log)
                    success.append(name)

                    # Bloquant : l'utilisateur doit valider avant de continuer.
                    VerificationDialog(self, name, verification).exec()

                except Exception as exc:
                    self.ui_log(f"[{name}] ERREUR : {exc}")
                    QMessageBox.critical(
                        self,
                        "Configuration interrompue",
                        f"Erreur pendant la configuration de {name}.\n\n"
                        f"{exc}\n\n"
                        f"Équipements terminés : "
                        f"{', '.join(success) or 'aucun'}",
                    )
                    return

            QMessageBox.information(
                self,
                "Configuration terminée",
                "Configuration terminée.\n\n"
                f"Équipements configurés : {', '.join(success)}\n\n"
                f"Journal :\n{LOG_FILE}",
            )
        finally:
            self.start_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
