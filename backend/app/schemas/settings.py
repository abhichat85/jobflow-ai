from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    id: int
    # Discovery
    linkedin_cookie_present: bool  # bool flag, never the value itself
    linkedin_search_url: Optional[str] = None
    yc_filters: Optional[dict] = None
    discovery_enabled: bool
    discovery_interval_hours: int
    discovery_last_run_at: Optional[datetime] = None
    discovery_last_count: Optional[int] = None
    # Scoring
    auto_review_threshold: int
    auto_apply_threshold: int
    daily_apply_cap: int
    # Apply
    default_resume_variant: Optional[str] = None
    cover_letter_tone: str

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    # If linkedin_cookie is provided, it's encrypted and stored.
    # Empty string clears the cookie.
    linkedin_cookie: Optional[str] = None
    linkedin_search_url: Optional[str] = None
    yc_filters: Optional[dict] = None
    discovery_enabled: Optional[bool] = None
    discovery_interval_hours: Optional[int] = None
    auto_review_threshold: Optional[int] = None
    auto_apply_threshold: Optional[int] = None
    daily_apply_cap: Optional[int] = None
    default_resume_variant: Optional[str] = None
    cover_letter_tone: Optional[str] = None
