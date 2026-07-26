from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox, QDateEdit
)
from PySide6.QtCore import QDate
from api_client import ApiClient, ApiError


class ReportsScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state

        layout = QVBoxLayout(self)
        title = QLabel("Raporlar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Excel/PDF çıktılarını indirin.", objectName="hint"))

        simple_reports = [
            ("Buyer Takvimi (Excel)", "/reports/buyer-calendar", "buyer_takvimi.xlsx"),
            ("Firma Takvimi (Excel)", "/reports/participant-calendar", "firma_takvimi.xlsx"),
            ("No Show Raporu (Excel)", "/reports/no-show", "no_show_raporu.xlsx"),
            ("En Çok Görüşme Alan Firmalar (Excel)", "/reports/top-companies", "en_cok_gorusme.xlsx"),
            ("Ülke Bazlı Analiz (Excel)", "/reports/country-analysis", "ulke_analiz.xlsx"),
            ("Sektör Bazlı Analiz (Excel)", "/reports/sector-analysis", "sektor_analiz.xlsx"),
        ]
        for label, endpoint, filename in simple_reports:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, e=endpoint, f=filename: self.download(e, {}, f))
            layout.addWidget(btn)

        daily_row = QHBoxLayout()
        self.daily_date = QDateEdit()
        self.daily_date.setCalendarPopup(True)
        self.daily_date.setDate(QDate.currentDate())
        daily_btn = QPushButton("Günlük Toplantı Programı (PDF)")
        daily_btn.clicked.connect(self.download_daily)
        daily_row.addWidget(QLabel("Tarih:"))
        daily_row.addWidget(self.daily_date)
        daily_row.addWidget(daily_btn)
        layout.addLayout(daily_row)

        layout.addStretch()

    def download(self, endpoint, extra_params, default_filename):
        event_id = self.app_state.get("event_id")
        if not event_id:
            QMessageBox.warning(self, "Etkinlik Seçilmedi", "Önce üstten bir etkinlik seçin.")
            return
        params = {"event_id": event_id, **extra_params}
        path, _ = QFileDialog.getSaveFileName(self, "Raporu Kaydet", default_filename)
        if not path:
            return
        try:
            self.api.download_report(endpoint, params, path)
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        QMessageBox.information(self, "İndirildi", f"Rapor kaydedildi:\n{path}")

    def download_daily(self):
        meeting_date = self.daily_date.date().toString("yyyy-MM-dd")
        self.download("/reports/daily-schedule-pdf", {"meeting_date": meeting_date},
                       f"gunluk_program_{meeting_date}.pdf")

    def refresh(self):
        pass
