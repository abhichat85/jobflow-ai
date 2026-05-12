from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interview_stage: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    interviewer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interviewer_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prep_doc_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    outcome: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="interviews")
    contact: Mapped[Optional["Contact"]] = relationship()
    prep: Mapped[list["InterviewPrep"]] = relationship(back_populates="interview")


class InterviewPrep(Base):
    __tablename__ = "interview_prep"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    company_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    likely_questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    suggested_answers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    talking_points: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    questions_to_ask: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    thirty_sixty_ninety_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_negotiation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    interview: Mapped["Interview"] = relationship(back_populates="prep")
