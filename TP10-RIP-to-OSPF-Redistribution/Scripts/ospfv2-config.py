#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TP10 - Configuration OSPF Area 0
R1/R2/R3/R4/ASBR
- PySide6 GUI dark style Cisco
- Selection d'un ou plusieurs routeurs
- Connexion Telnet GNS3 sans champs Telnet dans l'interface
- Force le mode privilegie
- Configure OSPF + router-id + reseaux
- Affiche les verifications apres chaque routeur et attend validation
- Sauvegarde la configuration avec "copy running-config startup-config"
"""

import sys
import socket
import threading
import logging
from pathlib import Path

from netmiko import ConnectHandler
from PySide6.QtCore import QObject, Signal, Slot, QThread, Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPlainTextEdit, QGroupBox, QCheckBox
)

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "config_tp10_ospf.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

ROUTERS = {
    "R1": {"port": 5009, "rid": "1.1.1.1",
           "networks": ["10.0.1.0", "10.0.2.0", "10.0.3.0"]},
    "R2": {"port": 5010, "rid": "2.2.2.2",
           "networks": ["10.0.1.0", "10.0.4.0", "10.0.5.0", "10.0.7.0"]},
    "R3": {"port": 5011, "rid": "3.3.3.3",
           "networks": ["10.0.3.0", "10.0.4.0", "10.0.6.0"]},
    "R4": {"port": 5012, "rid": "4.4.4.4",
           "networks": ["10.0.2.0", "10.0.5.0", "10.0.6.0", "10.0.8.0"]},
    "ASBR": {"port": 5015, "rid": "5.5.5.5",
             "networks": ["10.0.7.0", "10.0.8.0"]},
}
ORDER = ["R1", "R2", "R3", "R4", "ASBR"]

def commands_for(name):
    d = ROUTERS[name]
    cmds = [
        "router ospf 1",
        f"router-id {d['rid']}",
    ]
    cmds += [f"network {n} 0.0.0.3 area 0" for n in d["networks"]]
    return cmds

def connect_router(name, username, password, secret):
    port = ROUTERS[name]["port"]
    logging.info("Connexion %s sur 127.0.0.1:%s", name, port)
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=5):
            pass
    except OSError as e:
        raise RuntimeError(f"{name}: port GNS3 {port} inaccessible: {e}")

    params = {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": port,
        "username": username or None,
        "password": password or None,
        "secret": secret or password or None,
        "conn_timeout": 20,
        "banner_timeout": 60,
        "auth_timeout": 30,
        "blocking_timeout": 30,
        "fast_cli": False,
        "global_delay_factor": 1,
        "session_log": str(LOG_DIR / f"{name}_ospf_session.log"),
    }
    conn = ConnectHandler(**params)
    conn.write_channel("\x03")
    try:
        if not conn.check_enable_mode():
            conn.enable()
    except Exception:
        conn.enable()
    return conn

class CredentialsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP10 - Identifiants Cisco")
        self.setMinimumWidth(430)
        layout = QFormLayout(self)
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.secret = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.secret.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Mot de passe Telnet (si nécessaire)")
        self.secret.setPlaceholderText("Enable secret (vide = mot de passe)")
        layout.addRow("Username :", self.user)
        layout.addRow("Password :", self.password)
        layout.addRow("Enable secret :", self.secret)
        buttons = QHBoxLayout()
        ok = QPushButton("Continuer")
        cancel = QPushButton("Annuler")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addRow(buttons)

class VerificationDialog(QDialog):
    def __init__(self, router, output):
        super().__init__()
        self.setWindowTitle(f"TP10 - Vérification OSPF - {router}")
        self.resize(900, 650)
        lay = QVBoxLayout(self)
        title = QLabel(f"<b>{router}</b> — vérification terminée")
        title.setFont(QFont("Arial", 14))
        lay.addWidget(title)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText(output)
        lay.addWidget(box)
        info = QLabel("Vérifiez la sortie. Cliquez sur « Valider » pour continuer.")
        lay.addWidget(info)
        buttons = QHBoxLayout()
        btn = QPushButton("Valider et continuer")
        btn.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(btn)
        lay.addLayout(buttons)

class Worker(QObject):
    log = Signal(str)
    progress = Signal(str)
    verification = Signal(str, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, routers, creds):
        super().__init__()
        self.routers = routers
        self.username, self.password, self.secret = creds
        self.continue_event = threading.Event()
        self.stop_event = threading.Event()

    def request_continue(self):
        self.continue_event.set()

    def stop(self):
        self.stop_event.set()
        self.continue_event.set()

    @Slot()
    def run(self):
        try:
            for name in self.routers:
                if self.stop_event.is_set():
                    break
                self.progress.emit(f"Connexion à {name}...")
                conn = None
                try:
                    conn = connect_router(name, self.username, self.password, self.secret)
                    self.log.emit(f"{name}: connecté en mode privilégié.")

                    # Retour propre au mode EXEC privilégié, même si la session était
                    # initialement dans config/interface/submode.
                    conn.send_command_timing("end", strip_prompt=False, strip_command=False)
                    if not conn.check_enable_mode():
                        conn.enable()

                    self.progress.emit(f"Configuration OSPF sur {name}...")
                    cfg = commands_for(name)
                    conn.send_config_set(cfg, cmd_verify=False, read_timeout=30)
                    conn.send_command_timing("end")

                    if not conn.check_enable_mode():
                        conn.enable()

                    self.progress.emit(f"Sauvegarde de {name}...")
                    save = conn.send_command_timing(
                        "copy running-config startup-config",
                        strip_prompt=False,
                        strip_command=False,
                        read_timeout=30,
                    )
                    # IOS peut demander le nom du fichier de destination.
                    if "Destination filename" in save or "destination filename" in save:
                        save += conn.send_command_timing(
                            "\n", strip_prompt=False, strip_command=False, read_timeout=30
                        )
                    # Certains IOS affichent une confirmation.
                    if "[OK]" not in save and "bytes copied" not in save.lower():
                        extra = conn.send_command_timing(
                            "\n", strip_prompt=False, strip_command=False, read_timeout=15
                        )
                        save += extra

                    # Vérification demandée + commandes OSPF utiles.
                    out1 = conn.send_command_timing("show ip ospf neighbor", read_timeout=30)
                    out2 = conn.send_command_timing("show ip route ospf", read_timeout=30)
                    out3 = conn.send_command_timing("show ip protocols", read_timeout=30)
                    output = (
                        f"===== {name} | show ip ospf neighbor =====\n{out1}\n"
                        f"===== {name} | show ip route ospf =====\n{out2}\n"
                        f"===== {name} | show ip protocols =====\n{out3}\n"
                        f"===== {name} | sauvegarde =====\n{save}\n"
                    )
                    logging.info("%s verification:\n%s", name, output)
                    self.verification.emit(name, output)
                    self.continue_event.clear()
                    while not self.stop_event.is_set():
                        if self.continue_event.wait(0.2):
                            break
                    if self.stop_event.is_set():
                        break
                finally:
                    if conn:
                        try:
                            conn.disconnect()
                        except Exception:
                            pass
                    self.log.emit(f"{name}: session fermée.")

            self.progress.emit("Traitement terminé.")
        except Exception as e:
            logging.exception("Erreur OSPF")
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TP10 – Configuration OSPF Area 0 – GNS3")
        self.resize(720, 650)
        self.thread = None
        self.worker = None
        root = QVBoxLayout(self)

        header = QHBoxLayout()
        logo = QLabel()
        logo_path = BASE_DIR / "cisco_logo.jpg"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            logo.setPixmap(pix.scaledToHeight(55))
        else:
            logo.setText("CISCO")
            logo.setFont(QFont("Arial", 18, QFont.Bold))
        header.addWidget(logo)
        title = QLabel("TP10 — Configuration OSPF Area 0")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        desc = QLabel(
            "R1 / R2 / R3 / R4 / ASBR • Router-ID imposé • Area 0 • "
            "Aucune redistribution à cette étape"
        )
        root.addWidget(desc)

        group = QGroupBox("Routeurs à configurer")
        gl = QVBoxLayout(group)
        self.list = QListWidget()
        for name in ORDER:
            item = QListWidgetItem(f"{name}   |   Telnet GNS3 : 127.0.0.1:{ROUTERS[name]['port']}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list.addItem(item)
        gl.addWidget(self.list)
        row = QHBoxLayout()
        allb = QPushButton("Tout sélectionner")
        noneb = QPushButton("Tout désélectionner")
        allb.clicked.connect(lambda: self.set_all(True))
        noneb.clicked.connect(lambda: self.set_all(False))
        row.addWidget(allb); row.addWidget(noneb); row.addStretch()
        gl.addLayout(row)
        root.addWidget(group)

        self.status = QLabel("Prêt.")
        root.addWidget(self.status)
        self.start_btn = QPushButton("Configurer OSPF et sauvegarder")
        self.start_btn.clicked.connect(self.start)
        root.addWidget(self.start_btn)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(1000)
        root.addWidget(self.log_view)

    def set_all(self, checked):
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )

    def start(self):
        routers = [
            self.list.item(i).text().split()[0]
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.CheckState.Checked
        ]
        if not routers:
            QMessageBox.warning(self, "Sélection", "Sélectionnez au moins un routeur.")
            return
        dlg = CredentialsDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self.start_btn.setEnabled(False)
        creds = (dlg.user.text().strip(), dlg.password.text(), dlg.secret.text())
        self.thread = QThread()
        self.worker = Worker(routers, creds)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText)
        self.worker.log.connect(self.append_log)
        self.worker.verification.connect(self.show_verification)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.start_btn.setEnabled(True))
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(str)
    def append_log(self, text):
        self.log_view.appendPlainText(text)
        logging.info(text)

    @Slot(str, str)
    def show_verification(self, router, output):
        dlg = VerificationDialog(router, output)
        dlg.exec()
        if self.worker:
            self.worker.request_continue()

    @Slot(str)
    def show_error(self, msg):
        QMessageBox.critical(self, "Erreur", msg)
        self.status.setText("Erreur — traitement interrompu.")
        if self.worker:
            self.worker.stop()

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(3000)
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background: #111827; color: #E5E7EB; font-family: Arial; font-size: 13px; }
        QDialog { background: #111827; }
        QGroupBox { border: 1px solid #374151; border-radius: 8px; margin-top: 10px; padding: 10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #61A0FF; }
        QPushButton { background: #049FD9; color: white; border: 0; border-radius: 6px; padding: 9px 16px; font-weight: bold; }
        QPushButton:hover { background: #087EA4; }
        QPushButton:disabled { background: #374151; color: #9CA3AF; }
        QLineEdit, QPlainTextEdit, QListWidget { background: #0B1220; border: 1px solid #374151; border-radius: 6px; padding: 6px; }
        QListWidget::item { padding: 8px; }
        QListWidget::item:selected { background: #16324F; }
        QCheckBox { spacing: 8px; }
    """)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
