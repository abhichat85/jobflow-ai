from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Discovery
    linkedin_cookie_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_search_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Job preferences (natural-language discovery setup)
    job_titles: Mapped[str] = mapped_column(Text, default="[]")
    locations: Mapped[str] = mapped_column(Text, default="[]")
    remote_preference: Mapped[str] = mapped_column(String(20), default="any")
    seniority_levels: Mapped[str] = mapped_column(Text, default="[]")
    company_stage: Mapped[str] = mapped_column(String(20), default="any")
    min_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    linkedin_auth_status: Mapped[str] = mapped_column(String(20), default="disconnected")
    linkedin_search_urls: Mapped[str] = mapped_column(Text, default="[]")
    yc_filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    discovery_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    discovery_interval_hours: Mapped[int] = mapped_column(Integer, default=6)
    discovery_last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discovery_last_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Scoring
    auto_review_threshold: Mapped[int] = mapped_column(Integer, default=65)
    auto_apply_threshold: Mapped[int] = mapped_column(Integer, default=80)
    daily_apply_cap: Mapped[int] = mapped_column(Integer, default=10)

    # Apply
    default_resume_variant: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cover_letter_tone: Mapped[str] = mapped_column(String(20), default="professional")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
