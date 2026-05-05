from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.services.qr_service import create_qr_code


PDF_DIR = Path("data/pdf")


def get_job_file_name(job):
    if job.file:
        return job.file.original_filename
    return "-"


def checklist_value(checklist, field_name):
    if not checklist:
        return False

    return bool(getattr(checklist, field_name, False))


def draw_single_line(c, x, y, text, max_width, font_name="Helvetica", font_size=8):
    text = str(text)
    c.setFont(font_name, font_size)

    if c.stringWidth(text, font_name, font_size) <= max_width:
        c.drawString(x, y, text)
        return

    ellipsis = "..."

    while text and c.stringWidth(text + ellipsis, font_name, font_size) > max_width:
        text = text[:-1]

    c.drawString(x, y, text + ellipsis)


def generate_print_job_pdf(job, base_url: str) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    job_number = f"DJ-{job.id:04d}"
    pdf_path = PDF_DIR / f"{job_number}.pdf"

    job_url = f"{base_url}/jobs/{job.id}"
    qr_path = create_qr_code(job_url, f"{job_number}.png")

    c = canvas.Canvas(str(pdf_path), pagesize=A5)
    width, height = A5

    margin_x = 10 * mm
    y = height - 10 * mm

    # Header
    c.setFillColor(colors.HexColor("#111827"))
    c.rect(0, height - 24 * mm, width, 24 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(margin_x, height - 11 * mm, "ZERO2PRINT DRUCKJOB")

    c.setFont("Helvetica", 8)
    c.drawString(margin_x, height - 17 * mm, "Werkstattzettel fuer 3D-Druckauftrag")

    c.setFillColor(colors.HexColor("#2563EB"))
    c.roundRect(width - 47 * mm, height - 18 * mm, 35 * mm, 9 * mm, 3 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width - 29.5 * mm, height - 14.9 * mm, job_number)

    y = height - 32 * mm

    # Auftrag
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y, "Auftrag")
    y -= 6 * mm

    rows = [
        ("Job", job_number),
        ("Kunde", job.project.customer.name),
        ("Projekt", job.project.name),
        ("Datei", get_job_file_name(job)),
        ("Status", job.status or "-"),
    ]

    y = draw_table(c, margin_x, y, rows, width)

    y -= 4 * mm

    # Druckdaten
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y, "Druckdaten")
    y -= 6 * mm

    rows = [
        ("Drucker", job.printer_name or "-"),
        ("Material", job.material or "-"),
        ("Farbe", job.color or "-"),
        ("Zeit", job.planned_print_time or "-"),
        ("Filament", f"{job.planned_weight_grams} g" if job.planned_weight_grams else "-"),
    ]

    y = draw_table(c, margin_x, y, rows, width)

    y -= 4 * mm

    # Checkliste
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y, "Checkliste")
    y -= 5 * mm

    checklist_rows = [
        ("Datei geprueft", checklist_value(job.checklist, "file_checked")),
        ("Slicer geprueft", checklist_value(job.checklist, "slicer_checked")),
        ("Material bereit", checklist_value(job.checklist, "material_ready")),
        ("Bett gereinigt", checklist_value(job.checklist, "bed_cleaned")),
        ("1. Schicht OK", checklist_value(job.checklist, "first_layer_checked")),
        ("Druck geprueft", checklist_value(job.checklist, "print_finished_checked")),
        ("Nacharbeit erledigt", checklist_value(job.checklist, "post_processing_done")),
        ("Verpackt", checklist_value(job.checklist, "packed")),
    ]

    y = draw_checklist(c, margin_x, y, checklist_rows)

    y -= 3 * mm

    # Notizen
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Notizen")
    y -= 5 * mm

    notes = job.notes or "Keine Notizen."
    y = draw_multiline_text(c, margin_x, y, notes, max_width=82 * mm, max_lines=4)

    # QR-Code unten rechts
    qr_size = 26 * mm
    qr_x = width - margin_x - qr_size
    qr_y = 12 * mm

    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setFillColor(colors.white)
    c.roundRect(qr_x - 3 * mm, qr_y - 8 * mm, qr_size + 6 * mm, qr_size + 15 * mm, 3 * mm, fill=1, stroke=1)

    c.drawImage(str(qr_path), qr_x, qr_y, qr_size, qr_size)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 3 * mm, "QR-Code scannen")

    # Footer / Link
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.HexColor("#6B7280"))
    draw_single_line(c, margin_x, 7 * mm, f"Link: {job_url}", max_width=95 * mm, font_size=6)

    c.save()

    return pdf_path


def draw_table(c, x, y, rows, page_width):
    label_width = 25 * mm
    value_width = page_width - x * 2 - label_width
    row_height = 6 * mm

    for label, value in rows:
        c.setFillColor(colors.HexColor("#F9FAFB"))
        c.rect(x, y - row_height + 1 * mm, label_width, row_height, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.rect(x + label_width, y - row_height + 1 * mm, value_width, row_height, fill=1, stroke=0)

        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.rect(x, y - row_height + 1 * mm, label_width + value_width, row_height, fill=0, stroke=1)

        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 2 * mm, y - 3.8 * mm, str(label))

        c.setFillColor(colors.HexColor("#111827"))
        draw_single_line(
            c,
            x + label_width + 2 * mm,
            y - 3.8 * mm,
            value,
            max_width=value_width - 4 * mm,
            font_name="Helvetica",
            font_size=7,
        )

        y -= row_height

    return y


def draw_checklist(c, x, y, rows):
    col_width = 60 * mm
    row_height = 5.5 * mm

    for index, (label, checked) in enumerate(rows):
        col = index % 2
        row = index // 2

        item_x = x + (col * col_width)
        item_y = y - (row * row_height)

        box_size = 3.2 * mm

        c.setStrokeColor(colors.HexColor("#111827"))
        c.setFillColor(colors.white)
        c.rect(item_x, item_y - box_size + 1 * mm, box_size, box_size, fill=0, stroke=1)

        if checked:
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 7)
            c.drawString(item_x + 0.5 * mm, item_y - 1.8 * mm, "X")

        c.setFillColor(colors.HexColor("#111827"))
        c.setFont("Helvetica", 7)
        c.drawString(item_x + 5 * mm, item_y - 1.8 * mm, label)

    used_rows = (len(rows) + 1) // 2
    return y - (used_rows * row_height)


def draw_multiline_text(c, x, y, text, max_width, max_lines=4):
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#111827"))

    words = str(text).split()
    line = ""
    lines_drawn = 0

    for word in words:
        test_line = f"{line} {word}".strip()

        if c.stringWidth(test_line, "Helvetica", 7) <= max_width:
            line = test_line
        else:
            if lines_drawn >= max_lines:
                return y

            c.drawString(x, y, line)
            y -= 4 * mm
            lines_drawn += 1
            line = word

    if line and lines_drawn < max_lines:
        c.drawString(x, y, line)
        y -= 4 * mm

    return y