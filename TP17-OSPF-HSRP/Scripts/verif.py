#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Captures des vérifications

Le script se connecte aux routeurs GNS3 en TELNET, exécute les commandes
de vérification et génère un PNG par routeur et par commande.

Commandes :
    show ip interface brief
    show standby brief
    show ip ospf neighbor
    show ip route ospf
    show ip ospf interface brief

Les captures sont de vraies images PNG de la sortie CLI, pas des fichiers
texte renommés.

Installation :
    pip install netmiko pillow PySide6

Lancement :
    python captures_verification_tp17.py
"""

import sys
import re
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from PIL import Image, ImageDraw, ImageFont
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

COMMANDS = [
    "show ip interface brief",
    "show standby brief",
    "show ip ospf neighbor",
    "show ip route ospf",
    "show ip ospf interface brief",
]

BASE_DIR = Path(__file__).resolve().parent
CAPTURE_DIR = BASE_DIR / "captures"
LOG_DIR = BASE_DIR / "logs"
CAPTURE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"captures_{datetime.now():%Y%m%d_%H%M%S}.log"

CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 30
BANNER_TIMEOUT = 60
READ_TIMEOUT = 45


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {message}\n")


def safe_name(command):
    return re.sub(r"[^a-zA-Z0-9]+", "_", command).strip("_")


def get_font(size=18):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def save_png(router, command, output):
    font = get_font(18)
    title_font = get_font(22)

    lines = output.replace("\r", "").splitlines()
    if not lines:
        lines = ["<aucune sortie>"]

    # Largeur suffisante pour les lignes CLI.
    max_chars = max(len(line) for line in lines)
    width = max(1100, min(2400, 20 + max_chars * 11))
    line_height = 27
    header_height = 75
    height = header_height + max(1, len(lines)) * line_height + 25

    image = Image.new("RGB", (width, height), "#080d12")
    draw = ImageDraw.Draw(image)

    draw.text(
        (20, 15),
        f"{router}  |  {command}",
        font=title_font,
        fill="#00a0d1",
    )

    y = header_height

    for line in lines:
        draw.text(
            (20, y),
            line,
            font=font,
            fill="#e6edf3",
        )
        y += line_height

    filename = (
        CAPTURE_DIR
        / f"{router}_{safe_name(command)}.png"
    )

    image.save(filename)
    return filename


def connect_router(router):
    return ConnectHandler(
        device_type="cisco_ios_telnet",
        host=HOST,
        port=ROUTERS[router],
        username="",
        password="",
        secret="",
        conn_timeout=CONNECT_TIMEOUT,
        auth_timeout=AUTH_TIMEOUT,
        banner_timeout=BANNER_TIMEOUT,
        fast_cli=False,
    )


def capture_router(router, write_log):
    conn = None
    files = []

    try:
        write_log(
            f"[{router}] Connexion Telnet "
            f"localhost:{ROUTERS[router]}"
        )

        conn = connect_router(router)

        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception:
            conn.enable()

        write_log(f"[{router}] Mode privilégié OK")

        for command in COMMANDS:
            write_log(f"[{router}] {command}")

            output = conn.send_command(
                command,
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )

            filename = save_png(
                router,
                command,
                output,
            )

            files.append(filename)

            log(
                f"{router} | {command} | {filename}\n"
                f"{output}\n"
            )

            write_log(
                f"[{router}] PNG créé : {filename.name}"
            )

        return files

    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "TP17 — Captures des vérifications"
        )
        self.resize(900, 700)

        self.checks = {}

        root = QVBoxLayout(self)

        title = QLabel(
            "TP17 — Captures des vérifications"
        )
        title.setStyleSheet(
            "font-size:25px;font-weight:bold;"
        )
        root.addWidget(title)

        info = QLabel(
            "Telnet GNS3 • 5 commandes • PNG "
            "par routeur et par commande"
        )
        info.setStyleSheet(
            "color:#00a0d1;font-size:14px;"
        )
        root.addWidget(info)

        group = QGroupBox("Routeurs")
        gl = QVBoxLayout(group)

        for router, port in ROUTERS.items():
            cb = QCheckBox(
                f"{router} — Telnet localhost:{port}"
            )
            cb.setMinimumHeight(38)
            self.checks[router] = cb
            gl.addWidget(cb)

        root.addWidget(group)

        row = QHBoxLayout()

        all_btn = QPushButton(
            "Tout sélectionner"
        )
        all_btn.clicked.connect(
            lambda: [
                c.setChecked(True)
                for c in self.checks.values()
            ]
        )
        row.addWidget(all_btn)

        none_btn = QPushButton(
            "Tout désélectionner"
        )
        none_btn.clicked.connect(
            lambda: [
                c.setChecked(False)
                for c in self.checks.values()
            ]
        )
        row.addWidget(none_btn)

        root.addLayout(row)

        self.start = QPushButton(
            "Lancer les captures"
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
            router
            for router, checkbox in self.checks.items()
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
            "Créer les captures pour :\n\n"
            + ", ".join(selected)
            + "\n\n"
            "5 captures PNG seront créées par routeur.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.start.setEnabled(False)

        total = 0
        completed = []

        try:
            for router in selected:
                try:
                    self.write_log(
                        f"\n========== {router} =========="
                    )

                    files = capture_router(
                        router,
                        self.write_log,
                    )

                    total += len(files)
                    completed.append(router)

                    QMessageBox.information(
                        self,
                        f"Captures — {router}",
                        f"{len(files)} captures PNG créées pour "
                        f"{router}.\n\n"
                        "Clique sur OK pour passer au routeur suivant."
                    )

                except Exception as exc:
                    log(
                        f"ERREUR {router}: {exc}"
                    )

                    QMessageBox.critical(
                        self,
                        "Capture interrompue",
                        f"Erreur sur {router} :\n\n"
                        f"{exc}\n\n"
                        f"Routeurs terminés : "
                        f"{', '.join(completed) or 'aucun'}"
                    )
                    return

            QMessageBox.information(
                self,
                "Terminé",
                f"Captures terminées.\n\n"
                f"Routeurs : {', '.join(completed)}\n"
                f"PNG créés : {total}\n\n"
                f"Dossier : {CAPTURE_DIR}\n"
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
