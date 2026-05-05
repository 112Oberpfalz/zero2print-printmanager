from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import PrintJob, Project, ProjectFile, Customer
from app.services.pdf_service import generate_print_job_pdf
from app.template_helpers import status_class

router = APIRouter(prefix="/jobs", tags=["print_jobs"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class


JOB_STATUSES = [
    "Bereit zum Druck",
    "Druck läuft",
    "Druck fertig",
    "Fehler",
    "Nacharbeit",
    "Erledigt",
]


PRINTER_PRESETS = [
    "Anycubic Kobra S1",
    "Anderer Drucker",
]


MATERIAL_PRESETS = [
    "PLA+",
]


def parse_optional_int(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def update_project_status_from_job(project: Project, job_status: str):
    """
    Aktualisiert den Projektstatus automatisch anhand des Druckjob-Status.
    Bewusst simpel gehalten, damit der Workflow im Alltag nicht nervt.
    """
    if not project or not job_status:
        return

    status = job_status.strip()

    mapping = {
        "Bereit zum Druck": "Bereit zum Druck",
        "Druck läuft": "Druck läuft",
        "Nacharbeit": "Nacharbeit",
        "Erledigt": "Fertig",
    }

    new_project_status = mapping.get(status)

    if new_project_status:
        project.status = new_project_status


@router.get("")
def print_jobs_index(
    request: Request,
    q: str = Query(default=""),
    status: str = Query(default=""),
    db: Session = Depends(get_db)
):
    query = (
        db.query(PrintJob)
        .join(Project)
        .join(Customer)
    )

    search = q.strip()
    selected_status = status.strip()

    if search:
        query = query.outerjoin(ProjectFile, PrintJob.file_id == ProjectFile.id)
        query = query.filter(
            or_(
                Project.name.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%"),
                PrintJob.printer_name.ilike(f"%{search}%"),
                PrintJob.material.ilike(f"%{search}%"),
                PrintJob.color.ilike(f"%{search}%"),
                PrintJob.notes.ilike(f"%{search}%"),
                ProjectFile.original_filename.ilike(f"%{search}%"),
            )
        )

    if selected_status:
        query = query.filter(PrintJob.status == selected_status)

    jobs = query.order_by(PrintJob.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="print_jobs.html",
        context={
            "title": "Druckjobs",
            "jobs": jobs,
            "q": search,
            "selected_status": selected_status,
            "statuses": JOB_STATUSES
        }
    )


@router.get("/new")
def print_job_new(
    request: Request,
    project_id: int | None = Query(default=None),
    file_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    selected_project = None
    selected_file = None
    project_files = []

    if project_id:
        selected_project = db.query(Project).filter(Project.id == project_id).first()

        if selected_project:
            project_files = selected_project.files

    if file_id:
        selected_file = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()

        if selected_file:
            selected_project = selected_file.project
            project_files = selected_project.files

    return templates.TemplateResponse(
        request=request,
        name="print_job_new.html",
        context={
            "title": "Druckjob anlegen",
            "projects": projects,
            "selected_project": selected_project,
            "selected_file": selected_file,
            "project_files": project_files,
            "printer_presets": PRINTER_PRESETS,
            "material_presets": MATERIAL_PRESETS,
            "statuses": JOB_STATUSES,
        }
    )


@router.post("/new")
def print_job_create(
    project_id: int = Form(...),
    file_id: str = Form("0"),
    printer_name: str = Form(""),
    material: str = Form("PLA+"),
    color: str = Form(""),
    planned_print_time: str = Form(""),
    planned_weight_grams: str = Form(""),
    status: str = Form("Bereit zum Druck"),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    parsed_file_id = parse_optional_int(file_id)
    if parsed_file_id == 0:
        parsed_file_id = None

    parsed_weight = parse_optional_int(planned_weight_grams)
    clean_status = status.strip()

    job = PrintJob(
        project_id=project.id,
        file_id=parsed_file_id,
        printer_name=printer_name.strip(),
        material=material.strip() or "PLA+",
        color=color.strip(),
        planned_print_time=planned_print_time.strip(),
        planned_weight_grams=parsed_weight,
        status=clean_status,
        notes=notes.strip()
    )

    db.add(job)

    update_project_status_from_job(project, clean_status)

    db.commit()
    db.refresh(job)

    return RedirectResponse(
        url=f"/jobs/{job.id}",
        status_code=303
    )


@router.get("/{job_id}/edit")
def print_job_edit(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    if not job:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Druckjob wurde nicht gefunden."
            },
            status_code=404
        )

    project_files = job.project.files

    return templates.TemplateResponse(
        request=request,
        name="print_job_edit.html",
        context={
            "title": "Druckjob bearbeiten",
            "job": job,
            "projects": projects,
            "project_files": project_files,
            "statuses": JOB_STATUSES,
            "printer_presets": PRINTER_PRESETS,
            "material_presets": MATERIAL_PRESETS,
        }
    )


@router.post("/{job_id}/edit")
def print_job_update(
    job_id: int,
    project_id: int = Form(...),
    file_id: str = Form("0"),
    printer_name: str = Form(""),
    material: str = Form("PLA+"),
    color: str = Form(""),
    planned_print_time: str = Form(""),
    planned_weight_grams: str = Form(""),
    status: str = Form("Bereit zum Druck"),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    parsed_file_id = parse_optional_int(file_id)
    if parsed_file_id == 0:
        parsed_file_id = None

    parsed_weight = parse_optional_int(planned_weight_grams)
    clean_status = status.strip()

    job.project_id = project_id
    job.file_id = parsed_file_id
    job.printer_name = printer_name.strip()
    job.material = material.strip() or "PLA+"
    job.color = color.strip()
    job.planned_print_time = planned_print_time.strip()
    job.planned_weight_grams = parsed_weight
    job.status = clean_status
    job.notes = notes.strip()

    update_project_status_from_job(project, clean_status)

    db.commit()

    return RedirectResponse(
        url=f"/jobs/{job.id}",
        status_code=303
    )


@router.post("/{job_id}/status")
def print_job_update_status(
    job_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    clean_status = status.strip()
    job.status = clean_status

    update_project_status_from_job(job.project, clean_status)

    db.commit()

    return RedirectResponse(
        url=f"/jobs/{job.id}",
        status_code=303
    )


@router.post("/{job_id}/done")
def print_job_mark_done(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

    if job:
        job.status = "Erledigt"
        update_project_status_from_job(job.project, "Erledigt")
        db.commit()

    return RedirectResponse(
        url=f"/jobs/{job_id}",
        status_code=303
    )


@router.get("/{job_id}/pdf")
def print_job_pdf(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    base_url = str(request.base_url).rstrip("/")
    pdf_path = generate_print_job_pdf(job, base_url)

    return FileResponse(
        path=pdf_path,
        filename=f"DJ-{job.id:04d}.pdf",
        media_type="application/pdf"
    )


@router.get("/{job_id}")
def print_job_detail(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()

    if not job:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Druckjob wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="print_job_detail.html",
        context={
            "title": f"DJ-{job.id:04d}",
            "job": job
        }
    )