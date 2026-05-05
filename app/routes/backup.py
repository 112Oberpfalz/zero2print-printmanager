from datetime import datetime
from pathlib import Path
import zipfile

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/backup", tags=["backup"])
templates = Jinja2Templates(directory="app/templates")

DATA_DIR = Path("data")
BACKUP_DIR = DATA_DIR / "backups"


@router.get("")
def backup_index(request: Request):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backups = sorted(
        BACKUP_DIR.glob("*.zip"),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return templates.TemplateResponse(
        request=request,
        name="backup.html",
        context={
            "title": "Backup",
            "backups": backups
        }
    )


@router.post("/create")
def backup_create():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"zero2print_backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename

    paths_to_backup = [
        DATA_DIR / "database.sqlite",
        DATA_DIR / "uploads",
        DATA_DIR / "pdf",
        DATA_DIR / "qr",
    ]

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for path in paths_to_backup:
            if not path.exists():
                continue

            if path.is_file():
                zip_file.write(
                    path,
                    arcname=path.relative_to(DATA_DIR)
                )

            elif path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        zip_file.write(
                            file,
                            arcname=file.relative_to(DATA_DIR)
                        )

    return FileResponse(
        path=backup_path,
        filename=backup_filename,
        media_type="application/zip"
    )


@router.get("/{backup_name}/download")
def backup_download(backup_name: str):
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        return RedirectResponse(url="/backup", status_code=303)

    if backup_path.suffix.lower() != ".zip":
        return RedirectResponse(url="/backup", status_code=303)

    return FileResponse(
        path=backup_path,
        filename=backup_path.name,
        media_type="application/zip"
    )