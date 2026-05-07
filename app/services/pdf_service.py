import os
from datetime import datetime

import qrcode
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from app.config import get_public_base_url


PDF_DIR = "data/pdf"
QR_DIR = "data/qr"


CHECKLIST_ITEMS = [
    ("file_checked", "Datei geprüft"),
    ("slicer_checked", "Slicer geprüft"),
    ("material_ready", "Material bereit"),
    ("bed_cleaned", "Druckbett sauber"),
    ("first_layer_checked", "First Layer geprüft"),
    ("print_finished_checked", "Druck fertig"),
    ("post_processing_done", "Nacharbeit erledigt"),
    ("packed", "Verpackt"),
]


def ensure_dirs():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(QR_DIR, exist_ok=True)


def safe_text(value, fallback="-"):
    if value is None:
        return fallback

    value = str(value).strip()

    if value == "":
        return fallback

    return value


def checkbox_mark(value: bool) -> str:
    return "X" if value else " "


def make_qr_code(job, base_url: str) -> str:
    ensure_dirs()

    job_url = f"{base_url}/jobs/{job.id}"

    qr_path = os.path.join(QR_DIR, f"job_{job.id:04d}.png")

    img = qrcode.make(job_url)
    img.save(qr_path)

    return qr_path


def draw_wrapped_text(pdf, text, x, y, max_width, line_height=4.2 * mm, font_name="Helvetica", font_size=8):
    pdf.setFont(font_name, font_size)

    if not text:
        return y

    words = str(text).split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        width = pdf.stringWidth(test_line, font_name, font_size)

        if width <= max_width:
            line = test_line
        else:
            pdf.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        pdf.drawString(x, y, line)
        y -= line_height

    return y


def draw_label_value(pdf, label, value, x, y, label_width=35 * mm):
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x, y, label)

    pdf.setFont("Helvetica", 8)
    pdf.drawString(x + label_width, y, safe_text(value))

    return y - 5 * mm


def generate_print_job_pdf(job, fallback_base_url: str | None = None) -> str:
    ensure_dirs()

    base_url = get_public_base_url(fallback_base_url)
    qr_path = make_qr_code(job, base_url)

    pdf_path = os.path.join(PDF_DIR, f"DJ-{job.id:04d}.pdf")

    width, height = A5
    pdf = canvas.Canvas(pdf_path, pagesize=A5)

    margin_x = 12 * mm
    y = height - 12 * mm

    # Header
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.rect(0, height - 24 * mm, width, 24 * mm, fill=True, stroke=False)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(margin_x, height - 13 * mm, "Zero2Print Werkstattzettel")

    pdf.setFont("Helvetica", 8)
    pdf.drawString(margin_x, height - 19 * mm, datetime.now().strftime("%d.%m.%Y %H:%M"))

    pdf.setFillColor(colors.HexColor("#2563eb"))
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawRightString(width - margin_x, height - 14 * mm, f"DJ-{job.id:04d}")

    y = height - 34 * mm

    # Auftrag
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin_x, y, "Auftrag")
    y -= 7 * mm

    project = getattr(job, "project", None)
    customer = getattr(project, "customer", None) if project else None

    y = draw_label_value(pdf, "Projekt:", getattr(project, "name", "-"), margin_x, y)
    y = draw_label_value(pdf, "Kunde:", getattr(customer, "name", "-"), margin_x, y)
    y = draw_label_value(pdf, "Status:", getattr(job, "status", "-"), margin_x, y)

    file_obj = getattr(job, "file", None)
    filename = getattr(file_obj, "original_filename", "-") if file_obj else "-"

    y -= 2 * mm

    # Druckdaten
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin_x, y, "Druckdaten")
    y -= 7 * mm

    y = draw_label_value(pdf, "Datei:", filename, margin_x, y)
    y = draw_label_value(pdf, "Drucker:", getattr(job, "printer_name", "-"), margin_x, y)
    y = draw_label_value(pdf, "Material:", getattr(job, "material", "-"), margin_x, y)
    y = draw_label_value(pdf, "Farbe:", getattr(job, "color", "-"), margin_x, y)
    y = draw_label_value(pdf, "Druckzeit:", getattr(job, "planned_print_time", "-"), margin_x, y)

    weight = getattr(job, "planned_weight_grams", None)
    if weight:
        weight_text = f"{weight} g"
    else:
        weight_text = "-"

    y = draw_label_value(pdf, "Gewicht:", weight_text, margin_x, y)

    y -= 2 * mm

    # Checkliste
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin_x, y, "Checkliste")
    y -= 7 * mm

    checklist = getattr(job, "checklist", None)

    left_x = margin_x
    right_x = margin_x + 58 * mm

    for index, (field, label) in enumerate(CHECKLIST_ITEMS):
        current_x = left_x if index % 2 == 0 else right_x

        if index % 2 == 0 and index != 0:
            y -= 6 * mm

        value = False

        if checklist:
            value = bool(getattr(checklist, field, False))

        pdf.setFont("Helvetica", 8)
        pdf.rect(current_x, y - 2 * mm, 3.5 * mm, 3.5 * mm, stroke=True, fill=False)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(current_x + 1.75 * mm, y - 1.3 * mm, checkbox_mark(value))
        pdf.setFont("Helvetica", 8)
        pdf.drawString(current_x + 5 * mm, y - 1 * mm, label)

    y -= 11 * mm

    # Notizen
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin_x, y, "Notizen")
    y -= 6 * mm

    notes = safe_text(getattr(job, "notes", ""), "")

    if notes:
        y = draw_wrapped_text(
            pdf,
            notes,
            margin_x,
            y,
            max_width=width - margin_x * 2 - 35 * mm,
            line_height=4.2 * mm,
            font_size=8
        )
    else:
        pdf.setFont("Helvetica", 8)
        pdf.drawString(margin_x, y, "-")
        y -= 5 * mm

    # QR-Code
    qr_size = 28 * mm
    qr_x = width - margin_x - qr_size
    qr_y = 16 * mm

    pdf.drawImage(qr_path, qr_x, qr_y, qr_size, qr_size)

    pdf.setFont("Helvetica", 6.5)
    pdf.setFillColor(colors.HexColor("#6b7280"))
    pdf.drawCentredString(qr_x + qr_size / 2, qr_y - 3 * mm, "Job öffnen")

    # Footer
    pdf.setFont("Helvetica", 6.5)
    pdf.setFillColor(colors.HexColor("#6b7280"))

    if base_url:
        footer_text = base_url
    else:
        footer_text = "Zero2Print PrintManager"

    pdf.drawString(margin_x, 9 * mm, footer_text)

    pdf.save()

    return pdf_path