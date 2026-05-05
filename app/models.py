from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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

    projects = relationship(
        "Project",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


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

    files = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    print_jobs = relationship(
        "PrintJob",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    time_entries = relationship(
        "TimeEntry",
        back_populates="project",
        cascade="all, delete-orphan"
    )


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

    print_jobs = relationship(
        "PrintJob",
        back_populates="file"
    )


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
    file = relationship("ProjectFile", back_populates="print_jobs")

    time_entries = relationship(
        "TimeEntry",
        back_populates="print_job"
    )

    checklist = relationship(
        "PrintJobChecklist",
        back_populates="print_job",
        uselist=False,
        cascade="all, delete-orphan"
    )


class PrintJobChecklist(Base):
    __tablename__ = "print_job_checklists"

    id = Column(Integer, primary_key=True, index=True)
    print_job_id = Column(Integer, ForeignKey("print_jobs.id"), nullable=False, unique=True)

    file_checked = Column(Boolean, default=False)
    slicer_checked = Column(Boolean, default=False)
    material_ready = Column(Boolean, default=False)
    bed_cleaned = Column(Boolean, default=False)
    first_layer_checked = Column(Boolean, default=False)
    print_finished_checked = Column(Boolean, default=False)
    post_processing_done = Column(Boolean, default=False)
    packed = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow)

    print_job = relationship("PrintJob", back_populates="checklist")


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

    project = relationship("Project", back_populates="time_entries")
    print_job = relationship("PrintJob", back_populates="time_entries")