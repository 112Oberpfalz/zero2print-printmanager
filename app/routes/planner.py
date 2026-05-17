from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.planner_service import get_planned_jobs, planner_summary

router = APIRouter(prefix="/planner", tags=["planner"])

templates = Jinja2Templates(directory="app/templates")


@router.get("")
def planner_index(request: Request, db: Session = Depends(get_db)):
    planned_jobs = get_planned_jobs(db)
    summary = planner_summary(planned_jobs)

    next_job = planned_jobs[0] if planned_jobs else None

    return templates.TemplateResponse(
        request=request,
        name="planner.html",
        context={
            "title": "Druckplanung",
            "planned_jobs": planned_jobs,
            "summary": summary,
            "next_job": next_job,
        }
    )