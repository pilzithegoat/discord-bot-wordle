import sys
import os
import subprocess
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTextEdit, QMessageBox, QGroupBox, QScrollArea)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

class BotLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Wordle Bot Launcher")
        self.setMinimumSize(1000, 800)
        
        # Hauptwidget und Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # ScrollArea für Konfiguration
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Bot Konfiguration
        bot_group = QGroupBox("Bot Konfiguration")
        bot_layout = QVBoxLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Discord Bot Token (ohne Anführungszeichen)")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        bot_layout.addWidget(QLabel("Bot Token:"))
        bot_layout.addWidget(self.token_input)
        
        bot_group.setLayout(bot_layout)
        scroll_layout.addWidget(bot_group)
        
        # Website Konfiguration
        web_group = QGroupBox("Website Konfiguration")
        web_layout = QVBoxLayout()
        
        self.flask_key_input = QLineEdit()
        self.flask_key_input.setPlaceholderText("Flask Secret Key (ohne Anführungszeichen)")
        web_layout.addWidget(QLabel("Flask Secret Key:"))
        web_layout.addWidget(self.flask_key_input)
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Discord Client ID (ohne Anführungszeichen)")
        web_layout.addWidget(QLabel("Discord Client ID:"))
        web_layout.addWidget(self.client_id_input)
        
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Discord Client Secret (ohne Anführungszeichen)")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        web_layout.addWidget(QLabel("Discord Client Secret:"))
        web_layout.addWidget(self.client_secret_input)
        
        self.redirect_uri_input = QLineEdit()
        self.redirect_uri_input.setPlaceholderText("Redirect URI (z.B. http://localhost:5000/callback)")
        web_layout.addWidget(QLabel("Redirect URI:"))
        web_layout.addWidget(self.redirect_uri_input)
        
        web_group.setLayout(web_layout)
        scroll_layout.addWidget(web_group)
        
        # Umgebungsvariablen
        env_group = QGroupBox("Umgebungsvariablen")
        env_layout = QVBoxLayout()
        
        self.env_input = QLineEdit()
        self.env_input.setPlaceholderText("Zusätzliche Umgebungsvariablen (z.B. DATABASE_URL=sqlite:///wordle.db)")
        env_layout.addWidget(QLabel("Umgebungsvariablen:"))
        env_layout.addWidget(self.env_input)
        
        env_group.setLayout(env_layout)
        scroll_layout.addWidget(env_group)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Status und Console
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.uptime_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.uptime_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        status_layout.addWidget(self.console)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Bot")
        self.start_button.clicked.connect(self.start_bot)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Variablen für den Bot-Prozess
        self.bot_process = None
        self.start_time = None
        self.uptime_timer = QTimer()
        self.uptime_timer.timeout.connect(self.update_uptime)
        
        # Lade gespeicherte Konfiguration
        self.load_config()
        
    def load_config(self):
        try:
            if os.path.exists("bot_config.txt"):
                with open("bot_config.txt", "r") as f:
                    config = {}
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            config[key] = value
                    
                    self.token_input.setText(config.get("DISCORD_TOKEN", ""))
                    self.flask_key_input.setText(config.get("FLASK_KEY", ""))
                    self.client_id_input.setText(config.get("CLIENT_ID", ""))
                    self.client_secret_input.setText(config.get("CLIENT_SECRET", ""))
                    self.redirect_uri_input.setText(config.get("REDIRECT_URI", ""))
                    self.env_input.setText(config.get("ENV_VARS", ""))
        except Exception as e:
            self.console.append(f"Fehler beim Laden der Konfiguration: {str(e)}")
            
    def save_config(self):
        try:
            with open("bot_config.txt", "w") as f:
                f.write(f"DISCORD_TOKEN={self.token_input.text()}\n")
                f.write(f"FLASK_KEY={self.flask_key_input.text()}\n")
                f.write(f"CLIENT_ID={self.client_id_input.text()}\n")
                f.write(f"CLIENT_SECRET={self.client_secret_input.text()}\n")
                f.write(f"REDIRECT_URI={self.redirect_uri_input.text()}\n")
                f.write(f"ENV_VARS={self.env_input.text()}\n")
        except Exception as e:
            self.console.append(f"Fehler beim Speichern der Konfiguration: {str(e)}")
            
    def start_bot(self):
        if not self.token_input.text():
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Bot-Token ein!")
            return
            
        # Speichere Konfiguration
        self.save_config()
        
        # Setze Umgebungsvariablen
        env = os.environ.copy()
        env["DISCORD_TOKEN"] = self.token_input.text()
        env["FLASK_KEY"] = self.flask_key_input.text()
        env["CLIENT_ID"] = self.client_id_input.text()
        env["CLIENT_SECRET"] = self.client_secret_input.text()
        env["REDIRECT_URI"] = self.redirect_uri_input.text()
        
        # Füge zusätzliche Umgebungsvariablen hinzu
        for var in self.env_input.text().split():
            if "=" in var:
                key, value = var.split("=", 1)
                env[key] = value
        
        try:
            # Starte den Bot-Prozess
            self.bot_process = subprocess.Popen(
                [sys.executable, "-u", "main.py"],  # -u für unbuffered output
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.start_time = datetime.now()
            self.uptime_timer.start(1000)  # Update jede Sekunde
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Starte Thread zum Lesen der Ausgabe
            QTimer.singleShot(100, self.read_output)
            
            self.console.append("Bot wird gestartet...")
        except Exception as e:
            self.console.append(f"Fehler beim Starten des Bots: {str(e)}")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
    def stop_bot(self):
        if self.bot_process:
            self.bot_process.terminate()
            self.bot_process = None
            self.uptime_timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.console.append("Bot wurde gestoppt.")
            
    def read_output(self):
        if self.bot_process and self.bot_process.poll() is None:
            try:
                output = self.bot_process.stdout.readline()
                if output:
                    self.console.append(output.strip())
                    # Scroll zum Ende
                    self.console.verticalScrollBar().setValue(
                        self.console.verticalScrollBar().maximum()
                    )
                QTimer.singleShot(100, self.read_output)
            except Exception as e:
                self.console.append(f"Fehler beim Lesen der Ausgabe: {str(e)}")
                
    def update_uptime(self):
        if self.start_time:
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
    def closeEvent(self, event):
        self.stop_bot()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BotLauncher()
    window.show()
    sys.exit(app.exec()) 