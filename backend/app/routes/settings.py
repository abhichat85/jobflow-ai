from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import UserSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.crypto import encrypt

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session) -> UserSettings:
    s = db.query(UserSettings).first()
    if not s:
        s = UserSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _to_response(s: UserSettings) -> SettingsResponse:
    return SettingsResponse(
        id=s.id,
        linkedin_cookie_present=bool(s.linkedin_cookie_encrypted),
        linkedin_search_url=s.linkedin_search_url,
        yc_filters=s.yc_filters,
        discovery_enabled=s.discovery_enabled,
        discovery_interval_hours=s.discovery_interval_hours,
        discovery_last_run_at=s.discovery_last_run_at,
        discovery_last_count=s.discovery_last_count,
        auto_review_threshold=s.auto_review_threshold,
        auto_apply_threshold=s.auto_apply_threshold,
        daily_apply_cap=s.daily_apply_cap,
        default_resume_variant=s.default_resume_variant,
        cover_letter_tone=s.cover_letter_tone,
    )


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    return _to_response(_get_or_create(db))


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    s = _get_or_create(db)
    payload = data.model_dump(exclude_unset=True)

    # Special handling: cookie field is encrypted into a different DB column
    if "linkedin_cookie" in payload:
        raw = payload.pop("linkedin_cookie")
        if raw == "" or raw is None:
            s.linkedin_cookie_encrypted = None
        else:
            s.linkedin_cookie_encrypted = encrypt(raw)

    for key, value in payload.items():
        setattr(s, key, value)

    db.commit()
    db.refresh(s)
    return _to_response(s)
