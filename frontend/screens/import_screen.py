from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QFormLayout,
    QGroupBox, QRadioButton, QButtonGroup
)
from api_client import ApiClient, ApiError


class ImportScreen(QWidget):
    def __init__(self, api: ApiClient, app_state: dict):
        super().__init__()
        self.api = api
        self.app_state = app_state
        self.file_token = None
        self.excel_columns = []
        self.mapping_combos = {}

        layout = QVBoxLayout(self)
        title = QLabel("Excel İçe Aktarma")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "1) Dosya seçin  →  2) Alan eşleştirmesi yapın  →  3) İçe aktarın. "
            "Desteklenen format: .xlsx", objectName="hint"))

        type_box = QGroupBox("Ne içe aktarılıyor?")
        type_layout = QHBoxLayout(type_box)
        self.radio_buyer = QRadioButton("Hosted Buyer")
        self.radio_participant = QRadioButton("Katılımcı Firma")
        self.radio_buyer.setChecked(True)
        self.entity_group = QButtonGroup(self)
        self.entity_group.addButton(self.radio_buyer)
        self.entity_group.addButton(self.radio_participant)
        self.radio_buyer.toggled.connect(self.on_entity_type_changed)
        self.radio_participant.toggled.connect(self.on_entity_type_changed)
        type_layout.addWidget(self.radio_buyer)
        type_layout.addWidget(self.radio_participant)
        layout.addWidget(type_box)

        file_row = QHBoxLayout()
        self.file_label = QLabel("Dosya seçilmedi.")
        pick_btn = QPushButton("Dosya Seç (.xlsx)")
        pick_btn.clicked.connect(self.pick_file)
        file_row.addWidget(pick_btn)
        file_row.addWidget(self.file_label)
        layout.addLayout(file_row)

        self.mapping_box = QGroupBox("Alan Eşleştirme")
        self.mapping_layout = QFormLayout(self.mapping_box)
        layout.addWidget(self.mapping_box)

        layout.addWidget(QLabel("Önizleme (ilk 5 satır)"))
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        self.import_btn = QPushButton("İçe Aktar")
        self.import_btn.setObjectName("primary")
        self.import_btn.clicked.connect(self.do_import)
        self.import_btn.setEnabled(False)
        layout.addWidget(self.import_btn)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

    def current_entity_type(self):
        return "buyer" if self.radio_buyer.isChecked() else "participant"

    def on_entity_type_changed(self):
        if self.excel_columns:
            self.build_mapping_form()

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx)")
        if not path:
            return
        try:
            result = self.api.upload_file(path)
        except ApiError as e:
            QMessageBox.critical(self, "Yükleme Hatası", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Bağlantı Hatası", str(e))
            return

        self.file_token = result["file_token"]
        self.excel_columns = result["columns"]
        self.file_label.setText(path.split("/")[-1].split("\\")[-1])

        self.preview_table.setColumnCount(len(self.excel_columns))
        self.preview_table.setHorizontalHeaderLabels(self.excel_columns)
        rows = result["preview_rows"]
        self.preview_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.preview_table.setItem(r, c, QTableWidgetItem(str(val)))

        self.build_mapping_form()
        self.import_btn.setEnabled(True)

    def build_mapping_form(self):
        while self.mapping_layout.rowCount():
            self.mapping_layout.removeRow(0)
        self.mapping_combos = {}

        try:
            fields = self.api.import_fields(self.current_entity_type())
        except ApiError as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        for f in fields:
            combo = QComboBox()
            combo.addItem("(Eşleştirme yok)")
            combo.addItems(self.excel_columns)
            for i, col in enumerate(self.excel_columns):
                if f["label"].split()[0].lower() in col.lower() or f["field"] in col.lower().replace(" ", "_"):
                    combo.setCurrentIndex(i + 1)
                    break
            self.mapping_combos[f["field"]] = combo
            self.mapping_layout.addRow(f["label"], combo)

    def do_import(self):
        event_id = self.app_state.get("event_id")
        if not event_id:
            QMessageBox.warning(self, "Etkinlik Seçilmedi", "Önce üstten bir etkinlik seçin.")
            return
        if not self.file_token:
            QMessageBox.warning(self, "Dosya Yok", "Önce bir Excel dosyası seçin.")
            return

        mapping = {}
        for field, combo in self.mapping_combos.items():
            if combo.currentIndex() > 0:
                mapping[field] = combo.currentText()

        try:
            result = self.api.commit_import(event_id, self.current_entity_type(), self.file_token, mapping)
        except ApiError as e:
            QMessageBox.critical(self, "İçe Aktarma Hatası", str(e))
            return

        msg = f"{result['created']} / {result['total_rows']} kayıt içe aktarıldı."
        if result["errors"]:
            msg += "\n\nHatalar:\n" + "\n".join(result["errors"][:10])
        self.result_label.setText(msg)
        QMessageBox.information(self, "İçe Aktarma Tamamlandı", msg)
