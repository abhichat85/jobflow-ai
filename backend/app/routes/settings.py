import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import UserSettings
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.browser import _auth_sessions, open_login_window
from app.services.crypto import encrypt
from app.services.linkedin_url_builder import build_search_urls

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


def _to_preferences_response(s: UserSettings) -> PreferencesResponse:
    urls = json.loads(s.linkedin_search_urls or "[]")
    return PreferencesResponse(
        job_titles=json.loads(s.job_titles or "[]"),
        locations=json.loads(s.locations or "[]"),
        remote_preference=s.remote_preference,
        seniority_levels=json.loads(s.seniority_levels or "[]"),
        company_stage=s.company_stage,
        min_salary=s.min_salary,
        linkedin_auth_status=s.linkedin_auth_status,
        linkedin_search_urls=urls,
        linkedin_search_url=urls[0] if urls else s.linkedin_search_url,
    )


@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(db: Session = Depends(get_db)):
    return _to_preferences_response(_get_or_create(db))


@router.put("/preferences", response_model=PreferencesResponse)
def update_preferences(data: PreferencesUpdate, db: Session = Depends(get_db)):
    s = _get_or_create(db)
    payload = data.model_dump(exclude_unset=True)

    # JSON-encode list fields before storing
    for list_field in ("job_titles", "locations", "seniority_levels"):
        if list_field in payload:
            payload[list_field] = json.dumps(payload[list_field])

    for key, value in payload.items():
        setattr(s, key, value)

    # Rebuild search URLs from updated preferences
    urls = build_search_urls(s)
    s.linkedin_search_urls = json.dumps(urls)
    # Keep legacy single-URL field in sync
    s.linkedin_search_url = urls[0] if urls else None

    db.commit()
    db.refresh(s)
    return _to_preferences_response(s)


@router.post("/linkedin/start-auth")
async def start_linkedin_auth(db: Session = Depends(get_db)):
    """Spawn a visible Chromium login window. Returns session_id for polling."""
    session_id = str(uuid.uuid4())
    asyncio.create_task(open_login_window(session_id))
    return {"session_id": session_id}


@router.get("/linkedin/auth-status/{session_id}")
def get_linkedin_auth_status(session_id: str):
    """Poll for LinkedIn auth completion. Returns waiting|connected|timeout."""
    if session_id not in _auth_sessions:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return _auth_sessions[session_id]


@router.delete("/linkedin/disconnect")
def disconnect_linkedin(db: Session = Depends(get_db)):
    """Clear the LinkedIn session cookie and reset auth status."""
    s = _get_or_create(db)
    s.linkedin_cookie_encrypted = None
    s.linkedin_auth_status = "disconnected"
    db.commit()
    return {"status": "disconnected"}
