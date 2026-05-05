from pathlib import Path

folders = [
    "app",
    "app/routes",
    "app/services",
    "app/templates",
    "app/static",
    "data",
    "data/uploads",
    "data/pdf",
    "data/qr",
]

files = {}

files["app/__init__.py"] = ""

files["app/main.py"] = """from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zero2Print PrintManager")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard"}
    )
"""

files["app/database.py"] = """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./data/database.sqlite"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

files["app/models.py"] = """from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="customer")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="Anfrage")
    deadline = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project")
    print_jobs = relationship("PrintJob", back_populates="project")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    version = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("project_files.id"), nullable=True)
    printer_name = Column(String, nullable=True)
    material = Column(String, nullable=True)
    color = Column(String, nullable=True)
    planned_print_time = Column(String, nullable=True)
    planned_weight_grams = Column(Integer, nullable=True)
    status = Column(String, default="Bereit zum Druck")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="print_jobs")


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    print_job_id = Column(Integer, ForeignKey("print_jobs.id"), nullable=True)
    category = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
"""

files["app/routes/__init__.py"] = ""
files["app/routes/customers.py"] = ""
files["app/routes/projects.py"] = ""
files["app/routes/files.py"] = ""
files["app/routes/print_jobs.py"] = ""
files["app/routes/time_entries.py"] = ""

files["app/services/__init__.py"] = ""
files["app/services/pdf_service.py"] = ""
files["app/services/qr_service.py"] = ""
files["app/services/file_service.py"] = ""

files["app/templates/base.html"] = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} | Zero2Print PrintManager</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

<header class="topbar">
    <div class="brand">Zero2Print PrintManager</div>
    <nav>
        <a href="/">Dashboard</a>
        <a href="/customers">Kunden</a>
        <a href="/projects">Projekte</a>
        <a href="/jobs">Druckjobs</a>
        <a href="/time">Zeiten</a>
    </nav>
</header>

<main class="container">
    {% block content %}{% endblock %}
</main>

</body>
</html>
"""

files["app/templates/dashboard.html"] = """{% extends "base.html" %}

{% block content %}
<h1>Dashboard</h1>

<div class="cards">
    <div class="card">
        <h2>Offene Projekte</h2>
        <p>0</p>
    </div>

    <div class="card">
        <h2>Aktive Druckjobs</h2>
        <p>0</p>
    </div>

    <div class="card">
        <h2>Fertige Druckjobs</h2>
        <p>0</p>
    </div>

    <div class="card">
        <h2>Heute erfasste Zeit</h2>
        <p>0 min</p>
    </div>
</div>
{% endblock %}
"""

files["app/static/style.css"] = """* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    color: #1f2937;
}

.topbar {
    background: #111827;
    color: white;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand {
    font-weight: bold;
    font-size: 20px;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 16px;
}

nav a:hover {
    text-decoration: underline;
}

.container {
    padding: 32px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.card h2 {
    font-size: 16px;
    margin-top: 0;
    color: #4b5563;
}

.card p {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 0;
}
"""

files["requirements.txt"] = """fastapi
uvicorn
jinja2
python-multipart
sqlalchemy
reportlab
qrcode
pillow
"""

files["start.bat"] = """@echo off
title Zero2Print PrintManager
echo Starte Zero2Print PrintManager...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
"""

files["README.md"] = """# Zero2Print PrintManager

Lokales 3D-Druck Auftrags- und Dateiverwaltungssystem.

## Start

1. Abhängigkeiten installieren:

pip install -r requirements.txt

2. App starten:

start.bat

3. Im Browser öffnen:

http://localhost:8000

Im Heimnetz:

http://DEINE-PC-IP:8000
"""


def create_project_structure():
    base_path = Path.cwd()

    print("Erstelle Projektstruktur...")
    print(f"Zielordner: {base_path}")
    print()

    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"[ORDNER] {folder}")

    print()

    for file_path, content in files.items():
        path = base_path / file_path

        if path.exists():
            print(f"[SKIP]   {file_path} existiert bereits")
            continue

        path.write_text(content, encoding="utf-8")
        print(f"[DATEI]  {file_path}")

    print()
    print("Fertig.")
    print()
    print("Nächste Schritte:")
    print("1. pip install -r requirements.txt")
    print("2. start.bat ausführen")
    print("3. Browser öffnen: http://localhost:8000")


if __name__ == "__main__":
    create_project_structure()