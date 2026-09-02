#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""TP10 - Configuration RIP v2 via GNS3/Netmiko."""

import sys
import time
import socket
import threading
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFrame,
    QGridLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QHBoxLayout, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

try:
    from netmiko import ConnectHandler
except ImportError:
    ConnectHandler = None

BASE_DIR = Path("//")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "config_tp10_rip.log"
LOGO_FILE = BASE_DIR / "cisco_logo.jpg"

# Ports GNS3 de la topologie TP10.
ROUTERS = {
    "R9": 5017,
    "R5": 5013,
    "R6": 5014,
    "R8": 5016,
    "ASBR": 5015,
}
ROUTER_ORDER = ["R9", "R5", "R6", "R8", "ASBR"]

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)

QSS = """
QMainWindow, QWidget { background:#0b0f14; color:#f4f7f9; font-family:"Segoe UI"; }
QFrame#Header,QFrame#Card { background:#111820; border:1px solid #25313a; border-radius:14px; }
QLabel#Title { color:#e31837; font-size:25px; font-weight:800; }
QLabel#Subtitle { color:#9aa8b2; font-size:12px; }
QLabel#SectionTitle { color:#049fd9; font-size:15px; font-weight:700; }
QListWidget,QPlainTextEdit,QLineEdit { background:#0a0e12; border:1px solid #2a3944; border-radius:9px; color:#f4f7f9; padding:7px; }
QListWidget { padding:4px; }
QListWidget::item { padding:8px 10px; min-height:24px; border-radius:6px; }
QListWidget::item:hover { background:#17232c; }
QListWidget::item:selected { background:#183c4c; color:white; }
QPushButton { background:#17303d; border:1px solid #2e5364; border-radius:9px; padding:9px 14px; font-weight:700; }
QPushButton:hover { background:#20495c; }
QPushButton#Primary { background:#e31837; border:1px solid #ff3d5b; color:white; min-height:38px; }
QPushButton#Danger { background:#5a1a25; border:1px solid #9d3042; }
QCheckBox { spacing:8px; padding:4px; }
QProgressBar { background:#0a0e12; border:1px solid #2a3944; border-radius:7px; text-align:center; height:18px; }
QProgressBar::chunk { background:#049fd9; border-radius:6px; }
"""

class CredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identifiants IOS")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)

        title = QLabel("Connexion aux routeurs")
        title.setObjectName("Title")
        layout.addWidget(title)
        info = QLabel(
            "Les ports GNS3 sont intégrés au programme.\n"
            "Aucun paramètre Telnet n'est demandé."
        )
        info.setStyleSheet("color:#9aa8b2;")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QGridLayout()
        form.addWidget(QLabel("Utilisateur"), 0, 0)
        self.username = QLineEdit()
        self.username.setPlaceholderText("laisser vide si non utilisé")
        form.addWidget(self.username, 0, 1)

        form.addWidget(QLabel("Mot de passe"), 1, 0)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addWidget(self.password, 1, 1)

        form.addWidget(QLabel("Enable secret"), 2, 0)
        self.secret = QLineEdit()
        self.secret.setEchoMode(QLineEdit.Password)
        self.secret.setPlaceholderText("laisser vide si identique")
        form.addWidget(self.secret, 2, 1)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return self.username.text(), self.password.text(), self.secret.text()


class VerificationDialog(QDialog):
    def __init__(self, router, output, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{router} — Vérification RIP")
        self.resize(950, 620)
        layout = QVBoxLayout(self)

        title = QLabel(f"{router} — RIP v2")
        title.setObjectName("Title")
        layout.addWidget(title)

        info = QLabel(
            "Vérification : show ip protocols + show ip route rip.\n"
            "Validez pour continuer vers le routeur suivant."
        )
        info.setStyleSheet("color:#9aa8b2;")
        layout.addWidget(info)

        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setFont(QFont("Consolas", 10))
        box.setPlainText(output)
        layout.addWidget(box, 1)

        buttons = QDialogButtonBox()
        ok = buttons.addButton("Valider et continuer", QDialogButtonBox.AcceptRole)
        ok.setObjectName("Primary")
        stop = buttons.addButton("Arrêter", QDialogButtonBox.RejectRole)
        stop.setObjectName("Danger")
        ok.clicked.connect(self.accept)
        stop.clicked.connect(self.reject)
        layout.addWidget(buttons)


class Worker(QObject):
    log = Signal(str)
    progress = Signal(int, int, str)
    verification = Signal(str, str)
    finished = Signal(bool, str, list)

    def __init__(self, routers, username, password, secret):
        super().__init__()
        self.routers = list(routers)
        self.username = username
        self.password = password
        self.secret = secret
        self.stop_requested = False
        self.continue_event = None
        self.connection = None

    def stop(self):
        self.stop_requested = True
        if self.continue_event:
            self.continue_event.set()
        if self.connection:
            try:
                self.connection.disconnect()
            except Exception:
                pass

    def tcp_check(self, port):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=5):
                return True, ""
        except OSError as exc:
            return False, str(exc)

    def connect_router(self, name, port):
        ok, error = self.tcp_check(port)
        if not ok:
            raise ConnectionError(
                f"Impossible d'atteindre GNS3 sur 127.0.0.1:{port}.\n"
                f"Vérifiez que {name} est démarré dans GNS3.\n\n{error}"
            )

        username = self.username.strip() or None
        password = self.password or None
        secret = self.secret or password

        params = {
            "device_type": "cisco_ios_telnet",
            "host": "127.0.0.1",
            "port": port,
            "username": username,
            "password": password,
            "secret": secret,
            "conn_timeout": 20,
            "banner_timeout": 60,
            "auth_timeout": 30,
            "blocking_timeout": 30,
            "fast_cli": False,
            "global_delay_factor": 1,
            "session_log": str(LOG_DIR / f"{name}_netmiko.log"),
        }

        self.log.emit(f"[{name}] Port GNS3 accessible : 127.0.0.1:{port}")
        conn = ConnectHandler(**params)
        self.connection = conn

        # Sortir d'un éventuel mode de configuration.
        try:
            conn.write_channel("\x03")
            time.sleep(0.2)
        except Exception:
            pass

        if not conn.check_enable_mode():
            self.log.emit(f"[{name}] Passage en mode privilégié...")
            conn.enable()
        else:
            self.log.emit(f"[{name}] Déjà en mode privilégié.")

        return conn

    @Slot()
    def run(self):
        if ConnectHandler is None:
            self.finished.emit(
                False,
                "Netmiko n'est pas installé.\n"
                "Installez-le avec : python3 -m pip install --upgrade netmiko",
                [],
            )
            return

        done = []
        total = len(self.routers)

        for index, name in enumerate(self.routers, 1):
            if self.stop_requested:
                break

            conn = None
            try:
                self.progress.emit(index - 1, total, f"Connexion à {name}...")
                self.log.emit(f"[{name}] Début du traitement.")
                conn = self.connect_router(name, ROUTERS[name])

                self.log.emit(f"[{name}] Configuration RIP v2.")
                output = conn.send_config_set(
                    [
                        "router rip",
                        "version 2",
                        "no auto-summary",
                        "network 10.0.0.0",
                    ],
                    cmd_verify=False,
                    read_timeout=30,
                )
                logging.info("%s CONFIG:\n%s", name, output)

                # Garantie du mode privilégié après la configuration.
                try:
                    conn.send_command_timing(
                        "end", strip_prompt=False, strip_command=False, read_timeout=20
                    )
                except Exception:
                    pass
                if not conn.check_enable_mode():
                    conn.enable()

                time.sleep(0.3)
                conn.clear_buffer()

                protocols = conn.send_command_timing(
                    "show ip protocols",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=30,
                )
                routes = conn.send_command_timing(
                    "show ip route rip",
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=30,
                )

                verification = (
                    f"===== {name} =====\n"
                    f"===== show ip protocols =====\n{protocols}\n\n"
                    f"===== show ip route rip =====\n{routes}\n"
                )
                logging.info("%s VERIFICATION:\n%s", name, verification)

                done.append(name)
                self.progress.emit(index, total, f"{name} terminé.")
                self.log.emit(f"[{name}] RIP vérifié.")

                self.verification.emit(name, verification)

                self.continue_event = threading.Event()
                while not self.continue_event.is_set():
                    if self.stop_requested:
                        break
                    self.continue_event.wait(0.1)
                self.continue_event = None

                if self.stop_requested:
                    break

            except Exception as exc:
                logging.exception("Erreur %s", name)
                self.log.emit(f"[{name}] ERREUR {type(exc).__name__}: {exc}")
                self.finished.emit(
                    False,
                    f"Erreur sur {name} :\n\n{type(exc).__name__}: {exc}\n\n"
                    f"Consultez logs/{name}_netmiko.log",
                    done,
                )
                return
            finally:
                if conn:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
                self.connection = None

        if self.stop_requested:
            self.finished.emit(False, "Opération arrêtée.", done)
        else:
            self.finished.emit(
                True,
                f"RIP v2 configuré sur {len(done)} routeur(s).",
                done,
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cisco TP10 — Routage RIP v2")
        self.resize(1150, 760)
        self.setStyleSheet(QSS)
        self.thread = None
        self.worker = None
        self.running = False
        self.build_ui()

    def build_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = QFrame()
        header.setObjectName("Header")
        h = QHBoxLayout(header)
        logo = QLabel()
        logo.setFixedSize(150, 85)
        if LOGO_FILE.exists():
            logo.setPixmap(QPixmap(str(LOGO_FILE)).scaled(
                logo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            logo.setText("CISCO")
        h.addWidget(logo)

        titles = QVBoxLayout()
        title = QLabel("TP10 — Routage RIP v2")
        title.setObjectName("Title")
        titles.addWidget(title)
        sub = QLabel(
            "Domaine RIP • R9 / R5 / R6 / R8 / ASBR • "
            "Préparation de la redistribution RIP ↔ OSPF"
        )
        sub.setObjectName("Subtitle")
        titles.addWidget(sub)
        h.addLayout(titles)
        h.addStretch()
        root.addWidget(header)

        main = QHBoxLayout()
        left = QFrame()
        left.setObjectName("Card")
        ll = QVBoxLayout(left)

        sec = QLabel("Routeurs RIP à configurer")
        sec.setObjectName("SectionTitle")
        ll.addWidget(sec)

        self.select_all = QCheckBox("Sélectionner tous les routeurs")
        self.select_all.toggled.connect(self.toggle_all)
        ll.addWidget(self.select_all)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.NoSelection)
        self.list.setUniformItemSizes(True)
        self.list.setMinimumWidth(330)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for name in ROUTER_ORDER:
            item = QListWidgetItem(f"{name}    •    RIP v2")
            item.setData(Qt.UserRole, name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            item.setSizeHint(QSize(0, 42))
            self.list.addItem(item)

        self.list.itemChanged.connect(self.selection_changed)
        ll.addWidget(self.list, 1)

        row = QHBoxLayout()
        none = QPushButton("Tout désélectionner")
        none.clicked.connect(self.select_none)
        row.addWidget(none)
        self.start_btn = QPushButton("Configurer RIP")
        self.start_btn.setObjectName("Primary")
        self.start_btn.clicked.connect(self.start)
        row.addWidget(self.start_btn)
        ll.addLayout(row)

        right = QFrame()
        right.setObjectName("Card")
        rl = QVBoxLayout(right)
        sec2 = QLabel("Progression")
        sec2.setObjectName("SectionTitle")
        rl.addWidget(sec2)
        self.progress = QProgressBar()
        rl.addWidget(self.progress)
        self.status = QLabel("Prêt.")
        self.status.setStyleSheet("color:#9aa8b2;")
        rl.addWidget(self.status)
        sec3 = QLabel("Journal")
        sec3.setObjectName("SectionTitle")
        rl.addWidget(sec3)
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 9))
        rl.addWidget(self.log_box, 1)
        self.stop_btn = QPushButton("Arrêter")
        self.stop_btn.setObjectName("Danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        rl.addWidget(self.stop_btn)

        main.addWidget(left, 1)
        main.addWidget(right, 1)
        root.addLayout(main, 1)

        footer = QLabel(
            f"Log : {LOG_FILE} • Ports GNS3 intégrés • "
            "Aucune redistribution OSPF dans cette étape"
        )
        footer.setStyleSheet("color:#61717b; font-size:10px;")
        root.addWidget(footer)

    def selected(self):
        return [
            self.list.item(i).data(Qt.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.Checked
        ]

    def toggle_all(self, checked):
        self.list.blockSignals(True)
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(state)
        self.list.blockSignals(False)

    def select_none(self):
        self.select_all.blockSignals(True)
        self.select_all.setChecked(False)
        self.select_all.blockSignals(False)
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(Qt.Unchecked)
        self.list.blockSignals(False)

    def selection_changed(self, _item):
        count = sum(
            self.list.item(i).checkState() == Qt.Checked
            for i in range(self.list.count())
        )
        self.select_all.blockSignals(True)
        self.select_all.setChecked(count == self.list.count())
        self.select_all.blockSignals(False)

    def append_log(self, msg):
        stamp = time.strftime("%H:%M:%S")
        self.log_box.appendPlainText(f"[{stamp}] {msg}")
        logging.info(msg)

    def start(self):
        if self.running:
            return
        routers = self.selected()
        if not routers:
            QMessageBox.warning(self, "Aucun routeur", "Sélectionnez au moins un routeur.")
            return

        dlg = CredentialsDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        username, password, secret = dlg.values()

        confirm = QMessageBox.question(
            self, "Confirmer RIP v2",
            "Routeurs : " + ", ".join(routers) + "\n\n"
            "Commandes :\n"
            "router rip\n"
            " version 2\n"
            " no auto-summary\n"
            " network 10.0.0.0\n\n"
            "Aucune redistribution OSPF ne sera configurée.\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self.running = True
        self.start_btn.setEnabled(False)
        self.select_all.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setValue(0)
        self.log_box.clear()
        self.append_log("=== DÉBUT RIP v2 ===")

        self.thread = QThread(self)
        self.worker = Worker(routers, username, password, secret)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.progress.connect(self.update_progress)
        self.worker.verification.connect(self.show_verification)
        self.worker.finished.connect(self.finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup)
        self.thread.start()

    @Slot(str)
    def append_log(self, msg):
        stamp = time.strftime("%H:%M:%S")
        self.log_box.appendPlainText(f"[{stamp}] {msg}")
        logging.info(msg)

    @Slot(int, int, str)
    def update_progress(self, current, total, message):
        self.progress.setValue(int(current * 100 / total) if total else 0)
        self.status.setText(message)

    @Slot(str, str)
    def show_verification(self, name, output):
        dlg = VerificationDialog(name, output, self)
        result = dlg.exec()
        if not self.worker:
            return
        if result == QDialog.Accepted:
            self.append_log(f"[{name}] Validation reçue.")
            if self.worker.continue_event:
                self.worker.continue_event.set()
        else:
            self.append_log(f"[{name}] Arrêt demandé.")
            self.worker.stop()

    @Slot(bool, str, list)
    def finished(self, success, message, done):
        self.status.setText("Terminé." if success else "Arrêt / erreur.")
        self.append_log("=== FIN ===")
        box = QMessageBox.information if success else QMessageBox.critical
        box(
            self, "RIP v2",
            message + "\n\nRouteurs traités : " + (", ".join(done) or "aucun")
        )

    def stop(self):
        if self.worker:
            self.worker.stop()
        self.stop_btn.setEnabled(False)

    def cleanup(self):
        self.running = False
        self.start_btn.setEnabled(True)
        self.select_all.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cisco TP10 RIP v2")
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
