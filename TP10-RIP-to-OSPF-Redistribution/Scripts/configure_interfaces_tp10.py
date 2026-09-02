#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP10 - Configuration automatique des interfaces Cisco
------------------------------------------------------
- PySide6 : interface moderne dark / Cisco
- Netmiko : connexion aux routeurs Cisco via les ports GNS3 déjà définis
- Aucun champ "connexion Telnet" dans l'interface utilisateur
- Sélection d'un ou plusieurs routeurs
- Configuration :
    hostname
    no ip domain lookup
    interface
    ip address
    no shutdown
- Après chaque routeur : "show ip interface brief"
- La sortie est affichée dans une boîte de dialogue et l'utilisateur doit
  valider avant de passer au routeur suivant.

Topologie TP10 utilisée :
  OSPF : R1, R2, R3, R4, ASBR
  RIP  : R9, R5, R6, R8

Les ports localhost GNS3 sont volontairement internes au script :
  R1   5009
  R2   5010
  R3   5011
  R4   5012
  R5   5013
  R6   5014
  ASBR 5015
  R8   5016
  R9   5017

Dépendances :
  pip install --upgrade PySide6 netmiko
"""

import sys
import time
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QSize
from PySide6.QtGui import QFont, QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from netmiko import ConnectHandler
except ImportError:
    ConnectHandler = None


APP_DIR = Path(__file__).resolve().parent
LOGO_FILE = APP_DIR / "cisco_logo.jpg"
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "config_tp10_interfaces.log"

# Les paramètres de connexion ne sont pas exposés dans la GUI.
# Ils correspondent aux ports GNS3 de la topologie TP10.
ROUTERS = {
    "R1": {
        "port": 5009,
        "interfaces": [
            ("Serial2/0", "10.0.1.1", "255.255.255.252", "R2"),
            ("Serial2/1", "10.0.3.1", "255.255.255.252", "R3"),
            ("Serial2/2", "10.0.2.1", "255.255.255.252", "R4"),
        ],
    },
    "R2": {
        "port": 5010,
        "interfaces": [
            ("Serial2/0", "10.0.1.2", "255.255.255.252", "R1"),
            ("Serial2/1", "10.0.5.2", "255.255.255.252", "R4"),
            ("Serial2/2", "10.0.4.2", "255.255.255.252", "R3"),
            ("Serial2/3", "10.0.7.1", "255.255.255.252", "ASBR"),
        ],
    },
    "R3": {
        "port": 5011,
        "interfaces": [
            ("Serial2/0", "10.0.3.2", "255.255.255.252", "R1"),
            ("Serial2/1", "10.0.6.1", "255.255.255.252", "R4"),
            ("Serial2/2", "10.0.4.1", "255.255.255.252", "R2"),
        ],
    },
    "R4": {
        "port": 5012,
        "interfaces": [
            ("Serial2/0", "10.0.6.2", "255.255.255.252", "R3"),
            ("Serial2/1", "10.0.5.1", "255.255.255.252", "R2"),
            ("Serial2/2", "10.0.2.2", "255.255.255.252", "R1"),
            ("Serial2/3", "10.0.8.1", "255.255.255.252", "ASBR"),
        ],
    },
    "ASBR": {
        "port": 5015,
        "interfaces": [
            ("Serial2/0", "10.0.7.2", "255.255.255.252", "R2"),
            ("Serial2/1", "10.0.8.2", "255.255.255.252", "R4"),
            ("Serial2/2", "10.0.9.2", "255.255.255.252", "R9"),
            ("Serial2/3", "10.0.10.2", "255.255.255.252", "R6"),
        ],
    },
    "R9": {
        "port": 5017,
        "interfaces": [
            ("Serial2/0", "10.0.11.1", "255.255.255.252", "R5"),
            ("Serial2/1", "10.0.9.1", "255.255.255.252", "ASBR"),
            ("Serial2/2", "10.0.12.2", "255.255.255.252", "R6"),
        ],
    },
    "R5": {
        "port": 5013,
        "interfaces": [
            ("Serial2/0", "10.0.11.2", "255.255.255.252", "R9"),
            ("Serial2/1", "10.0.14.2", "255.255.255.252", "R8"),
        ],
    },
    "R6": {
        "port": 5014,
        "interfaces": [
            ("Serial2/0", "10.0.10.1", "255.255.255.252", "ASBR"),
            ("Serial2/1", "10.0.12.1", "255.255.255.252", "R9"),
            ("Serial2/2", "10.0.13.1", "255.255.255.252", "R8"),
        ],
    },
    "R8": {
        "port": 5016,
        "interfaces": [
            ("Serial2/0", "10.0.13.2", "255.255.255.252", "R6"),
            ("Serial2/1", "10.0.14.1", "255.255.255.252", "R5"),
        ],
    },
}

ROUTER_ORDER = ["R1", "R2", "R3", "R4", "ASBR", "R9", "R5", "R6", "R8"]

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)


DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0b0f14;
    color: #ffffff;
    font-family: "Segoe UI";
    font-size: 13px;
}

QFrame#Header {
    background-color: #101820;
    border: 1px solid #25313a;
    border-radius: 16px;
}

QFrame#Card {
    background-color: #111820;
    border: 1px solid #25313a;
    border-radius: 14px;
}

QLabel#Title {
    color: #ff2448;
    font-size: 27px;
    font-weight: 800;
}

QLabel#Subtitle {
    color: #d4dde2;
    font-size: 13px;
}

QLabel#SectionTitle {
    color: #22b8f0;
    font-size: 17px;
    font-weight: 800;
}

QGroupBox {
    border: 1px solid #2a3944;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: 700;
    color: #d9e1e6;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #049fd9;
}

QListWidget, QPlainTextEdit, QLineEdit {
    background-color: #121a21;
    border: 1px solid #3a4b57;
    border-radius: 9px;
    color: #ffffff;
    padding: 9px;
    selection-background-color: #176b8e;
    selection-color: #ffffff;
}

QListWidget::item {
    padding: 12px 10px;
    min-height: 24px;
    border-radius: 6px;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #17232c;
}

QListWidget::item:selected {
    background-color: #183c4c;
    color: #ffffff;
}

QLineEdit:focus, QPlainTextEdit:focus, QListWidget:focus {
    border: 1px solid #049fd9;
}

QPushButton {
    background-color: #1b3441;
    border: 1px solid #466575;
    border-radius: 9px;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 800;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #20495c;
}

QPushButton:pressed {
    background-color: #102832;
}

QPushButton#Primary {
    background-color: #e31837;
    border: 1px solid #ff3d5b;
    color: white;
    min-height: 38px;
}

QPushButton#Primary:hover {
    background-color: #c91531;
}

QPushButton#Danger {
    background-color: #5a1a25;
    border: 1px solid #9d3042;
}

QProgressBar {
    background-color: #0a0e12;
    border: 1px solid #2a3944;
    border-radius: 7px;
    text-align: center;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #049fd9;
    border-radius: 6px;
}

QCheckBox {
    spacing: 10px;
    padding: 6px;
    color: #ffffff;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #50616d;
    border-radius: 4px;
    background: #0a0e12;
}

QCheckBox::indicator:checked {
    border: 1px solid #049fd9;
    border-radius: 4px;
    background: #049fd9;
}
"""


class CredentialsDialog(QDialog):
    """Demande uniquement les identifiants IOS, pas les paramètres Telnet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identifiants IOS")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel("Connexion aux routeurs")
        title.setObjectName("Title")
        layout.addWidget(title)

        info = QLabel(
            "Les paramètres de connexion GNS3 sont intégrés au programme.\n"
            "Saisissez uniquement les identifiants IOS si votre image IOS les demande."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #d0dbe1; font-size: 13px;")
        layout.addWidget(info)

        form = QGridLayout()
        form.addWidget(QLabel("Utilisateur"), 0, 0)
        self.username = QLineEdit()
        self.username.setPlaceholderText("laisser vide si non utilisé")
        form.addWidget(self.username, 0, 1)

        form.addWidget(QLabel("Mot de passe"), 1, 0)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("laisser vide si non utilisé")
        form.addWidget(self.password, 1, 1)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return self.username.text(), self.password.text()


class ShowIpBriefDialog(QDialog):
    def __init__(self, router_name, output, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{router_name} — show ip interface brief")
        self.resize(1050, 650)
        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel(f"{router_name} — Vérification terminée")
        title.setObjectName("Title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Vérifiez la sortie ci-dessous. Cliquez sur « Valider et continuer » "
            "pour passer au routeur suivant."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #d0dbe1; font-size: 13px;")
        layout.addWidget(subtitle)

        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 12))
        text.setPlainText(output)
        layout.addWidget(text)

        buttons = QDialogButtonBox()
        validate = buttons.addButton(
            "Valider et continuer", QDialogButtonBox.AcceptRole
        )
        validate.setObjectName("Primary")
        validate.setMinimumHeight(38)
        validate.clicked.connect(self.accept)

        cancel = buttons.addButton("Arrêter", QDialogButtonBox.RejectRole)
        cancel.setObjectName("Danger")
        cancel.clicked.connect(self.reject)

        layout.addWidget(buttons)


class Worker(QObject):
    log = Signal(str)
    progress = Signal(int, int, str)
    finished = Signal(bool, str, list)
    show_brief = Signal(str, str)

    def __init__(self, selected, username, password):
        super().__init__()
        self.selected = selected
        self.username = username
        self.password = password
        self.continue_event = None
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True
        if self.continue_event:
            self.continue_event.set()

    @Slot()
    def run(self):
        if ConnectHandler is None:
            self.finished.emit(
                False,
                "Netmiko n'est pas installé.\n\n"
                "Installez-le avec : pip install netmiko",
                [],
            )
            return

        total = len(self.selected)
        completed = []

        for index, router_name in enumerate(self.selected, start=1):
            if self.stop_requested:
                break

            router = ROUTERS[router_name]
            self.progress.emit(index - 1, total, f"Connexion à {router_name}...")
            self.log.emit(
                f"[{router_name}] Connexion GNS3 localhost:{router['port']}"
            )

            connection = None
            try:
                params = {
                    "device_type": "cisco_ios_telnet",
                    "host": "127.0.0.1",
                    "port": router["port"],
                    "username": self.username,
                    "password": self.password,
                    "conn_timeout": 25,
                    "banner_timeout": 25,
                    "auth_timeout": 20,
                    "fast_cli": False,
                }

                connection = ConnectHandler(**params)
                self.log.emit(f"[{router_name}] Connexion établie.")

                # Quel que soit le mode IOS initial, revenir au mode privilégié.
                self.log.emit(f"[{router_name}] Retour vers le mode privilégié...")
                try:
                    connection.send_command_timing(
                        "end",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=20,
                    )
                except Exception:
                    pass

                connection.enable()
                self.log.emit(f"[{router_name}] Mode privilégié actif (EXEC #).")

                self.log.emit(
                    f"[{router_name}] Application de {len(router['interfaces'])} interface(s)."
                )

                # On utilise send_command_timing() plutôt que send_config_set().
                # Le hostname change le prompt IOS (Router# -> R9#), ce qui
                # peut faire échouer Netmiko avec :
                # "Pattern not detected: 'Router*' in output."
                config_output = []

                config_output.append(
                    connection.send_command_timing(
                        "configure terminal",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=30,
                    )
                )

                config_output.append(
                    connection.send_command_timing(
                        "no ip domain lookup",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=30,
                    )
                )

                for interface, ip, mask, neighbor in router["interfaces"]:
                    self.log.emit(
                        f"[{router_name}] {interface} <- {ip} {mask} (vers {neighbor})"
                    )

                    config_output.append(
                        connection.send_command_timing(
                            f"interface {interface}",
                            strip_prompt=False,
                            strip_command=False,
                            read_timeout=30,
                        )
                    )
                    config_output.append(
                        connection.send_command_timing(
                            f"ip address {ip} {mask}",
                            strip_prompt=False,
                            strip_command=False,
                            read_timeout=30,
                        )
                    )
                    config_output.append(
                        connection.send_command_timing(
                            "no shutdown",
                            strip_prompt=False,
                            strip_command=False,
                            read_timeout=30,
                        )
                    )
                    config_output.append(
                        connection.send_command_timing(
                            "exit",
                            strip_prompt=False,
                            strip_command=False,
                            read_timeout=30,
                        )
                    )

                # Le hostname est appliqué EN DERNIER afin que son changement
                # de prompt ne casse aucune commande de configuration.
                config_output.append(
                    connection.send_command_timing(
                        f"hostname {router_name}",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=30,
                    )
                )

                config_output.append(
                    connection.send_command_timing(
                        "end",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=30,
                    )
                )

                time.sleep(0.5)
                connection.clear_buffer()
                new_prompt = connection.find_prompt()
                self.log.emit(
                    f"[{router_name}] Nouveau prompt détecté : {new_prompt.strip()}"
                )

                output = "\n".join(config_output)
                logging.info("%s configuration:\n%s", router_name, output)

                # Pas de sauvegarde automatique : la vérification reste
                # indépendante de la sauvegarde de la configuration.

                # Revenir explicitement au mode privilégié avant la vérification.
                try:
                    connection.send_command_timing(
                        "end",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=20,
                    )
                except Exception:
                    pass

                connection.enable()
                self.log.emit(
                    f"[{router_name}] Mode privilégié confirmé pour la vérification."
                )

                brief = connection.send_command(
                    "show ip interface brief",
                    read_timeout=30,
                    strip_prompt=False,
                    strip_command=False,
                )

                self.log.emit(f"[{router_name}] show ip interface brief récupéré.")
                completed.append(router_name)
                self.progress.emit(index, total, f"{router_name} terminé.")

                # Demande à l'UI de montrer la boîte de dialogue.
                self.show_brief.emit(router_name, brief)

                # Attendre la validation de l'utilisateur.
                self.continue_event = __import__("threading").Event()
                while not self.continue_event.is_set():
                    if self.stop_requested:
                        break
                    self.continue_event.wait(0.1)
                self.continue_event = None

                if self.stop_requested:
                    self.log.emit(
                        f"[{router_name}] Opération arrêtée par l'utilisateur."
                    )
                    break

            except Exception as exc:
                logging.exception("Erreur sur %s", router_name)
                self.log.emit(f"[{router_name}] ERREUR : {exc}")
                self.finished.emit(
                    False,
                    f"Erreur pendant la configuration de {router_name} :\n\n{exc}",
                    completed,
                )
                return
            finally:
                if connection is not None:
                    try:
                        connection.disconnect()
                    except Exception:
                        pass

        if self.stop_requested:
            self.finished.emit(
                False,
                "Opération arrêtée par l'utilisateur.",
                completed,
            )
        else:
            self.finished.emit(
                True,
                f"Configuration terminée sur {len(completed)} routeur(s).",
                completed,
            )


class MainWindow(QMainWindow):
    continue_worker = Signal()
    stop_worker = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cisco TP10 — Configuration des interfaces")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(DARK_QSS)

        self.thread = None
        self.worker = None
        self.running = False

        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # Header
        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        logo = QLabel()
        logo.setFixedSize(155, 88)
        logo.setAlignment(Qt.AlignCenter)
        if LOGO_FILE.exists():
            pix = QPixmap(str(LOGO_FILE))
            pix = pix.scaled(
                logo.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            logo.setPixmap(pix)
        else:
            logo.setText("CISCO")
            logo.setStyleSheet(
                "font-size: 30px; font-weight: 900; color: #e31837;"
            )
        header_layout.addWidget(logo)

        titles = QVBoxLayout()
        title = QLabel("TP10 — Redistribution de routes")
        title.setObjectName("Title")
        titles.addWidget(title)

        subtitle = QLabel(
            "Configuration des adresses IP • Hostname • no ip domain lookup • "
            "Vérification interactive"
        )
        subtitle.setObjectName("Subtitle")
        titles.addWidget(subtitle)

        header_layout.addLayout(titles)
        header_layout.addStretch()

        status = QLabel("GNS3 / Cisco IOS")
        status.setStyleSheet(
            "color: #049fd9; font-weight: 700; padding: 8px 12px; "
            "border: 1px solid #2e5364; border-radius: 8px;"
        )
        header_layout.addWidget(status)

        root.addWidget(header)

        # Main split
        main = QHBoxLayout()
        main.setSpacing(14)

        # Left card: routers
        left = QFrame()
        left.setObjectName("Card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)

        section = QLabel("Routeurs à configurer")
        section.setObjectName("SectionTitle")
        left_layout.addWidget(section)

        hint = QLabel(
            "Sélectionnez un ou plusieurs routeurs. "
            "L'ordre de traitement suit la topologie."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #c8d3d9; font-size: 13px;")
        left_layout.addWidget(hint)

        self.select_all = QCheckBox("Sélectionner tous les routeurs")
        self.select_all.toggled.connect(self.toggle_all)
        left_layout.addWidget(self.select_all)

        self.router_list = QListWidget()
        self.router_list.setSelectionMode(QListWidget.NoSelection)
        self.router_list.setSpacing(4)
        self.router_list.setUniformItemSizes(True)
        self.router_list.setMinimumWidth(340)
        self.router_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.router_list.setTextElideMode(Qt.ElideNone)

        # Un QListWidgetItem natif est volontairement utilisé ici.
        # Aucun QWidget/QCheckBox personnalisé n'est placé dans la liste :
        # cela garantit un calcul de taille fiable et évite le texte tronqué.
        for name in ROUTER_ORDER:
            role = (
                "OSPF / Area 0"
                if name in {"R1", "R2", "R3", "R4", "ASBR"}
                else "RIP v2"
            )

            item = QListWidgetItem(f"{name}    •    {role}")
            item.setData(Qt.UserRole, name)
            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsEnabled
            )
            item.setCheckState(Qt.Unchecked)
            item.setSizeHint(QSize(0, 42))
            self.router_list.addItem(item)

        self.router_list.itemChanged.connect(self.update_selection_state)

        left_layout.addWidget(self.router_list, 1)

        buttons_row = QHBoxLayout()
        self.btn_select_none = QPushButton("Tout désélectionner")
        self.btn_select_none.clicked.connect(self.select_none)
        buttons_row.addWidget(self.btn_select_none)

        self.btn_config = QPushButton("Configurer la sélection")
        self.btn_config.setObjectName("Primary")
        self.btn_config.clicked.connect(self.start_configuration)
        buttons_row.addWidget(self.btn_config)

        left_layout.addLayout(buttons_row)

        # Right card: status/log
        right = QFrame()
        right.setObjectName("Card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)

        section2 = QLabel("Progression")
        section2.setObjectName("SectionTitle")
        right_layout.addWidget(section2)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        right_layout.addWidget(self.progress)

        self.status_label = QLabel("Prêt.")
        self.status_label.setStyleSheet("color: #d6e0e5; font-size: 13px; font-weight: 600;")
        right_layout.addWidget(self.status_label)

        section3 = QLabel("Journal d'exécution")
        section3.setObjectName("SectionTitle")
        right_layout.addWidget(section3)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 9))
        right_layout.addWidget(self.log_box, 1)

        self.btn_stop = QPushButton("Arrêter")
        self.btn_stop.setObjectName("Danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_configuration)
        right_layout.addWidget(self.btn_stop)

        main.addWidget(left, 1)
        main.addWidget(right, 1)
        root.addLayout(main, 1)

        footer = QLabel(
            f"Journal : {LOG_FILE}    •    "
            "Les ports GNS3 sont intégrés au programme et ne sont pas modifiables depuis la GUI."
        )
        footer.setStyleSheet("color: #91a3ad; font-size: 11px;")
        footer.setWordWrap(True)
        root.addWidget(footer)

    def toggle_all(self, checked):
        self.router_list.blockSignals(True)
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.router_list.count()):
            self.router_list.item(i).setCheckState(state)
        self.router_list.blockSignals(False)

    def select_none(self):
        self.select_all.blockSignals(True)
        self.select_all.setChecked(False)
        self.select_all.blockSignals(False)

        self.router_list.blockSignals(True)
        for i in range(self.router_list.count()):
            self.router_list.item(i).setCheckState(Qt.Unchecked)
        self.router_list.blockSignals(False)

    def update_selection_state(self, _item=None):
        checked = sum(
            self.router_list.item(i).checkState() == Qt.Checked
            for i in range(self.router_list.count())
        )

        all_checked = checked == self.router_list.count()
        self.select_all.blockSignals(True)
        self.select_all.setChecked(all_checked)
        self.select_all.blockSignals(False)

    def selected_routers(self):
        result = []
        for i in range(self.router_list.count()):
            item = self.router_list.item(i)
            if item.checkState() == Qt.Checked:
                result.append(item.data(Qt.UserRole))
        return result

    def start_configuration(self):
        if self.running:
            return

        selected = self.selected_routers()
        if not selected:
            QMessageBox.warning(
                self,
                "Aucun routeur",
                "Sélectionnez au moins un routeur à configurer.",
            )
            return

        credentials = CredentialsDialog(self)
        if credentials.exec() != QDialog.Accepted:
            return

        username, password = credentials.values()

        answer = QMessageBox.question(
            self,
            "Confirmer la configuration",
            "Routeurs sélectionnés :\n\n"
            + "  • " + "\n  • ".join(selected)
            + "\n\n"
            "La configuration va appliquer :\n"
            "  • hostname\n"
            "  • no ip domain lookup\n"
            "  • adresses IP /30\n"
            "  • no shutdown\n\n"
            "Après chaque routeur, vous devrez valider la sortie "
            "\"show ip interface brief\" pour continuer.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.running = True
        self.btn_config.setEnabled(False)
        self.btn_select_none.setEnabled(False)
        self.select_all.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.log_box.clear()
        self.append_log(
            "=== DÉBUT CONFIGURATION TP10 ===\n"
            f"Routeurs : {', '.join(selected)}"
        )

        self.thread = QThread(self)
        self.worker = Worker(selected, username, password)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.update_progress)
        self.worker.show_brief.connect(self.show_brief_dialog)
        self.worker.finished.connect(self.configuration_finished)
        self.worker.finished.connect(self.thread.quit)

        self.thread.finished.connect(self.cleanup_thread)

        self.thread.start()

    @Slot(str)
    def append_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_box.appendPlainText(line)
        logging.info(message)

    @Slot(int, int, str)
    def update_progress(self, current, total, message):
        percent = int((current / total) * 100) if total else 0
        self.progress.setValue(percent)
        self.status_label.setText(message)

    @Slot(str, str)
    def show_brief_dialog(self, router_name, output):
        dialog = ShowIpBriefDialog(router_name, output, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.append_log(
                f"[{router_name}] Validation utilisateur reçue. "
                "Passage au routeur suivant."
            )
            if self.worker:
                # Signal thread-safe vers le worker.
                self.worker.continue_event.set()
        else:
            self.append_log(
                f"[{router_name}] Arrêt demandé depuis la boîte de dialogue."
            )
            if self.worker:
                self.worker.stop()
                if self.worker.continue_event:
                    self.worker.continue_event.set()

    @Slot(bool, str, list)
    def configuration_finished(self, success, message, completed):
        self.progress.setValue(100 if success else self.progress.value())

        if success:
            self.status_label.setText("Configuration terminée.")
            self.append_log("=== FIN : SUCCÈS ===")
            QMessageBox.information(
                self,
                "Configuration terminée",
                message + "\n\n"
                "Routeurs traités : "
                + (", ".join(completed) if completed else "aucun"),
            )
        else:
            self.status_label.setText("Opération arrêtée / en erreur.")
            self.append_log("=== FIN : ARRÊT / ERREUR ===")
            QMessageBox.critical(
                self,
                "Configuration interrompue",
                message + "\n\n"
                "Routeurs traités : "
                + (", ".join(completed) if completed else "aucun"),
            )

    def stop_configuration(self):
        if self.worker:
            self.append_log("Arrêt demandé par l'utilisateur.")
            self.worker.stop()
            if self.worker.continue_event:
                self.worker.continue_event.set()
        self.btn_stop.setEnabled(False)

    def cleanup_thread(self):
        self.running = False
        self.btn_config.setEnabled(True)
        self.btn_select_none.setEnabled(True)
        self.select_all.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()

        self.worker = None
        self.thread = None

    def closeEvent(self, event):
        if self.running:
            answer = QMessageBox.question(
                self,
                "Configuration en cours",
                "Une configuration est encore en cours.\n"
                "Voulez-vous vraiment arrêter le programme ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer == QMessageBox.Yes:
                self.stop_configuration()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cisco TP10 Interface Configurator")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 12))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
