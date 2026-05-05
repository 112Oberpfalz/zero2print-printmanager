from datetime import datetime

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TimeEntry, Project, PrintJob
from app.template_helpers import status_class

router = APIRouter(prefix="/time", tags=["time_entries"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class


CATEGORIES = [
    "Kundenkommunikation",
    "CAD / Konstruktion",
    "Dateiprüfung",
    "Slicing",
    "Druckvorbereitung",
    "Nacharbeit",
    "Verpackung",
    "Sonstiges",
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


def calculate_duration_minutes(start_time, end_time):
    if not start_time or not end_time:
        return 1

    seconds = (end_time - start_time).total_seconds()
    minutes = int(seconds // 60)

    if minutes < 1:
        minutes = 1

    return minutes


# ------------------------------------------------------------
# Web-Seiten
# ------------------------------------------------------------

@router.get("")
def time_index(request: Request, db: Session = Depends(get_db)):
    entries = db.query(TimeEntry).order_by(TimeEntry.created_at.desc()).all()

    active_entries = (
        db.query(TimeEntry)
        .filter(TimeEntry.start_time.isnot(None))
        .filter(TimeEntry.end_time.is_(None))
        .order_by(TimeEntry.start_time.desc())
        .all()
    )

    total_minutes = 0

    for entry in entries:
        if entry.duration_minutes:
            total_minutes += entry.duration_minutes

    return templates.TemplateResponse(
        request=request,
        name="time_entries.html",
        context={
            "title": "Zeiten",
            "entries": entries,
            "active_entries": active_entries,
            "total_minutes": total_minutes,
        }
    )


@router.get("/new")
def time_new(
    request: Request,
    project_id: int | None = Query(default=None),
    job_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    jobs = db.query(PrintJob).order_by(PrintJob.created_at.desc()).all()

    selected_project = None
    selected_job = None

    if project_id:
        selected_project = db.query(Project).filter(Project.id == project_id).first()

    if job_id:
        selected_job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if selected_job:
            selected_project = selected_job.project

    return templates.TemplateResponse(
        request=request,
        name="time_entry_new.html",
        context={
            "title": "Zeit eintragen",
            "projects": projects,
            "jobs": jobs,
            "categories": CATEGORIES,
            "selected_project": selected_project,
            "selected_job": selected_job,
        }
    )


@router.post("/new")
def time_create_manual(
    project_id: int = Form(...),
    print_job_id: str = Form(""),
    category: str = Form(...),
    duration_minutes: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return RedirectResponse(url="/time", status_code=303)

    parsed_job_id = parse_optional_int(print_job_id)
    parsed_duration = parse_optional_int(duration_minutes)

    if not parsed_duration:
        parsed_duration = 1

    entry = TimeEntry(
        project_id=project.id,
        print_job_id=parsed_job_id,
        category=category.strip(),
        duration_minutes=parsed_duration,
        note=note.strip(),
        created_at=datetime.utcnow(),
    )

    db.add(entry)
    db.commit()

    return RedirectResponse(url="/time", status_code=303)


@router.post("/start")
def time_start(
    project_id: int = Form(...),
    print_job_id: str = Form(""),
    category: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return RedirectResponse(url="/time", status_code=303)

    parsed_job_id = parse_optional_int(print_job_id)

    entry = TimeEntry(
        project_id=project.id,
        print_job_id=parsed_job_id,
        category=category.strip(),
        start_time=datetime.utcnow(),
        end_time=None,
        duration_minutes=None,
        note=note.strip(),
        created_at=datetime.utcnow(),
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return RedirectResponse(url="/time", status_code=303)


# ------------------------------------------------------------
# Mini-Timer API
# Wichtig:
# Diese Routen müssen VOR /{entry_id}/stop stehen,
# sonst fängt FastAPI "/api/stop" als entry_id="api" ab.
# ------------------------------------------------------------

@router.get("/api/categories")
def api_categories():
    return {
        "success": True,
        "categories": CATEGORIES
    }


@router.get("/api/projects")
def api_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    result = []

    for project in projects:
        result.append(
            {
                "id": project.id,
                "name": project.name,
                "customer": project.customer.name if project.customer else "-",
                "status": project.status or "-",
            }
        )

    return {
        "success": True,
        "projects": result
    }


@router.get("/api/jobs")
def api_jobs(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(PrintJob)

    if project_id:
        query = query.filter(PrintJob.project_id == project_id)

    jobs = query.order_by(PrintJob.created_at.desc()).all()

    result = []

    for job in jobs:
        result.append(
            {
                "id": job.id,
                "job_number": f"DJ-{job.id:04d}",
                "project_id": job.project_id,
                "project": job.project.name if job.project else "-",
                "customer": job.project.customer.name if job.project and job.project.customer else "-",
                "status": job.status or "-",
                "printer_name": job.printer_name or "-",
                "material": job.material or "-",
                "color": job.color or "-",
            }
        )

    return {
        "success": True,
        "jobs": result
    }


@router.get("/api/active")
def api_active_timers(db: Session = Depends(get_db)):
    entries = (
        db.query(TimeEntry)
        .filter(TimeEntry.start_time.isnot(None))
        .filter(TimeEntry.end_time.is_(None))
        .order_by(TimeEntry.start_time.desc())
        .all()
    )

    result = []

    for entry in entries:
        result.append(
            {
                "id": entry.id,
                "project_id": entry.project_id,
                "project": entry.project.name if entry.project else "-",
                "customer": entry.project.customer.name if entry.project and entry.project.customer else "-",
                "print_job_id": entry.print_job_id,
                "job_number": f"DJ-{entry.print_job_id:04d}" if entry.print_job_id else "-",
                "category": entry.category or "-",
                "note": entry.note or "",
                "start_time": entry.start_time.strftime("%d.%m.%Y %H:%M:%S") if entry.start_time else "",
            }
        )

    return {
        "success": True,
        "active_timers": result
    }


@router.post("/api/start")
def api_start_timer(
    project_id: str = Form(...),
    print_job_id: str = Form(""),
    category: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    parsed_project_id = parse_optional_int(project_id)

    if not parsed_project_id:
        return {
            "success": False,
            "message": "Keine gültige Projekt-ID übergeben."
        }

    project = db.query(Project).filter(Project.id == parsed_project_id).first()

    if not project:
        return {
            "success": False,
            "message": "Projekt wurde nicht gefunden."
        }

    parsed_job_id = parse_optional_int(print_job_id)

    entry = TimeEntry(
        project_id=project.id,
        print_job_id=parsed_job_id,
        category=category.strip(),
        start_time=datetime.utcnow(),
        end_time=None,
        duration_minutes=None,
        note=note.strip(),
        created_at=datetime.utcnow(),
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "success": True,
        "message": "Timer gestartet.",
        "entry_id": entry.id
    }


@router.post("/api/stop")
def api_stop_timer(
    entry_id: str = Form(...),
    db: Session = Depends(get_db)
):
    parsed_entry_id = parse_optional_int(entry_id)

    if not parsed_entry_id:
        return {
            "success": False,
            "message": "Keine gültige Timer-ID übergeben."
        }

    entry = db.query(TimeEntry).filter(TimeEntry.id == parsed_entry_id).first()

    if not entry:
        return {
            "success": False,
            "message": f"Timer mit ID {parsed_entry_id} wurde nicht gefunden."
        }

    if entry.end_time:
        return {
            "success": False,
            "message": "Timer wurde bereits gestoppt."
        }

    entry.end_time = datetime.utcnow()
    entry.duration_minutes = calculate_duration_minutes(
        entry.start_time,
        entry.end_time
    )

    db.commit()

    return {
        "success": True,
        "message": "Timer gestoppt.",
        "duration_minutes": entry.duration_minutes
    }


# ------------------------------------------------------------
# Dynamische Web-Routen
# Müssen NACH /api/... stehen.
# ------------------------------------------------------------

@router.post("/{entry_id}/stop")
def time_stop(
    entry_id: int,
    db: Session = Depends(get_db)
):
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

    if not entry:
        return RedirectResponse(url="/time", status_code=303)

    if not entry.end_time:
        entry.end_time = datetime.utcnow()
        entry.duration_minutes = calculate_duration_minutes(
            entry.start_time,
            entry.end_time
        )
        db.commit()

    return RedirectResponse(url="/time", status_code=303)


@router.post("/{entry_id}/delete")
def time_delete(
    entry_id: int,
    db: Session = Depends(get_db)
):
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

    if entry:
        db.delete(entry)
        db.commit()

    return RedirectResponse(url="/time", status_code=303)