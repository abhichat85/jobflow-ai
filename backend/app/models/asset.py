from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ApplicationAsset(Base):
    __tablename__ = "application_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    resume_variant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("resume_variants.id"), nullable=True
    )
    tailored_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tailored_bullets: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped["Job"] = relationship(back_populates="assets")
    resume_variant: Mapped[Optional["ResumeVariant"]] = relationship()
