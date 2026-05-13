from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    company_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="discovered")
    fit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    apply_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ats_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    application_status: Mapped[str] = mapped_column(String(30), default="discovered")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    requirements: Mapped[list["JobRequirement"]] = relationship(back_populates="job")
    scores: Mapped[list["JobScore"]] = relationship(back_populates="job")
    assets: Mapped[list] = relationship("ApplicationAsset", back_populates="job")
    outreach_messages: Mapped[list] = relationship("Outreach", back_populates="job")
    interviews: Mapped[list] = relationship("Interview", back_populates="job")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    must_have_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    nice_to_have_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    years_experience_required: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    education_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_responsibilities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    culture_signals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    red_flags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="requirements")


class JobScore(Base):
    __tablename__ = "job_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    role_match: Mapped[int] = mapped_column(Integer, default=0)
    skill_match: Mapped[int] = mapped_column(Integer, default=0)
    startup_fit: Mapped[int] = mapped_column(Integer, default=0)
    ai_relevance: Mapped[int] = mapped_column(Integer, default=0)
    location_fit: Mapped[int] = mapped_column(Integer, default=0)
    speed_of_hiring: Mapped[int] = mapped_column(Integer, default=0)
    compensation_fit: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    decision: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_angle: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    outreach_angle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="scores")
