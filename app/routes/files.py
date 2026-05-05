from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, ProjectFile, PrintJob
from app.template_helpers import status_class, format_file_size

router = APIRouter(prefix="/projects", tags=["files"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class
templates.env.globals["format_file_size"] = format_file_size

UPLOAD_BASE_DIR = Path("data/uploads")

ALLOWED_EXTENSIONS = {
    ".stl",
    ".3mf",
    ".gcode",
    ".step",
    ".stp",
    ".f3d",
    ".zip",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


def safe_folder_name(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        " ": "_",
        "/": "_",
        "\\": "_",
        ":": "_",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    return "".join(char for char in value if char in allowed) or "unknown"


def get_project_or_redirect(project_id: int, db: Session):
    return db.query(Project).filter(Project.id == project_id).first()


@router.get("/{project_id}/files/upload")
def file_upload_form(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    project = get_project_or_redirect(project_id, db)

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
        name="file_upload.html",
        context={
            "title": "Datei hochladen",
            "project": project
        }
    )


@router.post("/{project_id}/files/upload")
async def file_upload(
    project_id: int,
    upload: UploadFile = File(...),
    version: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project = get_project_or_redirect(project_id, db)

    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    original_filename = upload.filename or "upload"
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        return RedirectResponse(
            url=f"/projects/{project.id}?error=filetype",
            status_code=303
        )

    customer_folder = safe_folder_name(project.customer.name)
    project_folder = safe_folder_name(project.name)

    target_dir = UPLOAD_BASE_DIR / customer_folder / project_folder
    target_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{file_extension}"
    target_path = target_dir / stored_filename

    content = await upload.read()
    target_path.write_bytes(content)

    project_file = ProjectFile(
        project_id=project.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(target_path),
        file_type=file_extension.replace(".", "").upper(),
        version=version.strip(),
        note=note.strip()
    )

    db.add(project_file)

    if project.status == "Anfrage":
        project.status = "Datei prüfen"

    db.commit()

    return RedirectResponse(
        url=f"/projects/{project.id}",
        status_code=303
    )


@router.get("/{project_id}/files/{file_id}/edit")
def file_edit_form(
    project_id: int,
    file_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    project_file = (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id)
        .filter(ProjectFile.project_id == project_id)
        .first()
    )

    if not project_file:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Datei wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="file_edit.html",
        context={
            "title": "Datei bearbeiten",
            "file": project_file,
            "project": project_file.project
        }
    )


@router.post("/{project_id}/files/{file_id}/edit")
def file_edit_save(
    project_id: int,
    file_id: int,
    version: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    project_file = (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id)
        .filter(ProjectFile.project_id == project_id)
        .first()
    )

    if not project_file:
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    project_file.version = version.strip()
    project_file.note = note.strip()

    db.commit()

    return RedirectResponse(
        url=f"/projects/{project_id}",
        status_code=303
    )


@router.post("/{project_id}/files/{file_id}/delete")
def file_delete(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    project_file = (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id)
        .filter(ProjectFile.project_id == project_id)
        .first()
    )

    if not project_file:
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    linked_jobs_count = (
        db.query(PrintJob)
        .filter(PrintJob.file_id == project_file.id)
        .count()
    )

    if linked_jobs_count > 0:
        project_file.note = (
            (project_file.note or "").strip()
            + "\n\nHinweis: Löschen blockiert, weil diese Datei mit einem Druckjob verknüpft ist."
        ).strip()
        db.commit()

        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    file_path = Path(project_file.file_path)

    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
        except OSError:
            pass

    db.delete(project_file)
    db.commit()

    return RedirectResponse(
        url=f"/projects/{project_id}",
        status_code=303
    )


@router.get("/{project_id}/files/{file_id}/download")
def file_download(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    project_file = (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id)
        .filter(ProjectFile.project_id == project_id)
        .first()
    )

    if not project_file:
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    file_path = Path(project_file.file_path)

    if not file_path.exists():
        return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

    return FileResponse(
        path=file_path,
        filename=project_file.original_filename,
        media_type="application/octet-stream"
    )