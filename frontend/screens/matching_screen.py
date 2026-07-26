from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QHeaderView, QAbstractItemView
)
from api_client import ApiClient, ApiError

STATUS_OPTIONS = [
    "Tümü", "Önerildi", "Onay Bekliyor", "Buyer Onayladı", "Katılımcı Onayladı",
    "Karşılıklı Onaylandı", "Toplantı Planlandı", "Tamamlandı", "No Show", "Reddedildi",
]


class MatchingScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state
        self.matches_cache = []

        layout = QVBoxLayout(self)
        title = QLabel("Akıllı Eşleştirme Motoru")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "Ağırlıkları ayarlayıp eşleştirmeleri oluşturun, ardından listeden onaylayın.",
            objectName="hint"))

        settings_box = QGroupBox("Eşleştirme Ayarları")
        settings_layout = QFormLayout(settings_box)

        self.weight_product = QSpinBox(); self.weight_product.setRange(0, 100); self.weight_product.setValue(50)
        self.weight_sector = QSpinBox(); self.weight_sector.setRange(0, 100); self.weight_sector.setValue(30)
        self.weight_country = QSpinBox(); self.weight_country.setRange(0, 100); self.weight_country.setValue(20)
        self.threshold = QSpinBox(); self.threshold.setRange(0, 100); self.threshold.setValue(40)

        self.country_mode = QComboBox()
        self.country_mode.addItem("Filtre yok (uluslararası çeşitlilik ödüllenir)", "none")
        self.country_mode.addItem("Aynı ülkeleri eşleştir", "same_only")
        self.country_mode.addItem("Aynı ülkeleri hariç tut", "exclude_same")

        settings_layout.addRow("Ürün Uyumu Ağırlığı (%)", self.weight_product)
        settings_layout.addRow("Sektör Uyumu Ağırlığı (%)", self.weight_sector)
        settings_layout.addRow("Ülke Uyumu Ağırlığı (%)", self.weight_country)
        settings_layout.addRow("Eşik Skor (altındakiler önerilmez)", self.threshold)
        settings_layout.addRow("Ülke Filtresi", self.country_mode)

        generate_btn = QPushButton("Eşleştirmeleri Oluştur")
        generate_btn.setObjectName("primary")
        generate_btn.clicked.connect(self.generate_matches)
        settings_layout.addRow(generate_btn)

        layout.addWidget(settings_box)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Durum Filtresi:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(STATUS_OPTIONS)
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh)
        filter_row.addWidget(refresh_btn)
        self.approve_btn = QPushButton("Seçilenleri Onayla (Mail Gönder)")
        self.approve_btn.setObjectName("primary")
        self.approve_btn.clicked.connect(self.approve_selected)
        filter_row.addWidget(self.approve_btn)
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Buyer", "Katılımcı", "Ürün Skoru", "Sektör Skoru", "Toplam Skor", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.table)

        self.refresh()

    def generate_matches(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            QMessageBox.warning(self, "Etkinlik Seçilmedi", "Önce üstten bir etkinlik seçin.")
            return

        payload = {
            "event_id": event_id,
            "weight_product": self.weight_product.value(),
            "weight_sector": self.weight_sector.value(),
            "weight_country": self.weight_country.value(),
            "country_mode": self.country_mode.currentData(),
            "threshold": self.threshold.value(),
        }
        try:
            result = self.api.generate_matches(payload)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        QMessageBox.information(
            self, "Eşleştirme Tamamlandı",
            f"{result['created']} yeni eşleşme oluşturuldu.\n"
            f"Zaten var olan: {result['skipped_existing_pairs']}\n"
            f"Eşik altında kalan: {result['below_threshold']}\n"
            f"Ülke filtresiyle elenen: {result['filtered_by_country_rule']}"
        )
        self.refresh()

    def refresh(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        status = self.status_filter.currentText()
        try:
            self.matches_cache = self.api.list_matches(event_id, status if status != "Tümü" else None)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        self.table.setRowCount(len(self.matches_cache))
        for row, m in enumerate(self.matches_cache):
            self.table.setItem(row, 0, QTableWidgetItem(m["buyer_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(m["participant_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(m["product_score"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(m["sector_score"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(m["total_score"])))
            self.table.setItem(row, 5, QTableWidgetItem(m["status"]))

    def approve_selected(self):
        rows = sorted(set(idx.row() for idx in self.table.selectionModel().selectedRows()))
        if not rows:
            QMessageBox.warning(self, "Seçim Yok", "Onaylamak için en az bir eşleşme seçin.")
            return
        match_ids = [self.matches_cache[r]["id"] for r in rows]

        try:
            result = self.api.approve_matches(match_ids)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        lines = []
        for r in result["results"]:
            if not r.get("ok"):
                lines.append(f"Eşleşme {r['match_id']}: {r.get('error')}")
                continue
            b_status = "gönderildi" if r["buyer_mail_sent"] else f"BAŞARISIZ ({r['buyer_mail_error']})"
            p_status = "gönderildi" if r["participant_mail_sent"] else f"BAŞARISIZ ({r['participant_mail_error']})"
            lines.append(f"Eşleşme {r['match_id']} — Buyer maili: {b_status} | Katılımcı maili: {p_status}")

        QMessageBox.information(self, "Onay Sonucu", "\n".join(lines))
        self.refresh()
