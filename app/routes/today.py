from datetime import date, datetime

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, PrintJob, TimeEntry
from app.template_helpers import (
    status_class,
    checklist_done_count,
    checklist_total_count,
    checklist_progress,
    checklist_progress_class,
)

router = APIRouter(prefix="/today", tags=["today"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class
templates.env.globals["checklist_done_count"] = checklist_done_count
templates.env.globals["checklist_total_count"] = checklist_total_count
templates.env.globals["checklist_progress"] = checklist_progress
templates.env.globals["checklist_progress_class"] = checklist_progress_class


@router.get("")
def today_index(request: Request, db: Session = Depends(get_db)):
    today = date.today()

    active_timers = (
        db.query(TimeEntry)
        .filter(TimeEntry.start_time.isnot(None))
        .filter(TimeEntry.end_time.is_(None))
        .order_by(TimeEntry.start_time.desc())
        .all()
    )

    ready_jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status == "Bereit zum Druck")
        .order_by(PrintJob.created_at.desc())
        .all()
    )

    running_jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status == "Druck läuft")
        .order_by(PrintJob.created_at.desc())
        .all()
    )

    post_jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status == "Nacharbeit")
        .order_by(PrintJob.created_at.desc())
        .all()
    )

    error_jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status == "Fehler")
        .order_by(PrintJob.created_at.desc())
        .all()
    )

    open_projects = (
        db.query(Project)
        .filter(Project.status.notin_(["Fertig", "Archiviert"]))
        .order_by(Project.created_at.desc())
        .limit(10)
        .all()
    )

    all_time_entries = db.query(TimeEntry).all()

    today_minutes = 0

    for entry in all_time_entries:
        if entry.duration_minutes and entry.created_at and entry.created_at.date() == today:
            today_minutes += entry.duration_minutes

    return templates.TemplateResponse(
        request=request,
        name="today.html",
        context={
            "title": "Heute zu tun",
            "today": today,
            "now": datetime.now(),
            "active_timers": active_timers,
            "ready_jobs": ready_jobs,
            "running_jobs": running_jobs,
            "post_jobs": post_jobs,
            "error_jobs": error_jobs,
            "open_projects": open_projects,
            "today_minutes": today_minutes,
        }
    )