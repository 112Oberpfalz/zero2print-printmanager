from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
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


def generate_print_job_pdf(job, base_url: str) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    job_number = f"DJ-{job.id:04d}"
    pdf_path = PDF_DIR / f"{job_number}.pdf"

    job_url = f"{base_url}/jobs/{job.id}"
    qr_path = create_qr_code(job_url, f"{job_number}.png")

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    margin_x = 18 * mm
    y = height - 20 * mm

    # Header
    c.setFillColor(colors.HexColor("#111827"))
    c.rect(0, height - 35 * mm, width, 35 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin_x, height - 20 * mm, "ZERO2PRINT DRUCKJOB")

    c.setFont("Helvetica", 11)
    c.drawString(margin_x, height - 28 * mm, "Werkstattzettel fuer 3D-Druckauftrag")

    # Job number box
    c.setFillColor(colors.HexColor("#2563EB"))
    c.roundRect(width - 65 * mm, height - 29 * mm, 45 * mm, 13 * mm, 4 * mm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width - 42.5 * mm, height - 24.5 * mm, job_number)

    # Main content
    y = height - 52 * mm

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, y, "Auftragsdaten")
    y -= 10 * mm

    rows = [
        ("Job-Nr.", job_number),
        ("Kunde", job.project.customer.name),
        ("Projekt", job.project.name),
        ("Dateiname", get_job_file_name(job)),
        ("Status", job.status or "-"),
    ]

    y = draw_table(c, margin_x, y, rows, width)

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(margin_x, y, "Druckdaten")
    y -= 10 * mm

    rows = [
        ("Drucker", job.printer_name or "-"),
        ("Material", job.material or "-"),
        ("Farbe", job.color or "-"),
        ("Geplante Druckzeit", job.planned_print_time or "-"),
        ("Filament", f"{job.planned_weight_grams} g" if job.planned_weight_grams else "-"),
    ]

    y = draw_table(c, margin_x, y, rows, width)

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(margin_x, y, "Checkliste")
    y -= 8 * mm

    checklist_rows = [
        ("Datei geprueft", checklist_value(job.checklist, "file_checked")),
        ("Slicer geprueft", checklist_value(job.checklist, "slicer_checked")),
        ("Material vorbereitet", checklist_value(job.checklist, "material_ready")),
        ("Druckbett gereinigt", checklist_value(job.checklist, "bed_cleaned")),
        ("Erste Schicht kontrolliert", checklist_value(job.checklist, "first_layer_checked")),
        ("Druck fertig geprueft", checklist_value(job.checklist, "print_finished_checked")),
        ("Nacharbeit erledigt", checklist_value(job.checklist, "post_processing_done")),
        ("Verpackt", checklist_value(job.checklist, "packed")),
    ]

    y = draw_checklist(c, margin_x, y, checklist_rows)

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(margin_x, y, "Notizen")
    y -= 8 * mm

    notes = job.notes or "Keine Notizen vorhanden."
    y = draw_multiline_text(c, margin_x, y, notes, max_width=115 * mm)

    # QR box
    qr_box_x = width - 70 * mm
    qr_box_y = 42 * mm

    c.setStrokeColor(colors.HexColor("#E5E7EB"))
    c.setFillColor(colors.white)
    c.roundRect(qr_box_x, qr_box_y, 50 * mm, 62 * mm, 4 * mm, fill=1, stroke=1)

    c.drawImage(str(qr_path), qr_box_x + 7 * mm, qr_box_y + 20 * mm, 36 * mm, 36 * mm)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(qr_box_x + 25 * mm, qr_box_y + 14 * mm, "QR-Code scannen")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6B7280"))
    c.drawCentredString(qr_box_x + 25 * mm, qr_box_y + 9 * mm, "Druckjob im System oeffnen")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6B7280"))
    c.drawString(margin_x, 15 * mm, f"Lokaler Link: {job_url}")

    c.save()

    return pdf_path


def draw_table(c, x, y, rows, page_width):
    label_width = 45 * mm
    value_width = page_width - x * 2 - label_width
    row_height = 9 * mm

    for label, value in rows:
        c.setFillColor(colors.HexColor("#F9FAFB"))
        c.rect(x, y - row_height + 2 * mm, label_width, row_height, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.rect(x + label_width, y - row_height + 2 * mm, value_width, row_height, fill=1, stroke=0)

        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.rect(x, y - row_height + 2 * mm, label_width + value_width, row_height, fill=0, stroke=1)

        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 4 * mm, y - 4.5 * mm, str(label))

        c.setFillColor(colors.HexColor("#111827"))
        c.setFont("Helvetica", 10)
        c.drawString(x + label_width + 4 * mm, y - 4.5 * mm, str(value))

        y -= row_height

    return y


def draw_checklist(c, x, y, rows):
    col_width = 78 * mm
    row_height = 7 * mm

    for index, (label, checked) in enumerate(rows):
        col = index % 2
        row = index // 2

        item_x = x + (col * col_width)
        item_y = y - (row * row_height)

        box_size = 4 * mm

        c.setStrokeColor(colors.HexColor("#111827"))
        c.setFillColor(colors.white)
        c.rect(item_x, item_y - box_size + 1 * mm, box_size, box_size, fill=0, stroke=1)

        if checked:
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(item_x + 0.7 * mm, item_y - 2.4 * mm, "X")

        c.setFillColor(colors.HexColor("#111827"))
        c.setFont("Helvetica", 9)
        c.drawString(item_x + 6 * mm, item_y - 2.2 * mm, label)

    used_rows = (len(rows) + 1) // 2
    return y - (used_rows * row_height)


def draw_multiline_text(c, x, y, text, max_width):
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#111827"))

    words = str(text).split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()

        if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line)
            y -= 6 * mm
            line = word

    if line:
        c.drawString(x, y, line)
        y -= 6 * mm

    return y