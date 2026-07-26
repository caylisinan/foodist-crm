APP_STYLE = """
QWidget { background:#F7F3EA; font-family: Arial; color:#1E1712; font-size:13px; }
QMainWindow { background:#F7F3EA; }
QLabel#pageTitle { font-size:18px; font-weight:bold; color:#1F2A24; }
QLabel#hint { color:#77705F; font-size:12px; }
QPushButton { background:#1F2A24; color:white; padding:8px 16px; border-radius:2px; }
QPushButton:hover { background:#2B3B32; }
QPushButton:disabled { background:#B9B2A2; }
QPushButton#primary { background:#A23B2E; }
QPushButton#primary:hover { background:#8A3226; }
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
    border:1px solid #D8D0BC; padding:6px; border-radius:2px; background:#FFFFFF;
}
QTableWidget {
    background:#FFFFFF; border:1px solid #E3DCC8; gridline-color:#EDE8DA;
}
QHeaderView::section {
    background:#1F2A24; color:white; padding:6px; border:none; font-size:11px;
}
QTabWidget::pane { border:1px solid #E3DCC8; background:#FFFFFF; }
QTabBar::tab { background:#EFE7D6; padding:8px 16px; margin-right:2px; }
QTabBar::tab:selected { background:#1F2A24; color:white; }
QListWidget { background:#FFFFFF; border:1px solid #E3DCC8; }
"""
