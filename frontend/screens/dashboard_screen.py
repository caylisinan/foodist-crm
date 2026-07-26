from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QMessageBox
from api_client import ApiClient, ApiError


class DashboardScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state

        layout = QVBoxLayout(self)
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Etkinliğin genel durumu.", objectName="hint"))

        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        layout.addLayout(self.grid)
        layout.addStretch()

        self.cards = {}
        self.metrics_order = [
            ("total_buyers", "Toplam Buyer"),
            ("total_participants", "Toplam Katılımcı"),
            ("total_matches", "Toplam Eşleşme"),
            ("pending_approval", "Onay Bekleyen"),
            ("approved", "Onaylanan"),
            ("scheduled_meetings", "Planlanan Toplantı"),
            ("completed_meetings", "Tamamlanan Toplantı"),
            ("no_show_rate", "No-Show Oranı (%)"),
        ]
        for i, (key, label) in enumerate(self.metrics_order):
            card = QFrame()
            card.setStyleSheet("QFrame { background:#FFFFFF; border:1px solid #E3DCC8; border-radius:3px; }")
            card_layout = QVBoxLayout(card)
            value_lbl = QLabel("-")
            value_lbl.setStyleSheet("font-size:26px; font-weight:bold; color:#1F2A24;")
            label_lbl = QLabel(label)
            label_lbl.setStyleSheet("color:#77705F; font-size:11px; text-transform:uppercase;")
            card_layout.addWidget(value_lbl)
            card_layout.addWidget(label_lbl)
            self.grid.addWidget(card, i // 4, i % 4)
            self.cards[key] = value_lbl

        self.refresh()

    def refresh(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        try:
            data = self.api.get_dashboard(event_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        for key, _ in self.metrics_order:
            self.cards[key].setText(str(data.get(key, "-")))
