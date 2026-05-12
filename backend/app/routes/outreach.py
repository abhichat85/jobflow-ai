from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outreach import Contact, Outreach
from app.schemas.outreach import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    OutreachCreate,
    OutreachResponse,
    OutreachUpdate,
)

router = APIRouter(prefix="/api", tags=["outreach"])


@router.get("/contacts", response_model=list[ContactResponse])
def list_contacts(
    company: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    query = db.query(Contact)
    if company:
        query = query.filter(Contact.company_name.ilike(f"%{company}%"))
    return query.order_by(Contact.created_at.desc()).all()


@router.post("/contacts", response_model=ContactResponse)
def create_contact(data: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db)):
    contact = db.query(Contact).get(contact_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/outreach", response_model=list[OutreachResponse])
def list_outreach(
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Outreach)
    if status:
        query = query.filter(Outreach.status == status)
    if channel:
        query = query.filter(Outreach.channel == channel)
    return query.order_by(Outreach.created_at.desc()).all()


@router.post("/outreach", response_model=OutreachResponse)
def create_outreach(data: OutreachCreate, db: Session = Depends(get_db)):
    outreach = Outreach(**data.model_dump())
    db.add(outreach)
    db.commit()
    db.refresh(outreach)
    return outreach


@router.put("/outreach/{outreach_id}", response_model=OutreachResponse)
def update_outreach(outreach_id: int, data: OutreachUpdate, db: Session = Depends(get_db)):
    outreach = db.query(Outreach).get(outreach_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(outreach, key, value)
    db.commit()
    db.refresh(outreach)
    return outreach


@router.post("/outreach/{outreach_id}/approve", response_model=OutreachResponse)
def approve_outreach(outreach_id: int, db: Session = Depends(get_db)):
    outreach = db.query(Outreach).get(outreach_id)
    outreach.status = "sent"
    outreach.sent_at = datetime.utcnow()
    if outreach.message_type == "initial":
        outreach.scheduled_followup_at = datetime.utcnow() + timedelta(days=2)
    db.commit()
    db.refresh(outreach)
    return outreach


@router.post("/outreach/{outreach_id}/mark-sent", response_model=OutreachResponse)
def mark_sent(outreach_id: int, db: Session = Depends(get_db)):
    outreach = db.query(Outreach).get(outreach_id)
    outreach.status = "sent"
    outreach.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(outreach)
    return outreach


@router.post("/outreach/{outreach_id}/mark-replied", response_model=OutreachResponse)
def mark_replied(outreach_id: int, db: Session = Depends(get_db)):
    outreach = db.query(Outreach).get(outreach_id)
    outreach.status = "replied"
    outreach.reply_received_at = datetime.utcnow()
    db.commit()
    db.refresh(outreach)
    return outreach


@router.get("/outreach/follow-ups", response_model=list[OutreachResponse])
def get_pending_followups(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    return (
        db.query(Outreach)
        .filter(
            Outreach.scheduled_followup_at <= now,
            Outreach.status == "sent",
        )
        .all()
    )
