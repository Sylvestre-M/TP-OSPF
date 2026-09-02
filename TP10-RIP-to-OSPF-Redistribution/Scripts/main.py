#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP10 - Redistribution OSPF -> RIP
Version simple

ASBR GNS3 :
    Telnet 127.0.0.1:5015

Configuration :
    router rip
     version 2
     no auto-summary
     redistribute ospf 1 metric 2

Puis :
    copy running-config startup-config
    show ip protocols
    show ip route rip

Installation :
    pip install netmiko PySide6
"""

import sys
from pathlib import Path

from netmiko import ConnectHandler
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "redistribution_ospf_to_rip.log"


class CredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identifiants Cisco")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel("Connexion ASBR")
        title.setStyleSheet(
            "font-size:20px; font-weight:bold;"
        )
        layout.addWidget(title)

        form = QFormLayout()

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username IOS")
        form.addRow("Username :", self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Password :", self.password)

        self.secret = QLineEdit()
        self.secret.setEchoMode(QLineEdit.Password)
        self.secret.setPlaceholderText(
            "Vide = même valeur que Password"
        )
        form.addRow("Enable secret :", self.secret)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_credentials(self):
        username = self.username.text().strip()
        password = self.password.text()
        secret = self.secret.text() or password

        return username, password, secret


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "TP10 - Redistribution OSPF vers RIP - ASBR"
        )
        self.resize(850, 600)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        title = QLabel(
            "TP10 — Redistribution OSPF → RIP"
        )
        title.setStyleSheet(
            "font-size:24px; font-weight:bold;"
        )
        layout.addWidget(title)

        info = QLabel(
            "ASBR : 127.0.0.1:5015\n"
            "Configuration de la redistribution OSPF vers RIP uniquement."
        )
        info.setStyleSheet(
            "color:#b8c2cc; font-size:14px;"
        )
        layout.addWidget(info)

        self.button = QPushButton(
            "Configurer l'ASBR"
        )
        self.button.clicked.connect(
            self.configure_asbr
        )
        layout.addWidget(self.button)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Sortie Cisco..."
        )
        layout.addWidget(self.output)

    def log(self, text):
        self.output.appendPlainText(text)

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8",
        ) as logfile:
            logfile.write(text + "\n")

    def configure_asbr(self):
        credentials = CredentialsDialog(self)

        if credentials.exec() != QDialog.Accepted:
            return

        username, password, secret = (
            credentials.get_credentials()
        )

        self.button.setEnabled(False)
        self.output.clear()

        connection = None

        try:
            self.log(
                "========================================"
            )
            self.log(
                "Connexion à ASBR — 127.0.0.1:5015"
            )

            device = {
                "device_type": "cisco_ios_telnet",
                "host": "127.0.0.1",
                "port": 5015,
                "username": username or None,
                "password": password,
                "secret": secret,
                "conn_timeout": 20,
                "banner_timeout": 60,
                "auth_timeout": 30,
                "fast_cli": False,
            }

            connection = ConnectHandler(**device)

            self.log("Connexion réussie.")

            # Toujours revenir en mode privilégié.
            try:
                if not connection.check_enable_mode():
                    connection.enable()
            except Exception:
                connection.enable()

            self.log("Mode privilégié confirmé.")

            # Configuration.
            commands = [
                "router rip",
                "version 2",
                "no auto-summary",
                "redistribute ospf 1 metric 2",
            ]

            self.log(
                "\n--- Configuration OSPF -> RIP ---"
            )

            result = connection.send_config_set(
                commands,
                cmd_verify=False,
                read_timeout=30,
            )

            self.log(result)

            connection.send_command_timing("end")

            # Sauvegarde.
            self.log(
                "\n--- Sauvegarde startup-config ---"
            )

            save = connection.send_command_timing(
                "copy running-config startup-config",
                read_timeout=30,
            )

            self.log(save)

            # Si IOS demande le nom du fichier.
            if "destination filename" in save.lower():
                save2 = connection.send_command_timing(
                    "",
                    read_timeout=30,
                )
                self.log(save2)
                save += save2

            # Si IOS demande confirmation.
            if "overwrite" in save.lower():
                save3 = connection.send_command_timing(
                    "yes",
                    read_timeout=30,
                )
                self.log(save3)

            # Vérifications.
            self.log(
                "\n--- show ip protocols ---"
            )
            protocols = connection.send_command_timing(
                "show ip protocols",
                read_timeout=30,
            )
            self.log(protocols)

            self.log(
                "\n--- show ip route rip ---"
            )
            routes = connection.send_command_timing(
                "show ip route rip",
                read_timeout=30,
            )
            self.log(routes)

            QMessageBox.information(
                self,
                "Terminé",
                "La redistribution OSPF → RIP a été "
                "configurée sur l'ASBR et sauvegardée.",
            )

        except Exception as error:
            self.log(
                "\nERREUR :\n" + str(error)
            )

            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )

        finally:
            if connection is not None:
                try:
                    connection.disconnect()
                except Exception:
                    pass

            self.button.setEnabled(True)


def apply_style(app):
    app.setStyleSheet("""
        QWidget {
            background: #101820;
            color: #f2f5f7;
            font-size: 14px;
        }

        QLineEdit, QPlainTextEdit {
            background: #0d141b;
            color: #f2f5f7;
            border: 1px solid #3a4856;
            border-radius: 7px;
            padding: 8px;
        }

        QPushButton {
            background: #00a0d1;
            color: white;
            border: none;
            border-radius: 7px;
            padding: 12px;
            font-weight: bold;
        }

        QPushButton:hover {
            background: #19b3df;
        }

        QPushButton:disabled {
            background: #39444e;
        }

        QDialog {
            background: #101820;
        }
    """)


def main():
    app = QApplication(sys.argv)
    apply_style(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
