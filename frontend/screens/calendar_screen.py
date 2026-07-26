from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QFormLayout, QHeaderView, QAbstractItemView, QFileDialog, QLineEdit
)
from PySide6.QtCore import QDate
from api_client import ApiClient, ApiError


class CalendarScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state
        self.eligible_matches = []
        self.meetings_cache = []

        layout = QVBoxLayout(self)
        title = QLabel("Takvim / Toplantı Planlama")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "Karşılıklı onaylanan eşleşmeleri seçip tarih/saat vererek 15 dakikalık toplantı planlayın.",
            objectName="hint"))

        form_box = QGroupBox("Toplantı Planla")
        form_layout = QFormLayout(form_box)

        self.eligible_combo = QComboBox()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("ör. 10:00")
        self.stand_input = QLineEdit()
        self.stand_input.setPlaceholderText("boş bırakılırsa katılımcının kayıtlı stand no'su kullanılır")

        form_layout.addRow("Karşılıklı Onaylanan Eşleşme", self.eligible_combo)
        form_layout.addRow("Tarih", self.date_input)
        form_layout.addRow("Başlangıç Saati (15 dk'lık slot)", self.time_input)
        form_layout.addRow("Stand No (opsiyonel override)", self.stand_input)

        schedule_btn = QPushButton("Toplantıyı Planla ve Mail Gönder")
        schedule_btn.setObjectName("primary")
        schedule_btn.clicked.connect(self.schedule_meeting)
        form_layout.addRow(schedule_btn)

        layout.addWidget(form_box)

        list_row = QHBoxLayout()
        list_row.addWidget(QLabel("Görüntülenen Gün:"))
        self.view_date_input = QDateEdit()
        self.view_date_input.setCalendarPopup(True)
        self.view_date_input.setDate(QDate.currentDate())
        self.view_date_input.dateChanged.connect(self.refresh_meetings)
        list_row.addWidget(self.view_date_input)
        list_row.addStretch()
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_all)
        list_row.addWidget(refresh_btn)
        layout.addLayout(list_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Saat", "Buyer", "Katılımcı", "Stand No", "Durum", "Katıldı/Katılmadı", "ICS"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        self.refresh_all()

    def refresh_all(self):
        self.refresh_eligible_matches()
        self.refresh_meetings()

    def refresh_eligible_matches(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        try:
            all_matches = self.api.list_matches(event_id, "Karşılıklı Onaylandı")
            scheduled_too = self.api.list_matches(event_id, "Toplantı Planlandı")
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        self.eligible_matches = all_matches + scheduled_too
        self.eligible_combo.clear()
        for m in self.eligible_matches:
            label = f"{m['buyer_name']}  ↔  {m['participant_name']}  (skor {m['total_score']}, {m['status']})"
            self.eligible_combo.addItem(label, m["id"])

    def refresh_meetings(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            return
        meeting_date = self.view_date_input.date().toString("yyyy-MM-dd")
        try:
            self.meetings_cache = self.api.list_meetings(event_id, meeting_date)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        self.table.setRowCount(len(self.meetings_cache))
        for row, meeting in enumerate(self.meetings_cache):
            self.table.setItem(row, 0, QTableWidgetItem(f"{meeting['start_time']}-{meeting['end_time']}"))
            self.table.setItem(row, 1, QTableWidgetItem(meeting.get("buyer_name") or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(meeting.get("participant_name") or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(meeting.get("stand_no") or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(meeting["status"]))

            attend_combo = QComboBox()
            attend_combo.addItems(["Planlandı", "Tamamlandı", "Katılmadı"])
            attend_combo.setCurrentText(meeting["status"])
            attend_combo.currentTextChanged.connect(
                lambda text, mid=meeting["id"]: self.update_attendance(mid, text))
            self.table.setCellWidget(row, 5, attend_combo)

            ics_btn = QPushButton("İndir (.ics)")
            ics_btn.clicked.connect(lambda _, mid=meeting["id"]: self.download_ics(mid))
            self.table.setCellWidget(row, 6, ics_btn)

    def schedule_meeting(self):
        if self.eligible_combo.count() == 0:
            QMessageBox.warning(self, "Uygun Eşleşme Yok",
                                 "Önce 'Eşleştirme' ekranından eşleşmeleri karşılıklı onaylatmanız gerekir.")
            return
        match_id = self.eligible_combo.currentData()
        meeting_date = self.date_input.date().toString("yyyy-MM-dd")
        start_time = self.time_input.text().strip()

        if not start_time or ":" not in start_time:
            QMessageBox.warning(self, "Eksik Bilgi", "Saat alanını 'SS:DD' formatında girin (ör. 10:00).")
            return

        try:
            self.api.schedule_meeting(match_id, meeting_date, start_time, self.stand_input.text().strip() or None)
        except ApiError as e:
            QMessageBox.critical(self, "Planlanamadı", str(e))
            return

        QMessageBox.information(self, "Planlandı", "Toplantı planlandı ve taraflara bilgilendirme e-postası gönderildi.")
        self.view_date_input.setDate(self.date_input.date())
        self.refresh_all()

    def update_attendance(self, meeting_id, status):
        try:
            self.api.update_attendance(meeting_id, status)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))

    def download_ics(self, meeting_id):
        path, _ = QFileDialog.getSaveFileName(self, "ICS Dosyasını Kaydet", f"toplanti-{meeting_id}.ics", "ICS (*.ics)")
        if not path:
            return
        try:
            self.api.download_ics(meeting_id, path)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "İndirildi", f"ICS dosyası kaydedildi:\n{path}\n\nBu dosyayı Outlook/Google Calendar'a çift tıklayarak içe aktarabilirsiniz.")
