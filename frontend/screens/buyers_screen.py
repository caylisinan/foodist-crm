from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QFormLayout, QGroupBox
)
from api_client import ApiClient, ApiError


class BuyersScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state
        self.selected_buyer_id = None

        layout = QVBoxLayout(self)
        title = QLabel("Hosted Buyer Yönetimi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Alım heyeti üyelerini ve yetkili kişilerini buradan yönetin.", objectName="hint"))

        form_box = QGroupBox("Buyer Ekle / Güncelle")
        form_layout = QFormLayout(form_box)
        self.company_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.country_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.sector_input = QLineEdit()
        self.products_input = QLineEdit()
        self.products_input.setPlaceholderText("virgülle ayırın: Süt ürünleri, Zeytinyağı")
        self.max_meetings_input = QSpinBox()
        self.max_meetings_input.setRange(1, 20)
        self.max_meetings_input.setValue(4)
        self.max_minutes_input = QSpinBox()
        self.max_minutes_input.setRange(15, 480)
        self.max_minutes_input.setValue(60)

        form_layout.addRow("Firma Adı *", self.company_input)
        form_layout.addRow("Yetkili Ad Soyad", self.contact_input)
        form_layout.addRow("Ülke", self.country_input)
        form_layout.addRow("E-posta", self.email_input)
        form_layout.addRow("Telefon", self.phone_input)
        form_layout.addRow("Sektör", self.sector_input)
        form_layout.addRow("İlgilenilen Ürünler", self.products_input)
        form_layout.addRow("Maks. Toplantı", self.max_meetings_input)
        form_layout.addRow("Maks. Dakika", self.max_minutes_input)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self.save_buyer)
        self.clear_btn = QPushButton("Temizle / Yeni")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.clear_btn)
        form_layout.addRow(btn_row)

        layout.addWidget(form_box)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Firma", "Yetkili", "Ülke", "Sektör", "E-posta", "Limit", "", "CRM Geçmişi"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout.addWidget(self.table)

        self.buyers_cache = []
        self.refresh()

    def refresh(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        try:
            self.buyers_cache = self.api.list_buyers(event_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self.table.setRowCount(len(self.buyers_cache))
        for row, b in enumerate(self.buyers_cache):
            self.table.setItem(row, 0, QTableWidgetItem(b["company_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("contact_name") or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("country") or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(b.get("sector") or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(b.get("contact_email") or "-"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{b['max_meetings']} top. / {b['max_minutes']} dk"))
            del_btn = QPushButton("Sil")
            del_btn.clicked.connect(lambda _, bid=b["id"]: self.delete_buyer(bid))
            self.table.setCellWidget(row, 6, del_btn)

            history_btn = QPushButton("Geçmiş")
            history_btn.clicked.connect(lambda _, bid=b["id"]: self.show_history(bid))
            self.table.setCellWidget(row, 7, history_btn)

    def show_history(self, buyer_id):
        try:
            data = self.api.buyer_history(buyer_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        companies = ", ".join(data["met_companies"]) if data["met_companies"] else "—"
        msg = (
            f"Firma: {data['company_name']}\n\n"
            f"Katıldığı etkinlik sayısı: {data['events_participated']}\n"
            f"Toplam toplantı: {data['total_meetings']}\n"
            f"Tamamlanan: {data['completed_meetings']}\n"
            f"No-Show: {data['no_show_count']}\n\n"
            f"Görüştüğü Firmalar:\n{companies}"
        )
        QMessageBox.information(self, "CRM Geçmişi", msg)

    def on_row_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        b = self.buyers_cache[idx]
        self.selected_buyer_id = b["id"]
        self.company_input.setText(b["company_name"])
        self.contact_input.setText(b.get("contact_name") or "")
        self.country_input.setText(b.get("country") or "")
        self.email_input.setText(b.get("contact_email") or "")
        self.phone_input.setText(b.get("contact_phone") or "")
        self.sector_input.setText(b.get("sector") or "")
        self.products_input.setText(b.get("interested_products") or "")
        self.max_meetings_input.setValue(b.get("max_meetings") or 4)
        self.max_minutes_input.setValue(b.get("max_minutes") or 60)

    def clear_form(self):
        self.selected_buyer_id = None
        for w in [self.company_input, self.contact_input, self.country_input,
                  self.email_input, self.phone_input, self.sector_input, self.products_input]:
            w.clear()
        self.max_meetings_input.setValue(4)
        self.max_minutes_input.setValue(60)
        self.table.clearSelection()

    def save_buyer(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            QMessageBox.warning(self, "Etkinlik Seçilmedi", "Önce üstten bir etkinlik seçin.")
            return
        if not self.company_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Firma adı zorunludur.")
            return

        payload = {
            "event_id": event_id,
            "company_name": self.company_input.text().strip(),
            "contact_name": self.contact_input.text().strip() or None,
            "country": self.country_input.text().strip() or None,
            "contact_email": self.email_input.text().strip() or None,
            "contact_phone": self.phone_input.text().strip() or None,
            "sector": self.sector_input.text().strip() or None,
            "interested_products": self.products_input.text().strip() or None,
            "max_meetings": self.max_meetings_input.value(),
            "max_minutes": self.max_minutes_input.value(),
        }
        try:
            if self.selected_buyer_id:
                self.api.update_buyer(self.selected_buyer_id, payload)
            else:
                self.api.create_buyer(payload)
        except ApiError as e:
            QMessageBox.critical(self, "Kaydedilemedi", str(e))
            return

        self.clear_form()
        self.refresh()

    def delete_buyer(self, buyer_id):
        if QMessageBox.question(self, "Onay", "Bu buyer silinsin mi?") != QMessageBox.Yes:
            return
        try:
            self.api.delete_buyer(buyer_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
        self.refresh()
