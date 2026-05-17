from datetime import datetime, date

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
import app.models

from app.models import Customer, Project, PrintJob, TimeEntry
from app.routes import customers, projects, print_jobs, time_entries, files, backup, today, planner
from app.template_helpers import status_class

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zero2Print PrintManager")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class

app.include_router(customers.router)
app.include_router(projects.router)
app.include_router(print_jobs.router)
app.include_router(time_entries.router)
app.include_router(files.router)
app.include_router(backup.router)
app.include_router(today.router)
app.include_router(planner.router)

@app.get("/")
def home():
    return RedirectResponse(url="/today", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    customers_count = db.query(Customer).count()
    projects_count = db.query(Project).count()

    open_projects_count = (
        db.query(Project)
        .filter(Project.status.notin_(["Fertig", "Archiviert"]))
        .count()
    )

    active_jobs_count = (
        db.query(PrintJob)
        .filter(PrintJob.status.in_(["Bereit zum Druck", "Druck läuft", "Nacharbeit"]))
        .count()
    )

    finished_jobs_count = (
        db.query(PrintJob)
        .filter(PrintJob.status.in_(["Druck fertig", "Erledigt"]))
        .count()
    )

    active_timers_count = (
        db.query(TimeEntry)
        .filter(TimeEntry.start_time.isnot(None))
        .filter(TimeEntry.end_time.is_(None))
        .count()
    )

    today_date = date.today()

    all_time_entries = db.query(TimeEntry).all()
    today_minutes = 0
    total_minutes = 0

    for entry in all_time_entries:
        if entry.duration_minutes:
            total_minutes += entry.duration_minutes

            if entry.created_at and entry.created_at.date() == today_date:
                today_minutes += entry.duration_minutes

    latest_projects = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .limit(5)
        .all()
    )

    latest_jobs = (
        db.query(PrintJob)
        .order_by(PrintJob.created_at.desc())
        .limit(5)
        .all()
    )

    active_timers = (
        db.query(TimeEntry)
        .filter(TimeEntry.start_time.isnot(None))
        .filter(TimeEntry.end_time.is_(None))
        .order_by(TimeEntry.start_time.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Dashboard",
            "customers_count": customers_count,
            "projects_count": projects_count,
            "open_projects_count": open_projects_count,
            "active_jobs_count": active_jobs_count,
            "finished_jobs_count": finished_jobs_count,
            "active_timers_count": active_timers_count,
            "today_minutes": today_minutes,
            "total_minutes": total_minutes,
            "latest_projects": latest_projects,
            "latest_jobs": latest_jobs,
            "active_timers": active_timers,
            "now": datetime.now(),
        }
    )