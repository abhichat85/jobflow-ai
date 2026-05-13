from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ApplicationAttempt(Base):
    __tablename__ = "application_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    status: Mapped[str] = mapped_column(String(20))  # "success" | "failed" | "in_progress"
    resume_variant: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cover_letter_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    form_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confirmation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped["Job"] = relationship("Job")
