from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    twitter_handle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    relationship_strength: Mapped[str] = mapped_column(String(20), default="cold")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    outreach_messages: Mapped[list["Outreach"]] = relationship(back_populates="contact")


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    channel: Mapped[str] = mapped_column(String(20))
    message_type: Mapped[str] = mapped_column(String(20))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_followup_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reply_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reply_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped[Optional["Job"]] = relationship(back_populates="outreach_messages")
    contact: Mapped["Contact"] = relationship(back_populates="outreach_messages")
