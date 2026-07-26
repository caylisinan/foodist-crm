"""
Foodist İstanbul — Hosted Buyer B2B CRM
Masaüstü Arayüzü (PySide6) Giriş Noktası.
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QStackedWidget, QComboBox,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)

from api_client import ApiClient, ApiError
from styles import APP_STYLE
from screens.login_screen import LoginScreen
from screens.buyers_screen import BuyersScreen
from screens.participants_screen import ParticipantsScreen
from screens.import_screen import ImportScreen
from screens.matching_screen import MatchingScreen
from screens.calendar_screen import CalendarScreen
from screens.dashboard_screen import DashboardScreen
from screens.reports_screen import ReportsScreen
from screens.settings_screen import SettingsScreen


MENU_ITEMS = [
    ("dashboard", "📊 Dashboard", DashboardScreen, False),
    ("buyers", "👤 Hosted Buyer", BuyersScreen, True),
    ("participants", "🏢 Katılımcı Firma", ParticipantsScreen, True),
    ("import", "📥 Excel İçe Aktar", ImportScreen, True),
    ("matching", "🔗 Eşleştirme / Onaylar", MatchingScreen, True),
    ("calendar", "🗓 Takvim / Toplantı", CalendarScreen, False),
    ("reports", "📄 Raporlar", ReportsScreen, False),
    ("settings", "⚙ Ayarlar", SettingsScreen, True),
]


class NewEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Etkinlik (Fuar Edisyonu)")
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.venue_input = QLineEdit()
        layout.addRow("Etkinlik Adı *", self.name_input)
        layout.addRow("Mekan", self.venue_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return self.name_input.text().strip(), self.venue_input.text().strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Foodist İstanbul — Hosted Buyer B2B CRM")
        self.resize(1280, 840)

        self.api = ApiClient()
        self.current_user = None
        self.app_state = {"event_id": None}
        self.screen_instances = {}

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen(self.api)
        self.login_screen.login_success.connect(self.on_login_success)
        self.stack.addWidget(self.login_screen)

        self.app_widget = None

    def on_login_success(self, user):
        self.current_user = user
        self.build_app_widget()
        self.stack.addWidget(self.app_widget)
        self.stack.setCurrentWidget(self.app_widget)
        self.load_events()

    def build_app_widget(self):
        widget = QWidget()
        outer = QHBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("background:#1F2A24;")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 16, 0, 16)

        brand = QLabel("FOODIST İSTANBUL")
        brand.setStyleSheet("color:white; font-weight:bold; font-size:14px; padding:0 16px;")
        side_layout.addWidget(brand)

        event_row = QWidget()
        event_layout = QVBoxLayout(event_row)
        event_layout.setContentsMargins(16, 12, 16, 12)
        event_label = QLabel("Etkinlik")
        event_label.setStyleSheet("color:#D97B5C; font-size:11px; text-transform:uppercase;")
        self.event_combo = QComboBox()
        self.event_combo.currentIndexChanged.connect(self.on_event_changed)
        new_event_btn = QPushButton("+ Yeni Etkinlik")
        new_event_btn.clicked.connect(self.create_event)
        event_layout.addWidget(event_label)
        event_layout.addWidget(self.event_combo)
        event_layout.addWidget(new_event_btn)
        side_layout.addWidget(event_row)

        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet("""
            QListWidget { background:#1F2A24; border:none; color:#D8D0BC; font-size:13px; }
            QListWidget::item { padding:12px 16px; }
            QListWidget::item:selected { background:#A23B2E; color:white; }
        """)
        self.menu_keys = []
        for key, label, screen_class, admin_only in MENU_ITEMS:
            if admin_only and self.current_user.get("role") != "admin":
                continue
            self.menu_list.addItem(QListWidgetItem(label))
            self.menu_keys.append((key, screen_class))
        self.menu_list.currentRowChanged.connect(self.on_menu_changed)
        side_layout.addWidget(self.menu_list, stretch=1)

        role_label = QLabel(f"Rol: {self.current_user.get('role', '?').upper()}")
        role_label.setStyleSheet("color:#B9B2A2; font-size:11px; padding:0 16px;")
        side_layout.addWidget(role_label)
        user_label = QLabel(f"Kullanıcı: {self.current_user.get('username', '?')}")
        user_label.setStyleSheet("color:#B9B2A2; font-size:11px; padding:0 16px;")
        side_layout.addWidget(user_label)

        logout_btn = QPushButton("Çıkış Yap")
        logout_btn.clicked.connect(self.logout)
        side_layout.addWidget(logout_btn)

        outer.addWidget(sidebar)

        self.content_stack = QStackedWidget()
        outer.addWidget(self.content_stack, stretch=1)

        for key, screen_class in self.menu_keys:
            instance = screen_class(self.api, self.app_state)
            self.screen_instances[key] = instance
            self.content_stack.addWidget(instance)

        if self.menu_list.count() > 0:
            self.menu_list.setCurrentRow(0)

        self.app_widget = widget

    def on_menu_changed(self, row):
        if row < 0 or row >= len(self.menu_keys):
            return
        key, _ = self.menu_keys[row]
        self.content_stack.setCurrentWidget(self.screen_instances[key])
        screen = self.screen_instances[key]
        if hasattr(screen, "refresh"):
            screen.refresh()
        elif hasattr(screen, "refresh_all"):
            screen.refresh_all()

    def load_events(self):
        try:
            events = self.api.list_events()
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        self.event_combo.blockSignals(True)
        self.event_combo.clear()
        for e in events:
            self.event_combo.addItem(e["name"], e["id"])
        self.event_combo.blockSignals(False)

        if events:
            self.app_state["event_id"] = events[0]["id"]
        else:
            self.app_state["event_id"] = None
            self.create_event(is_first=True)

    def on_event_changed(self, index):
        if index < 0:
            return
        self.app_state["event_id"] = self.event_combo.currentData()
        current = self.content_stack.currentWidget()
        if current and hasattr(current, "refresh"):
            current.refresh()
        elif current and hasattr(current, "refresh_all"):
            current.refresh_all()

    def create_event(self, is_first=False):
        dialog = NewEventDialog(self)
        if is_first:
            QMessageBox.information(
                self, "Etkinlik Bulunamadı",
                "Sistemde henüz bir etkinlik (fuar edisyonu) yok. Lütfen ilk etkinliği oluşturun.")
        if dialog.exec() != QDialog.Accepted:
            return
        name, venue = dialog.get_data()
        if not name:
            QMessageBox.warning(self, "Eksik Bilgi", "Etkinlik adı zorunludur.")
            return
        try:
            self.api.create_event(name, venue=venue or None)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self.load_events()

    def logout(self):
        if QMessageBox.question(self, "Çıkış", "Çıkış yapmak istediğinize emin misiniz?") != QMessageBox.Yes:
            return
        self.stack.removeWidget(self.app_widget)
        self.app_widget.deleteLater()
        self.app_widget = None
        self.screen_instances = {}
        self.current_user = None
        self.app_state = {"event_id": None}
        self.stack.setCurrentWidget(self.login_screen)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
