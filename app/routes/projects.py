from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Project, Customer
from app.template_helpers import status_class, format_file_size

router = APIRouter(prefix="/projects", tags=["projects"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class
templates.env.globals["format_file_size"] = format_file_size


PROJECT_STATUSES = [
    "Anfrage",
    "Datei prüfen",
    "Bereit zum Druck",
    "Druck läuft",
    "Nacharbeit",
    "Fertig",
    "Archiviert",
]


@router.get("")
def projects_index(
    request: Request,
    q: str = Query(default=""),
    status: str = Query(default=""),
    db: Session = Depends(get_db)
):
    query = db.query(Project).join(Customer)

    search = q.strip()
    selected_status = status.strip()

    if search:
        query = query.filter(
            or_(
                Project.name.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%"),
                Project.note.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%"),
            )
        )

    if selected_status:
        query = query.filter(Project.status == selected_status)

    projects = query.order_by(Project.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "title": "Projekte",
            "projects": projects,
            "q": search,
            "selected_status": selected_status,
            "statuses": PROJECT_STATUSES
        }
    )


@router.get("/new")
def project_new(
    request: Request,
    customer_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    customers = db.query(Customer).order_by(Customer.name.asc()).all()

    selected_customer = None
    if customer_id:
        selected_customer = db.query(Customer).filter(Customer.id == customer_id).first()

    return templates.TemplateResponse(
        request=request,
        name="project_new.html",
        context={
            "title": "Projekt anlegen",
            "customers": customers,
            "selected_customer": selected_customer
        }
    )


@router.post("/new")
def project_create(
    customer_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("Anfrage"),
    deadline: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project = Project(
        customer_id=customer_id,
        name=name.strip(),
        description=description.strip(),
        status=status.strip(),
        deadline=deadline.strip(),
        note=note.strip()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return RedirectResponse(
        url=f"/projects/{project.id}",
        status_code=303
    )


@router.get("/{project_id}/edit")
def project_edit(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    customers = db.query(Customer).order_by(Customer.name.asc()).all()

    if not project:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Projekt wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="project_edit.html",
        context={
            "title": "Projekt bearbeiten",
            "project": project,
            "customers": customers,
            "statuses": PROJECT_STATUSES
        }
    )


@router.post("/{project_id}/edit")
def project_update(
    project_id: int,
    customer_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("Anfrage"),
    deadline: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    project.customer_id = customer_id
    project.name = name.strip()
    project.description = description.strip()
    project.status = status.strip()
    project.deadline = deadline.strip()
    project.note = note.strip()

    db.commit()

    return RedirectResponse(
        url=f"/projects/{project.id}",
        status_code=303
    )


@router.post("/{project_id}/archive")
def project_archive(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if project:
        project.status = "Archiviert"
        db.commit()

    return RedirectResponse(
        url=f"/projects/{project_id}",
        status_code=303
    )


@router.get("/{project_id}")
def project_detail(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Projekt wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="project_detail.html",
        context={
            "title": project.name,
            "project": project
        }
    )