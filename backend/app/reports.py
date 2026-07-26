"""Excel ve PDF rapor üretimi."""
import os
import tempfile
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

REPORT_DIR = os.path.join(tempfile.gettempdir(), "foodist_crm_reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def _new_excel_path(name: str) -> str:
    return os.path.join(REPORT_DIR, f"{name}.xlsx")


def _new_pdf_path(name: str) -> str:
    return os.path.join(REPORT_DIR, f"{name}.pdf")


def export_rows_to_excel(rows: list[dict], headers: list[str], header_labels: list[str], filename: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.append(header_labels)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 45)
    path = _new_excel_path(filename)
    wb.save(path)
    return path


def export_rows_to_pdf(title: str, rows: list[list], header_labels: list[str], filename: str) -> str:
    path = _new_pdf_path(filename)
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Heading2"]), Spacer(1, 12)]

    data = [header_labels] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2A24")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F3EA")]),
    ]))
    elements.append(table)
    doc.build(elements)
    return path
