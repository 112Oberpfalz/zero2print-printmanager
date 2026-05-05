from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Customer
from app.template_helpers import status_class

router = APIRouter(prefix="/customers", tags=["customers"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["status_class"] = status_class


@router.get("")
def customers_index(
    request: Request,
    q: str = Query(default=""),
    db: Session = Depends(get_db)
):
    query = db.query(Customer)

    search = q.strip()

    if search:
        query = query.filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%"),
                Customer.note.ilike(f"%{search}%"),
            )
        )

    customers = query.order_by(Customer.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="customers.html",
        context={
            "title": "Kunden",
            "customers": customers,
            "q": search
        }
    )


@router.get("/new")
def customer_new(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="customer_new.html",
        context={"title": "Kunde anlegen"}
    )


@router.post("/new")
def customer_create(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    customer = Customer(
        name=name.strip(),
        email=email.strip(),
        phone=phone.strip(),
        note=note.strip()
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return RedirectResponse(
        url=f"/customers/{customer.id}",
        status_code=303
    )


@router.get("/{customer_id}/edit")
def customer_edit(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Kunde wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="customer_edit.html",
        context={
            "title": "Kunde bearbeiten",
            "customer": customer
        }
    )


@router.post("/{customer_id}/edit")
def customer_update(
    customer_id: int,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        return RedirectResponse(url="/customers", status_code=303)

    customer.name = name.strip()
    customer.email = email.strip()
    customer.phone = phone.strip()
    customer.note = note.strip()

    db.commit()

    return RedirectResponse(
        url=f"/customers/{customer.id}",
        status_code=303
    )


@router.get("/{customer_id}")
def customer_detail(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={
                "title": "Nicht gefunden",
                "message": "Kunde wurde nicht gefunden."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="customer_detail.html",
        context={
            "title": customer.name,
            "customer": customer
        }
    )