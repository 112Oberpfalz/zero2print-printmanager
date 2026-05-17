from dataclasses import dataclass
from datetime import datetime
import re

from sqlalchemy.orm import Session

from app.models import PrintJob


OPEN_JOB_STATUSES = [
    "Bereit zum Druck",
    "Nacharbeit",
]


@dataclass
class PlannedJob:
    job: PrintJob
    estimated_minutes: int | None
    duration_label: str
    deadline_sort: str
    recommendation: str
    score: int


def parse_print_time_to_minutes(value: str | None) -> int | None:
    if not value:
        return None

    text = str(value).strip().lower()
    if not text:
        return None

    if text.isdigit():
        return int(text)

    colon_match = re.match(r"^(\d{1,2})\s*:\s*(\d{1,2})$", text)
    if colon_match:
        hours = int(colon_match.group(1))
        minutes = int(colon_match.group(2))
        return hours * 60 + minutes

    hours = 0
    minutes = 0

    hour_match = re.search(r"(\d+)\s*(h|std|stunde|stunden)", text)
    minute_match = re.search(r"(\d+)\s*(m|min|minute|minuten)", text)

    if hour_match:
        hours = int(hour_match.group(1))

    if minute_match:
        minutes = int(minute_match.group(1))

    total = hours * 60 + minutes
    if total > 0:
        return total

    numbers = re.findall(r"\d+", text)
    if len(numbers) == 1:
        return int(numbers[0])

    return None


def format_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "keine Zeit angegeben"

    hours = minutes // 60
    rest = minutes % 60

    if hours and rest:
        return f"{hours}h {rest}min"
    if hours:
        return f"{hours}h"
    return f"{rest}min"


def normalize_deadline(value: str | None) -> str:
    if not value:
        return "9999-12-31"

    text = str(value).strip()
    if not text:
        return "9999-12-31"

    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"]:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue

    return text


def build_recommendation(job: PrintJob, minutes: int | None) -> str:
    hints = []

    if minutes is None:
        hints.append("Druckzeit ergänzen, damit die Planung genauer wird")
    elif minutes >= 420:
        hints.append("guter Nachtjob")
    elif minutes <= 90:
        hints.append("kurzer Tagesdruck / Lückenfüller")
    else:
        hints.append("normaler Tagesdruck")

    if job.material or job.color:
        material = job.material or "Material offen"
        color = job.color or "Farbe offen"
        hints.append(f"Material/Farbe: {material} / {color}")

    if job.project and job.project.deadline:
        hints.append(f"Deadline: {job.project.deadline}")

    return " · ".join(hints)


def score_job(job: PrintJob, minutes: int | None) -> int:
    score = 0

    if job.project and job.project.deadline:
        score -= 100

    if minutes is None:
        score += 200
    elif minutes <= 90:
        score -= 10
    elif minutes >= 420:
        score += 10

    return score


def get_planned_jobs(db: Session) -> list[PlannedJob]:
    jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status.in_(OPEN_JOB_STATUSES))
        .order_by(PrintJob.created_at.asc())
        .all()
    )

    planned = []

    for job in jobs:
        minutes = parse_print_time_to_minutes(job.planned_print_time)
        deadline_sort = normalize_deadline(job.project.deadline if job.project else None)
        score = score_job(job, minutes)

        planned.append(
            PlannedJob(
                job=job,
                estimated_minutes=minutes,
                duration_label=format_minutes(minutes),
                deadline_sort=deadline_sort,
                recommendation=build_recommendation(job, minutes),
                score=score,
            )
        )

    planned.sort(
        key=lambda item: (
            item.deadline_sort,
            item.score,
            (item.job.material or "").lower(),
            (item.job.color or "").lower(),
            item.estimated_minutes or 999999,
            item.job.created_at,
        )
    )

    return planned


def planner_summary(planned_jobs: list[PlannedJob]) -> dict:
    total_minutes = sum(item.estimated_minutes or 0 for item in planned_jobs)
    missing_times = sum(1 for item in planned_jobs if item.estimated_minutes is None)
    night_jobs = sum(
        1 for item in planned_jobs
        if item.estimated_minutes and item.estimated_minutes >= 420
    )
    short_jobs = sum(
        1 for item in planned_jobs
        if item.estimated_minutes and item.estimated_minutes <= 90
    )

    return {
        "open_jobs": len(planned_jobs),
        "total_minutes": total_minutes,
        "total_label": format_minutes(total_minutes),
        "missing_times": missing_times,
        "night_jobs": night_jobs,
        "short_jobs": short_jobs,
    }