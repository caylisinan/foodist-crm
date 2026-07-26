from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QCheckBox, QLabel,
    QMessageBox, QFormLayout, QGroupBox
)
from api_client import ApiClient, ApiError


class SettingsScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state

        layout = QVBoxLayout(self)
        title = QLabel("Ayarlar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("SMTP e-posta ayarları ve eşleştirme varsayılanları.", objectName="hint"))

        smtp_box = QGroupBox("E-posta (SMTP) Ayarları")
        smtp_layout = QFormLayout(smtp_box)
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.from_name_input = QLineEdit()
        self.from_email_input = QLineEdit()
        self.secure_check = QCheckBox("465 portu için SSL/TLS kullan (Gmail için genelde 587 + kapalı bırakın)")

        smtp_layout.addRow("SMTP Sunucu", self.host_input)
        smtp_layout.addRow("Port", self.port_input)
        smtp_layout.addRow("Kullanıcı Adı", self.user_input)
        smtp_layout.addRow("Şifre / Uygulama Şifresi", self.pass_input)
        smtp_layout.addRow("Gönderen Adı", self.from_name_input)
        smtp_layout.addRow("Gönderen E-posta", self.from_email_input)
        smtp_layout.addRow(self.secure_check)
        layout.addWidget(smtp_box)

        weights_box = QGroupBox("Eşleştirme Varsayılanları")
        weights_layout = QFormLayout(weights_box)
        self.weight_product_input = QLineEdit()
        self.weight_sector_input = QLineEdit()
        self.weight_country_input = QLineEdit()
        self.threshold_input = QLineEdit()
        self.max_meetings_input = QLineEdit()
        self.max_minutes_input = QLineEdit()
        weights_layout.addRow("Ürün Ağırlığı (%)", self.weight_product_input)
        weights_layout.addRow("Sektör Ağırlığı (%)", self.weight_sector_input)
        weights_layout.addRow("Ülke Ağırlığı (%)", self.weight_country_input)
        weights_layout.addRow("Eşik Skor", self.threshold_input)
        weights_layout.addRow("Varsayılan Buyer Toplantı Limiti", self.max_meetings_input)
        weights_layout.addRow("Varsayılan Buyer Dakika Limiti", self.max_minutes_input)
        layout.addWidget(weights_box)

        save_btn = QPushButton("Ayarları Kaydet")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)
        layout.addStretch()

        self.load_settings()

    def load_settings(self):
        try:
            s = self.api.get_settings()
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self.host_input.setText(s.get("smtp_host") or "")
        self.port_input.setText(s.get("smtp_port") or "587")
        self.user_input.setText(s.get("smtp_user") or "")
        self.pass_input.setText(s.get("smtp_pass") or "")
        self.from_name_input.setText(s.get("smtp_from_name") or "")
        self.from_email_input.setText(s.get("smtp_from_email") or "")
        self.secure_check.setChecked((s.get("smtp_secure") or "false") == "true")
        self.weight_product_input.setText(s.get("weight_product") or "50")
        self.weight_sector_input.setText(s.get("weight_sector") or "30")
        self.weight_country_input.setText(s.get("weight_country") or "20")
        self.threshold_input.setText(s.get("match_threshold") or "40")
        self.max_meetings_input.setText(s.get("default_max_meetings") or "4")
        self.max_minutes_input.setText(s.get("default_max_minutes") or "60")

    def save(self):
        payload = {
            "smtp_host": self.host_input.text().strip(),
            "smtp_port": self.port_input.text().strip(),
            "smtp_user": self.user_input.text().strip(),
            "smtp_pass": self.pass_input.text(),
            "smtp_from_name": self.from_name_input.text().strip(),
            "smtp_from_email": self.from_email_input.text().strip(),
            "smtp_secure": "true" if self.secure_check.isChecked() else "false",
            "weight_product": self.weight_product_input.text().strip(),
            "weight_sector": self.weight_sector_input.text().strip(),
            "weight_country": self.weight_country_input.text().strip(),
            "match_threshold": self.threshold_input.text().strip(),
            "default_max_meetings": self.max_meetings_input.text().strip(),
            "default_max_minutes": self.max_minutes_input.text().strip(),
        }
        try:
            self.api.update_settings(payload)
        except ApiError as e:
            QMessageBox.critical(self, "Kaydedilemedi", str(e))
            return
        QMessageBox.information(self, "Kaydedildi", "Ayarlar kaydedildi.")

    def refresh(self):
        self.load_settings()
