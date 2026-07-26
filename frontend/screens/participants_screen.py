from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QFormLayout, QGroupBox
)
from api_client import ApiClient, ApiError


class ParticipantsScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state
        self.selected_id = None

        layout = QVBoxLayout(self)
        title = QLabel("Katılımcı Firma Yönetimi")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Fuara katılan firmaları buradan yönetin.", objectName="hint"))

        form_box = QGroupBox("Katılımcı Ekle / Güncelle")
        form_layout = QFormLayout(form_box)
        self.company_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.country_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.sector_input = QLineEdit()
        self.products_input = QLineEdit()
        self.products_input.setPlaceholderText("virgülle ayırın: Süt ürünleri, Peynir")
        self.stand_input = QLineEdit()

        form_layout.addRow("Firma Adı *", self.company_input)
        form_layout.addRow("Yetkili Ad Soyad", self.contact_input)
        form_layout.addRow("Ülke", self.country_input)
        form_layout.addRow("E-posta", self.email_input)
        form_layout.addRow("Telefon", self.phone_input)
        form_layout.addRow("Sektör", self.sector_input)
        form_layout.addRow("Sunulan Ürünler", self.products_input)
        form_layout.addRow("Stand No", self.stand_input)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self.save_participant)
        self.clear_btn = QPushButton("Temizle / Yeni")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.clear_btn)
        form_layout.addRow(btn_row)

        layout.addWidget(form_box)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Firma", "Yetkili", "Ülke", "Sektör", "Stand No", "E-posta", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout.addWidget(self.table)

        self.cache = []
        self.refresh()

    def refresh(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        try:
            self.cache = self.api.list_participants(event_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self.table.setRowCount(len(self.cache))
        for row, p in enumerate(self.cache):
            self.table.setItem(row, 0, QTableWidgetItem(p["company_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("contact_name") or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(p.get("country") or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(p.get("sector") or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(p.get("stand_no") or "-"))
            self.table.setItem(row, 5, QTableWidgetItem(p.get("contact_email") or "-"))
            del_btn = QPushButton("Sil")
            del_btn.clicked.connect(lambda _, pid=p["id"]: self.delete_participant(pid))
            self.table.setCellWidget(row, 6, del_btn)

    def on_row_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        p = self.cache[idx]
        self.selected_id = p["id"]
        self.company_input.setText(p["company_name"])
        self.contact_input.setText(p.get("contact_name") or "")
        self.country_input.setText(p.get("country") or "")
        self.email_input.setText(p.get("contact_email") or "")
        self.phone_input.setText(p.get("contact_phone") or "")
        self.sector_input.setText(p.get("sector") or "")
        self.products_input.setText(p.get("offered_products") or "")
        self.stand_input.setText(p.get("stand_no") or "")

    def clear_form(self):
        self.selected_id = None
        for w in [self.company_input, self.contact_input, self.country_input,
                  self.email_input, self.phone_input, self.sector_input,
                  self.products_input, self.stand_input]:
            w.clear()
        self.table.clearSelection()

    def save_participant(self):
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
            "offered_products": self.products_input.text().strip() or None,
            "stand_no": self.stand_input.text().strip() or None,
        }
        try:
            if self.selected_id:
                self.api.update_participant(self.selected_id, payload)
            else:
                self.api.create_participant(payload)
        except ApiError as e:
            QMessageBox.critical(self, "Kaydedilemedi", str(e))
            return

        self.clear_form()
        self.refresh()

    def delete_participant(self, participant_id):
        if QMessageBox.question(self, "Onay", "Bu katılımcı silinsin mi?") != QMessageBox.Yes:
            return
        try:
            self.api.delete_participant(participant_id)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
        self.refresh()
