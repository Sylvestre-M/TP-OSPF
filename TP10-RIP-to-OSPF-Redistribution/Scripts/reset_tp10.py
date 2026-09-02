#!/usr/bin/env python3
"""
TP10 - Réinitialisation automatisée des routeurs GNS3

Fonctions :
- Interface graphique moderne avec PySide6
- Connexion Telnet aux 9 routeurs
- Passage en mode privilégié
- Effacement de la startup-config
- Gestion automatique du prompt :
      System configuration has been modified. Save? [yes/no]:
  -> no
- Gestion automatique des confirmations de reload
- Réponse automatique "no" à l'Initial Configuration Dialog
- Attente du redémarrage IOS
- Vérification finale
- Journalisation dans logs/reset_tp10.log

Topologie TP10 :
ASBR, R1, R2, R3, R4, R5, R6, R8, R9
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QMessageBox,
    QGroupBox,
)


# ============================================================
# CHEMINS
# ============================================================

PROJECT_DIR = Path(
    "/home/sylvestre-mouafo/Documents/Labs/"
    "TP10-Route-Redistribution"
)

LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "reset_tp10.log"


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("TP10-RESET")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
    )
    logger.addHandler(handler)


# ============================================================
# ROUTEURS / PORTS GNS3
# ============================================================

ROUTERS = {
    "R1": 5009,
    "R2": 5010,
    "R3": 5011,
    "R4": 5012,
    "R5": 5013,
    "R6": 5014,
    "ASBR": 5015,
    "R8": 5016,
    "R9": 5017,
}

HOST = "127.0.0.1"

# Si GNS3 demande des identifiants, renseigne-les ici.
USERNAME = ""
PASSWORD = ""
SECRET = ""


# ============================================================
# PARAMÈTRES
# ============================================================

# Délais volontairement larges pour laisser GNS3 / IOS redémarrer.
CONNECT_TIMEOUT = 60
REBOOT_WAIT = 30
RECONNECT_ATTEMPTS = 18
RECONNECT_DELAY = 8


# ============================================================
# WORKER
# ============================================================

class ResetWorker(QObject):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def log(self, message, level="INFO"):
        line = f"[{level}] {message}"
        logger.info(message)
        self.log_signal.emit(line)

    def connect_router(self, name, port):
        device = {
            "device_type": "cisco_ios_telnet",
            "host": HOST,
            "port": port,
            "username": USERNAME,
            "password": PASSWORD,
            "secret": SECRET,
            "timeout": CONNECT_TIMEOUT,
            "conn_timeout": CONNECT_TIMEOUT,
            "auth_timeout": CONNECT_TIMEOUT,
            "banner_timeout": CONNECT_TIMEOUT,
            "fast_cli": False,
        }

        self.log(
            f"{name}: connexion Telnet "
            f"{HOST}:{port}"
        )

        connection = ConnectHandler(**device)

        # Passage explicite en mode privilégié.
        if not connection.check_enable_mode():
            self.log(
                f"{name}: passage en mode privilégié"
            )
            connection.enable()

        if not connection.check_enable_mode():
            raise RuntimeError(
                f"{name}: impossible d'obtenir le privilège 15"
            )

        self.log(
            f"{name}: mode privilégié OK"
        )

        return connection

    @staticmethod
    def contains(text, *patterns):
        lowered = text.lower()
        return any(
            pattern.lower() in lowered
            for pattern in patterns
        )

    def handle_boot_dialog(self, connection, name):
        """
        Gère les dialogues IOS après le redémarrage.

        Important :
        - Initial Configuration Dialog -> no
        - Auto-install / setup -> no
        - Press RETURN -> Entrée
        """

        self.log(
            f"{name}: traitement du démarrage IOS"
        )

        for _ in range(10):
            output = connection.send_command_timing(
                "",
                strip_prompt=False,
                strip_command=False,
                read_timeout=10,
            )

            if not output:
                time.sleep(1)
                continue

            self.log(
                f"{name}: {output[-500:].strip()}"
            )

            # Initial Configuration Dialog
            if self.contains(
                output,
                "Would you like to enter the initial configuration dialog",
                "initial configuration dialog",
            ):
                self.log(
                    f"{name}: réponse automatique -> no"
                )
                output = connection.send_command_timing(
                    "no",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=15,
                )

                self.log(
                    f"{name}: Initial Configuration Dialog refusé"
                )
                continue

            # AutoInstall / setup dialog
            if self.contains(
                output,
                "Would you like to terminate autoinstall",
                "terminate autoinstall",
                "autoinstall",
                "AutoInstall",
            ):
                self.log(
                    f"{name}: AutoInstall détecté -> no"
                )
                connection.send_command_timing(
                    "no",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=15,
                )
                continue

            # Prompt "Press RETURN to get started!"
            if self.contains(
                output,
                "Press RETURN to get started",
                "Press RETURN",
            ):
                self.log(
                    f"{name}: envoi de RETURN"
                )
                connection.send_command_timing(
                    "\n",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=10,
                )
                continue

            # Si on retrouve le prompt privilégié, le boot est terminé.
            if "#" in output:
                return True

            time.sleep(1)

        # Dernier essai pour obtenir le prompt.
        output = connection.send_command_timing(
            "\n",
            strip_prompt=False,
            strip_command=False,
            read_timeout=10,
        )

        return "#" in output

    def reset_router(self, name, port):
        connection = None

        try:
            connection = self.connect_router(
                name,
                port,
            )

            # ------------------------------------------------
            # Effacement startup-config
            # ------------------------------------------------
            self.log(
                f"{name}: effacement de la startup-config"
            )

            output = connection.send_command_timing(
                "erase startup-config",
                strip_prompt=False,
                strip_command=False,
                read_timeout=60,
            )

            self.log(
                f"{name}: réponse write erase : "
                f"{output[-500:].strip()}"
            )

            # IOS peut demander [confirm].
            if self.contains(
                output,
                "[confirm]",
                "continue?",
                "continue",
            ):
                self.log(
                    f"{name}: confirmation effacement -> RETURN"
                )
                output += connection.send_command_timing(
                    "\n",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=60,
                )

            # ------------------------------------------------
            # Reload
            # ------------------------------------------------
            self.log(
                f"{name}: reload"
            )

            output = connection.send_command_timing(
                "reload",
                strip_prompt=False,
                strip_command=False,
                read_timeout=60,
            )

            self.log(
                f"{name}: réponse reload : "
                f"{output[-700:].strip()}"
            )

            # Cas explicitement demandé :
            # System configuration has been modified. Save? [yes/no]:
            if self.contains(
                output,
                "System configuration has been modified",
                "Save? [yes/no]",
            ):
                self.log(
                    f"{name}: configuration modifiée -> réponse no"
                )
                output = connection.send_command_timing(
                    "no",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=60,
                )

            # Certaines images IOS demandent :
            # Proceed with reload? [confirm]
            if self.contains(
                output,
                "Proceed with reload",
                "[confirm]",
                "proceed with reload",
            ):
                self.log(
                    f"{name}: confirmation reload -> RETURN"
                )
                connection.send_command_timing(
                    "\n",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=60,
                )

            self.log(
                f"{name}: redémarrage lancé"
            )

            # La session Telnet va normalement se fermer.
            try:
                connection.disconnect()
            except Exception:
                pass

            connection = None

            # ------------------------------------------------
            # Attente du boot
            # ------------------------------------------------
            self.log(
                f"{name}: attente du redémarrage IOS "
                f"({REBOOT_WAIT}s)"
            )

            time.sleep(REBOOT_WAIT)

            # ------------------------------------------------
            # Reconnexion et traitement du setup
            # ------------------------------------------------
            for attempt in range(
                1,
                RECONNECT_ATTEMPTS + 1,
            ):
                try:
                    self.log(
                        f"{name}: reconnexion "
                        f"{attempt}/{RECONNECT_ATTEMPTS}"
                    )

                    connection = self.connect_router(
                        name,
                        port,
                    )

                    boot_ok = self.handle_boot_dialog(
                        connection,
                        name,
                    )

                    if boot_ok:
                        self.log(
                            f"{name}: démarrage IOS terminé"
                        )
                    else:
                        self.log(
                            f"{name}: dialogue IOS non confirmé",
                            "WARNING",
                        )

                    # ------------------------------------------------
                    # Vérification finale
                    # ------------------------------------------------
                    version = connection.send_command(
                        "show version",
                        read_timeout=60,
                    )

                    running = connection.send_command(
                        "show running-config",
                        read_timeout=60,
                    )

                    startup = connection.send_command(
                        "show startup-config",
                        read_timeout=60,
                    )

                    self.log(
                        f"{name}: show version OK"
                    )

                    # Après write erase + reload, la configuration
                    # utilisateur doit être absente.
                    suspicious = []

                    for line in (
                        "hostname ",
                        "router ospf ",
                        "router rip",
                        "ip address ",
                    ):
                        if line in running.lower():
                            suspicious.append(line)

                    if suspicious:
                        self.log(
                            f"{name}: éléments de configuration "
                            f"détectés après reset : "
                            f"{', '.join(suspicious)}",
                            "WARNING",
                        )
                    else:
                        self.log(
                            f"{name}: running-config propre"
                        )

                    self.log(
                        f"{name}: reset terminé avec succès"
                    )

                    return True

                except (
                    NetmikoTimeoutException,
                    ConnectionError,
                    OSError,
                ) as error:
                    self.log(
                        f"{name}: IOS pas encore disponible "
                        f"({error})",
                        "WARNING",
                    )

                    if connection:
                        try:
                            connection.disconnect()
                        except Exception:
                            pass

                        connection = None

                    time.sleep(RECONNECT_DELAY)

                except NetmikoAuthenticationException as error:
                    self.log(
                        f"{name}: authentification Telnet échouée : "
                        f"{error}",
                        "ERROR",
                    )
                    return False

                except Exception as error:
                    self.log(
                        f"{name}: erreur pendant le boot : "
                        f"{error}",
                        "ERROR",
                    )

                    if connection:
                        try:
                            connection.disconnect()
                        except Exception:
                            pass

                        connection = None

                    time.sleep(RECONNECT_DELAY)

            self.log(
                f"{name}: routeur indisponible après le redémarrage : impossible de se reconnecter dans le délai prévu",
                "ERROR",
            )

            return False

        except NetmikoTimeoutException as error:
            self.log(
                f"{name}: timeout Telnet : {error}",
                "ERROR",
            )
            return False

        except NetmikoAuthenticationException as error:
            self.log(
                f"{name}: authentification Telnet échouée : "
                f"{error}",
                "ERROR",
            )
            return False

        except Exception as error:
            self.log(
                f"{name}: {error}",
                "ERROR",
            )
            return False

        finally:
            if connection:
                try:
                    connection.disconnect()
                except Exception:
                    pass

    def run(self):
        total = len(ROUTERS)
        success = 0
        failed_router = None
        failed_reason = None

        self.log(
            "========== DÉBUT RESET TP10 =========="
        )

        self.log(
            f"{total} routeurs à réinitialiser"
        )

        for index, (name, port) in enumerate(
            ROUTERS.items(),
            start=1,
        ):
            self.log("")
            self.log("=" * 60)
            self.log(
                f"RESET {name} - port {port}"
            )
            self.log("=" * 60)

            router_ok = self.reset_router(name, port)

            if router_ok:
                success += 1
            else:
                # Politique stricte :
                # un routeur indisponible arrête immédiatement
                # toute l'opération. On ne continue pas avec
                # les routeurs suivants.
                failed_router = name
                failed_reason = (
                    "Le routeur ne répond pas ou "
                    "n'est pas redevenu accessible après "
                    "les délais d'attente."
                )

                self.log(
                    f"{name}: OPÉRATION ARRÊTÉE",
                    "ERROR",
                )

                self.log(
                    "Un routeur ne répond pas. "
                    "Les routeurs suivants ne seront pas traités.",
                    "ERROR",
                )

                break

            self.progress_signal.emit(
                int(index / total * 100)
            )

        self.log("")
        self.log("=" * 60)

        if failed_router:
            self.log(
                f"RÉSULTAT : opération interrompue sur "
                f"{failed_router} — "
                f"{success}/{total} routeurs terminés",
                "ERROR",
            )
        else:
            self.log(
                f"RÉSULTAT : {success}/{total} "
                "routeurs réinitialisés"
            )

        self.log("=" * 60)

        ok = (
            failed_router is None
            and success == total
        )

        if failed_router:
            message = (
                "OPÉRATION ARRÊTÉE\n\n"
                f"Le routeur {failed_router} ne répond pas.\n\n"
                f"Cause : {failed_reason}\n\n"
                f"Routeurs réinitialisés : "
                f"{success}/{total}\n\n"
                "Aucun routeur suivant n'a été traité.\n\n"
                f"Log :\n{LOG_FILE}"
            )
        else:
            message = (
                "Réinitialisation terminée.\n\n"
                f"Routeurs OK : {success}/{total}\n\n"
                f"Log :\n{LOG_FILE}"
            )

        self.finished_signal.emit(ok, message)


# ============================================================
# GUI
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "TP10 — Router Reset"
        )

        self.resize(
            1050,
            720,
        )

        self.thread = None
        self.worker = None

        self.build_ui()
        self.apply_style()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(
            25, 25, 25, 25
        )
        layout.setSpacing(15)

        title = QLabel(
            "TP10 — Réinitialisation des routeurs"
        )
        title.setObjectName("title")

        subtitle = QLabel(
            "GNS3 • Telnet • Cisco IOS • Reset automatisé"
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        timeout_info = QLabel(
            "⏱ Délais : 60 s connexion / 30 s attente reboot / "
            "18 tentatives de reconnexion. "
            "Un échec arrête toute l'opération."
        )
        timeout_info.setObjectName("timeoutInfo")
        layout.addWidget(timeout_info)

        # ----------------------------------------------------
        # Routeurs
        # ----------------------------------------------------

        group = QGroupBox(
            "Routeurs ciblés"
        )

        group_layout = QHBoxLayout(group)

        for name, port in ROUTERS.items():
            card = QLabel(
                f"<b>{name}</b><br>"
                f"Telnet : {HOST}:{port}"
            )
            card.setObjectName(
                "routerCard"
            )
            group_layout.addWidget(card)

        layout.addWidget(group)

        # ----------------------------------------------------
        # Explication
        # ----------------------------------------------------

        info = QLabel(
            "Le script efface la startup-config, redémarre "
            "chaque routeur et répond automatiquement « no » "
            "aux dialogues de configuration IOS."
        )

        info.setWordWrap(True)
        info.setObjectName("info")

        layout.addWidget(info)

        # ----------------------------------------------------
        # Progression
        # ----------------------------------------------------

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%p%")

        layout.addWidget(
            self.progress
        )

        # ----------------------------------------------------
        # Console
        # ----------------------------------------------------

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText(
            "Journal d'exécution..."
        )

        layout.addWidget(
            self.console,
            stretch=1,
        )

        # ----------------------------------------------------
        # Boutons
        # ----------------------------------------------------

        buttons = QHBoxLayout()

        self.start_button = QPushButton(
            "⟳  Réinitialiser tous les routeurs"
        )
        self.start_button.setObjectName(
            "primaryButton"
        )

        self.clear_button = QPushButton(
            "Effacer le journal"
        )

        self.open_log_button = QPushButton(
            "Ouvrir le log"
        )

        buttons.addWidget(
            self.start_button
        )
        buttons.addWidget(
            self.clear_button
        )
        buttons.addWidget(
            self.open_log_button
        )
        buttons.addStretch()

        layout.addLayout(buttons)

        self.start_button.clicked.connect(
            self.start_reset
        )

        self.clear_button.clicked.connect(
            self.console.clear
        )

        self.open_log_button.clicked.connect(
            self.open_log
        )

    def apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #111827;
            }

            QWidget {
                color: #E5E7EB;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel#title {
                font-size: 27px;
                font-weight: 700;
                color: #F9FAFB;
            }

            QLabel#subtitle {
                font-size: 14px;
                color: #9CA3AF;
            }

            QLabel#timeoutInfo {
                color: #FBBF24;
                background: #1F2937;
                border: 1px solid #92400E;
                border-radius: 8px;
                padding: 10px;
            }

            QLabel#info {
                color: #D1D5DB;
                background: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 14px;
            }

            QGroupBox {
                border: 1px solid #374151;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }

            QLabel#routerCard {
                background: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 14px;
                min-width: 105px;
            }

            QPlainTextEdit {
                background: #0B1120;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                font-family: "DejaVu Sans Mono";
                font-size: 12px;
            }

            QProgressBar {
                border: 1px solid #374151;
                border-radius: 6px;
                background: #1F2937;
                height: 12px;
                text-align: center;
            }

            QProgressBar::chunk {
                background: #2563EB;
                border-radius: 5px;
            }

            QPushButton {
                background: #1F2937;
                border: 1px solid #374151;
                border-radius: 7px;
                padding: 10px 18px;
            }

            QPushButton:hover {
                background: #374151;
            }

            QPushButton#primaryButton {
                background: #2563EB;
                border: none;
                font-weight: 700;
                padding: 11px 22px;
            }

            QPushButton#primaryButton:hover {
                background: #1D4ED8;
            }

            QPushButton:disabled {
                color: #6B7280;
                background: #111827;
            }
            """
        )

    def append_log(self, message):
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.console.appendPlainText(
            f"{timestamp}  {message}"
        )

    def start_reset(self):
        reply = QMessageBox.warning(
            self,
            "Confirmation requise",
            "Cette opération va :\n\n"
            "• effacer la startup-config ;\n"
            "• redémarrer R1, R2, R3, R4, R5, R6, "
            "ASBR, R8 et R9 ;\n"
            "• répondre automatiquement « no » "
            "aux dialogues IOS.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.start_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.progress.setValue(0)

        self.append_log(
            "[INFO] Démarrage de la réinitialisation..."
        )

        self.thread = QThread()
        self.worker = ResetWorker()

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.log_signal.connect(
            self.append_log
        )

        self.worker.progress_signal.connect(
            self.progress.setValue
        )

        self.worker.finished_signal.connect(
            self.reset_finished
        )

        self.worker.finished_signal.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.start()

    def reset_finished(
        self,
        success,
        message,
    ):
        self.start_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.progress.setValue(100)

        if success:
            QMessageBox.information(
                self,
                "Réinitialisation terminée",
                message,
            )
        else:
            QMessageBox.critical(
                self,
                "Opération arrêtée",
                message,
            )

    def open_log(self):
        if not LOG_FILE.exists():
            QMessageBox.information(
                self,
                "Log",
                "Le fichier log n'existe pas encore.",
            )
            return

        try:
            import subprocess

            subprocess.Popen([
                "xdg-open",
                str(LOG_FILE),
            ])

        except Exception as error:
            QMessageBox.warning(
                self,
                "Erreur",
                str(error),
            )


# ============================================================
# MAIN
# ============================================================

def main():
    app = QApplication(sys.argv)

    app.setApplicationName(
        "TP10 Router Reset"
    )

    window = MainWindow()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
