from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal

from api_client import ApiClient, ApiError


class LoginScreen(QWidget):
    login_success = Signal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.setStyleSheet("""
            QWidget { background:#F7F3EA; font-family: Arial; }
            QFrame#card { background:#FFFFFF; border:1px solid #E3DCC8; border-radius:4px; }
            QLabel#title { font-size:20px; font-weight:bold; color:#1F2A24; }
            QLabel#subtitle { color:#77705F; font-size:12px; }
            QLineEdit { border:1px solid #D8D0BC; padding:8px; border-radius:2px; background:#F7F3EA; }
            QPushButton { background:#A23B2E; color:white; padding:10px; border-radius:2px; font-weight:bold; }
            QPushButton:hover { background:#8A3226; }
        """)
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(360)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Foodist İstanbul")
        title.setObjectName("title")
        subtitle = QLabel("Hosted Buyer B2B CRM")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.handle_login)

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)

        login_btn = QPushButton("Giriş Yap")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        hint = QLabel("İlk kurulum: admin / admin123")
        hint.setStyleSheet("color:#9A4B3F; font-size:11px;")
        layout.addWidget(hint)

        outer.addWidget(card)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Eksik Bilgi", "Kullanıcı adı ve şifre gerekli.")
            return
        try:
            user = self.api.login(username, password)
            self.login_success.emit(user)
        except ApiError as e:
            QMessageBox.critical(self, "Giriş Başarısız", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Bağlantı Hatası",
                                  f"Backend'e bağlanılamadı. Backend çalışıyor mu?\n\n{e}")
