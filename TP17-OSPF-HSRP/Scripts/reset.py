#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP17 - Réinitialisation complète des routeurs et switchs GNS3.

Équipements pris en compte d'après la topologie fournie :
    R1 -> telnet localhost:5000
    R2 -> telnet localhost:5001
    R3 -> telnet localhost:5002
    R4 -> telnet localhost:5003
    R5 -> telnet localhost:5004
    R6 -> telnet localhost:5005
    S1 -> telnet localhost:5006
    S2 -> telnet localhost:5007
    S3 -> telnet localhost:5008
    S4 -> telnet localhost:5009

Comportement :
    1. Connexion Telnet à chaque équipement.
    2. Passage en mode privilégié.
    3. Exécution de "erase startup-config".
    4. Confirmation automatique si IOS demande [confirm].
    5. Exécution de "reload".
    6. Réponse "no" à :
           System configuration has been modified. Save? [yes/no]:
    7. Réponse "no" à :
           Would you like to enter the initial configuration dialog? [yes/no]:
    8. Attente longue du redémarrage.
    9. Reconnexion pour vérifier que l'équipement répond.
   10. Au moindre équipement non joignable, arrêt immédiat et boîte de dialogue.
   11. À la fin, boîte de dialogue de confirmation.

Dépendances :
    pip install netmiko PySide6
"""

import sys
import time
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


HOST = "127.0.0.1"

# D'après la capture GNS3 fournie.
DEVICES = [
    ("R1", 5000, "routeur"),
    ("R2", 5001, "routeur"),
    ("R3", 5002, "routeur"),
    ("R4", 5003, "routeur"),
    ("R5", 5004, "routeur"),
    ("R6", 5005, "routeur"),
    ("S1", 5006, "switch"),
    ("S2", 5007, "switch"),
    ("S3", 5008, "switch"),
    ("S4", 5009, "switch"),
]

# Valeurs volontairement élevées pour les consoles GNS3 lentes.
CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 30
BANNER_TIMEOUT = 60
READ_TIMEOUT = 45

# Après reload, IOS peut prendre du temps à redémarrer.
RELOAD_WAIT = 45
RECONNECT_ATTEMPTS = 12
RECONNECT_DELAY = 5

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / (
    f"reset_tp17_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)


def log_write(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def make_connection(port: int):
    """
    Connexion Telnet Cisco.
    On utilise un compte vide afin de fonctionner aussi avec
    les consoles GNS3 sans authentification.
    """
    return ConnectHandler(
        device_type="cisco_ios_telnet",
        host=HOST,
        port=port,
        username="",
        password="",
        secret="",
        conn_timeout=CONNECT_TIMEOUT,
        auth_timeout=AUTH_TIMEOUT,
        banner_timeout=BANNER_TIMEOUT,
        fast_cli=False,
    )


def process_events():
    QApplication.processEvents()


def send_with_confirm(connection, command: str):
    """
    Exécute une commande sans dépendre d'un prompt du type Router#.
    C'est important car le hostname peut avoir déjà été modifié.
    """
    output = connection.send_command_timing(
        command,
        read_timeout=READ_TIMEOUT,
        strip_prompt=False,
        strip_command=False,
    )

    lower = output.lower()

    if "[confirm]" in lower or "proceed with reload" in lower:
        output += connection.send_command_timing(
            "\n",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

    return output


def erase_startup_config(connection):
    output = send_with_confirm(
        connection,
        "erase startup-config",
    )

    # Certaines versions IOS affichent une confirmation différente.
    lower = output.lower()

    if (
        "[confirm]" in lower
        or "erase of nvram" in lower
        or "confirm" in lower
    ):
        output += connection.send_command_timing(
            "\n",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

    return output


def reload_device(connection):
    """
    Lance reload et répond explicitement 'no' au message
    de sauvegarde de configuration.

    On envoie ensuite 'no' à l'assistant initial IOS.
    """
    output = connection.send_command_timing(
        "reload",
        read_timeout=READ_TIMEOUT,
        strip_prompt=False,
        strip_command=False,
    )

    # Le point critique demandé :
    # "System configuration has been modified. Save? [yes/no]:"
    lower = output.lower()

    if (
        "system configuration has been modified" in lower
        or "save?" in lower
        or "[yes/no]" in lower
    ):
        output += connection.send_command_timing(
            "no",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

    # Certaines images IOS demandent ensuite une confirmation du reload.
    lower = output.lower()
    if "[confirm]" in lower or "proceed with reload" in lower:
        output += connection.send_command_timing(
            "\n",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

    # La session va normalement se fermer pendant le redémarrage.
    # On tente explicitement "no" si l'assistant initial apparaît
    # avant la coupure de session.
    lower = output.lower()
    if (
        "initial configuration dialog" in lower
        or "would you like to enter" in lower
        or "auto install" in lower
        or "autoinstall" in lower
    ):
        output += connection.send_command_timing(
            "no",
            read_timeout=READ_TIMEOUT,
            strip_prompt=False,
            strip_command=False,
        )

    return output


def reconnect_after_reload(name: str, port: int):
    """
    Attend le redémarrage puis vérifie que l'équipement répond.
    """
    time.sleep(RELOAD_WAIT)

    last_error = None

    for attempt in range(1, RECONNECT_ATTEMPTS + 1):
        process_events()
        log_write(
            f"{name}: tentative de reconnexion "
            f"{attempt}/{RECONNECT_ATTEMPTS}"
        )

        connection = None

        try:
            connection = make_connection(port)

            # On récupère simplement la réponse IOS sans exiger
            # un hostname particulier.
            output = connection.send_command_timing(
                "\n",
                read_timeout=READ_TIMEOUT,
                strip_prompt=False,
                strip_command=False,
            )

            lower = output.lower()

            # Si l'auto-install apparaît après le reboot, on répond no.
            if (
                "initial configuration dialog" in lower
                or "would you like to enter" in lower
                or "auto install" in lower
                or "autoinstall" in lower
            ):
                output += connection.send_command_timing(
                    "no",
                    read_timeout=READ_TIMEOUT,
                    strip_prompt=False,
                    strip_command=False,
                )

            # Passage privilégié.
            try:
                connection.enable()
            except Exception:
                pass

            log_write(f"{name}: reconnexion réussie.")
            return connection

        except Exception as exc:
            last_error = exc
            log_write(
                f"{name}: reconnexion échouée : {exc}"
            )

            if connection is not None:
                try:
                    connection.disconnect()
                except Exception:
                    pass

            if attempt < RECONNECT_ATTEMPTS:
                time.sleep(RECONNECT_DELAY)

    raise RuntimeError(
        f"{name} ne répond pas après le redémarrage. "
        f"Dernière erreur : {last_error}"
    )


def reset_one(name: str, port: int, kind: str, ui_log):
    connection = None

    try:
        ui_log(
            f"[{name}] Connexion Telnet "
            f"{HOST}:{port} ({kind})..."
        )

        connection = make_connection(port)

        ui_log(f"[{name}] Connexion OK.")

        # On tente le mode privilégié sans supposer le hostname.
        try:
            if not connection.check_enable_mode():
                connection.enable()
        except Exception:
            try:
                connection.enable()
            except Exception:
                pass

        ui_log(f"[{name}] erase startup-config")
        erase_output = erase_startup_config(connection)
        log_write(f"{name} erase output:\n{erase_output}")

        ui_log(f"[{name}] Configuration startup effacée.")

        ui_log(f"[{name}] reload...")
        reload_output = reload_device(connection)
        log_write(f"{name} reload output:\n{reload_output}")

        try:
            connection.disconnect()
        except Exception:
            pass
        connection = None

        ui_log(
            f"[{name}] Redémarrage en cours. "
            f"Attente {RELOAD_WAIT} secondes..."
        )

        process_events()

        new_connection = reconnect_after_reload(name, port)

        try:
            new_connection.disconnect()
        except Exception:
            pass

        ui_log(f"[{name}] Réinitialisation terminée.")
        log_write(f"{name}: RESET OK")

    except Exception as exc:
        log_write(f"{name}: RESET FAILED: {exc}")

        if connection is not None:
            try:
                connection.disconnect()
            except Exception:
                pass

        raise RuntimeError(
            f"Le routeur/switch {name} ne répond pas.\n\n"
            f"L'opération est arrêtée immédiatement.\n\n"
            f"Erreur : {exc}"
        ) from exc


class ResetWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "TP17 — Réinitialisation GNS3"
        )
        self.resize(820, 620)

        layout = QVBoxLayout(self)

        title = QLabel(
            "TP17 — Réinitialisation des routeurs et switchs"
        )
        title.setStyleSheet(
            "font-size: 23px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "erase startup-config → reload → no → "
            "vérification après redémarrage"
        )
        subtitle.setStyleSheet(
            "color: #00a0d1; font-size: 14px;"
        )
        layout.addWidget(subtitle)

        self.run_button = QPushButton(
            "Réinitialiser tous les équipements"
        )
        self.run_button.clicked.connect(self.start_reset)
        layout.addWidget(self.run_button)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        self.setStyleSheet("""
            QWidget {
                background: #101820;
                color: #f2f5f7;
            }

            QPlainTextEdit {
                background: #080d12;
                color: #d7e0e8;
                border: 1px solid #33404d;
                border-radius: 8px;
                padding: 10px;
                font-family: monospace;
                font-size: 13px;
            }

            QPushButton {
                background: #00a0d1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 13px;
                font-weight: bold;
                font-size: 14px;
            }

            QPushButton:hover {
                background: #19b3df;
            }

            QPushButton:disabled {
                background: #3b454e;
            }
        """)

    def ui_log(self, message):
        self.console.appendPlainText(message)
        log_write(message)
        process_events()

    def start_reset(self):
        self.run_button.setEnabled(False)
        self.console.clear()

        self.ui_log(
            "=== TP17 : RESET COMPLET ==="
        )
        self.ui_log(
            f"Journal : {LOG_FILE}"
        )
        self.ui_log(
            "Si un équipement ne répond pas, "
            "le traitement s'arrête immédiatement."
        )

        completed = []

        try:
            for name, port, kind in DEVICES:
                self.ui_log("")
                self.ui_log(
                    f"--- {name} ({kind}) ---"
                )

                try:
                    reset_one(
                        name,
                        port,
                        kind,
                        self.ui_log,
                    )
                    completed.append(name)

                except Exception as exc:
                    self.ui_log(
                        f"ERREUR BLOQUANTE : {exc}"
                    )

                    QMessageBox.critical(
                        self,
                        "Configuration interrompue",
                        f"L'opération s'arrête à cause de "
                        f"l'équipement {name}.\n\n"
                        f"{exc}\n\n"
                        f"Équipements terminés : "
                        f"{', '.join(completed) or 'aucun'}",
                    )

                    self.run_button.setEnabled(True)
                    return

            self.ui_log("")
            self.ui_log(
                "=== TOUS LES ÉQUIPEMENTS SONT RÉINITIALISÉS ==="
            )

            QMessageBox.information(
                self,
                "Réinitialisation terminée",
                "Réinitialisation terminée.\n\n"
                "Tous les routeurs et switchs ont répondu "
                "après leur redémarrage.\n\n"
                f"Équipements traités : {len(completed)}\n"
                f"Journal :\n{LOG_FILE}",
            )

        finally:
            self.run_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)

    window = ResetWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
