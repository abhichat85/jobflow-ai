# LinkedIn Discovery UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the technical LinkedIn cookie+URL setup with a natural-language 3-step wizard: job preferences → Playwright-guided login → ready state.

**Architecture:** New `linkedin_url_builder` service translates structured preferences (roles, location, seniority) into LinkedIn search URLs. A new `open_login_window()` in `BrowserService` spawns a visible Chromium window so users log in normally and the app captures the session cookie automatically. A `/setup` wizard page orchestrates the flow; the existing discovery pipeline is unchanged downstream.

**Tech Stack:** FastAPI, SQLAlchemy + Alembic (SQLite), Playwright (async), Next.js 14 App Router, TypeScript, Tailwind CSS

---

## File Map

### New files
| File | Responsibility |
|------|---------------|
| `backend/app/services/linkedin_url_builder.py` | Build LinkedIn search URLs from structured preferences |
| `backend/app/schemas/preferences.py` | Pydantic schemas for preferences GET/PUT |
| `backend/alembic/versions/<hash>_add_job_preferences_to_settings.py` | DB migration |
| `backend/tests/test_linkedin_url_builder.py` | URL builder unit tests |
| `backend/tests/test_routes_preferences.py` | Preferences API tests |
| `backend/tests/test_routes_linkedin_auth.py` | LinkedIn auth endpoints tests |
| `frontend/app/setup/page.tsx` | 3-step wizard page |
| `frontend/components/setup/preferences-step.tsx` | Step 1 — job preferences form |
| `frontend/components/setup/linkedin-auth-step.tsx` | Step 2 — guided login |
| `frontend/components/setup/ready-step.tsx` | Step 3 — success state |
| `frontend/components/ui/tag-input.tsx` | Reusable multi-tag input |

### Modified files
| File | Change |
|------|--------|
| `backend/app/models/settings.py` | +7 columns: `job_titles`, `locations`, `remote_preference`, `seniority_levels`, `company_stage`, `min_salary`, `linkedin_auth_status`, `linkedin_search_urls` |
| `backend/app/services/browser.py` | Add `open_login_window()` + module-level `_auth_sessions` dict |
| `backend/app/routes/settings.py` | Add 5 new endpoints (preferences + LinkedIn auth) |
| `backend/app/workflows/discovery.py` | Set `auth_status="expired"` on `SessionExpiredError`; loop through `linkedin_search_urls` |
| `frontend/lib/api.ts` | New types + functions for preferences and auth endpoints |
| `frontend/app/settings/page.tsx` | Replace LinkedIn cookie/URL section with summary card |
| `frontend/components/layout/sidebar.tsx` | Auto-redirect to `/setup` if preferences empty |

---

## Task 1: UserSettings Migration

**Files:**
- Modify: `backend/app/models/settings.py`
- Create: `backend/alembic/versions/<hash>_add_job_preferences_to_settings.py`
- Modify: `backend/tests/test_models_settings.py`

- [ ] **Step 1: Add columns to UserSettings model**

Open `backend/app/models/settings.py`. After the `linkedin_search_url` line, add:

```python
# Job preferences (natural-language discovery setup)
job_titles: Mapped[str] = mapped_column(Text, default="[]")
locations: Mapped[str] = mapped_column(Text, default="[]")
remote_preference: Mapped[str] = mapped_column(String(20), default="any")
seniority_levels: Mapped[str] = mapped_column(Text, default="[]")
company_stage: Mapped[str] = mapped_column(String(20), default="any")
min_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
linkedin_auth_status: Mapped[str] = mapped_column(String(20), default="disconnected")
linkedin_search_urls: Mapped[str] = mapped_column(Text, default="[]")
```

The full updated imports block should be:
```python
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
```
(`Text` is already imported — no change needed.)

- [ ] **Step 2: Write the Alembic migration**

Run `cd backend && .venv/bin/alembic revision --autogenerate -m "add_job_preferences_to_settings"` to generate the file, then verify it contains `add_column` ops for all 8 new fields. If autogenerate misses any, add them manually. The migration should look like:

```python
def upgrade() -> None:
    op.add_column("user_settings", sa.Column("job_titles", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("locations", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("remote_preference", sa.String(20), nullable=False, server_default="any"))
    op.add_column("user_settings", sa.Column("seniority_levels", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("user_settings", sa.Column("company_stage", sa.String(20), nullable=False, server_default="any"))
    op.add_column("user_settings", sa.Column("min_salary", sa.Integer(), nullable=True))
    op.add_column("user_settings", sa.Column("linkedin_auth_status", sa.String(20), nullable=False, server_default="disconnected"))
    op.add_column("user_settings", sa.Column("linkedin_search_urls", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("user_settings", "linkedin_search_urls")
    op.drop_column("user_settings", "linkedin_auth_status")
    op.drop_column("user_settings", "min_salary")
    op.drop_column("user_settings", "company_stage")
    op.drop_column("user_settings", "seniority_levels")
    op.drop_column("user_settings", "remote_preference")
    op.drop_column("user_settings", "locations")
    op.drop_column("user_settings", "job_titles")
```

- [ ] **Step 3: Write failing tests for new columns**

Append to `backend/tests/test_models_settings.py`:

```python
def test_user_settings_new_preference_defaults(db: Session):
    s = UserSettings()
    db.add(s)
    db.commit()
    db.refresh(s)
    assert s.job_titles == "[]"
    assert s.locations == "[]"
    assert s.remote_preference == "any"
    assert s.seniority_levels == "[]"
    assert s.company_stage == "any"
    assert s.min_salary is None
    assert s.linkedin_auth_status == "disconnected"
    assert s.linkedin_search_urls == "[]"
```

- [ ] **Step 4: Run failing test**

```bash
cd backend && .venv/bin/pytest tests/test_models_settings.py::test_user_settings_new_preference_defaults -v
```
Expected: FAIL — columns not in DB schema yet (or AttributeError if model was already updated but migration not run).

- [ ] **Step 5: Run migration against dev DB**

```bash
cd backend && .venv/bin/alembic upgrade head
```
Expected: `Running upgrade ... -> <hash>, add_job_preferences_to_settings`

- [ ] **Step 6: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_models_settings.py -v
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/settings.py backend/alembic/versions/ backend/tests/test_models_settings.py
git commit -m "feat: add job preference columns to UserSettings"
```

---

## Task 2: LinkedIn URL Builder Service

**Files:**
- Create: `backend/app/services/linkedin_url_builder.py`
- Create: `backend/tests/test_linkedin_url_builder.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_linkedin_url_builder.py`:

```python
import json
import urllib.parse
from app.models.settings import UserSettings
from app.services.linkedin_url_builder import build_search_urls


def _make_settings(**kwargs) -> UserSettings:
    s = UserSettings()
    s.job_titles = json.dumps(kwargs.get("job_titles", ["Product Manager"]))
    s.locations = json.dumps(kwargs.get("locations", ["United States"]))
    s.remote_preference = kwargs.get("remote_preference", "any")
    s.seniority_levels = json.dumps(kwargs.get("seniority_levels", []))
    s.company_stage = kwargs.get("company_stage", "any")
    s.min_salary = kwargs.get("min_salary", None)
    return s


def test_basic_url_structure():
    s = _make_settings()
    urls = build_search_urls(s)
    assert len(urls) == 1
    parsed = urllib.parse.urlparse(urls[0])
    assert parsed.netloc == "www.linkedin.com"
    assert parsed.path == "/jobs/search/"
    qs = urllib.parse.parse_qs(parsed.query)
    assert qs["keywords"][0] == "Product Manager"
    assert qs["location"][0] == "United States"
    assert qs["f_TPR"][0] == "r604800"  # last 7 days always applied


def test_multiple_titles_produce_multiple_urls():
    s = _make_settings(job_titles=["Product Manager", "Senior PM", "Head of Product"])
    urls = build_search_urls(s)
    assert len(urls) == 3
    keywords = [urllib.parse.parse_qs(urllib.parse.urlparse(u).query)["keywords"][0] for u in urls]
    assert "Product Manager" in keywords
    assert "Senior PM" in keywords
    assert "Head of Product" in keywords


def test_remote_preference_maps_to_f_wt():
    for pref, code in [("remote", "2"), ("hybrid", "3"), ("onsite", "1")]:
        s = _make_settings(remote_preference=pref)
        urls = build_search_urls(s)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
        assert qs["f_WT"][0] == code, f"Expected f_WT={code} for {pref}"


def test_any_remote_omits_f_wt():
    s = _make_settings(remote_preference="any")
    urls = build_search_urls(s)
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
    assert "f_WT" not in qs


def test_seniority_maps_to_f_e():
    s = _make_settings(seniority_levels=["Senior", "Lead"])
    urls = build_search_urls(s)
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
    # Both Senior and Lead map to code "4"
    assert qs["f_E"][0] == "4"


def test_mixed_seniority_codes():
    s = _make_settings(seniority_levels=["Entry", "Senior", "Director+"])
    urls = build_search_urls(s)
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
    codes = set(qs["f_E"][0].split(","))
    assert codes == {"2", "4", "5"}


def test_empty_titles_returns_empty_list():
    s = _make_settings(job_titles=[])
    urls = build_search_urls(s)
    assert urls == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/pytest tests/test_linkedin_url_builder.py -v
```
Expected: ModuleNotFoundError — file doesn't exist yet

- [ ] **Step 3: Implement the URL builder**

Create `backend/app/services/linkedin_url_builder.py`:

```python
"""Build LinkedIn Jobs search URLs from structured UserSettings preferences."""
import json
import urllib.parse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.settings import UserSettings

# LinkedIn URL parameter mappings
_REMOTE_TO_F_WT = {
    "remote": "2",
    "hybrid": "3",
    "onsite": "1",
}

_SENIORITY_TO_F_E = {
    "Entry": "2",
    "Mid": "3",
    "Senior": "4",
    "Lead": "4",
    "Director+": "5",
}

_BASE_URL = "https://www.linkedin.com/jobs/search/"


def build_search_urls(settings: "UserSettings") -> list[str]:
    """Return one LinkedIn search URL per job title.

    company_stage has no LinkedIn URL equivalent — stored for future
    post-discovery filtering only.
    """
    titles: list[str] = json.loads(settings.job_titles or "[]")
    if not titles:
        return []

    locations: list[str] = json.loads(settings.locations or "[]")
    location = locations[0] if locations else "United States"

    seniority_levels: list[str] = json.loads(settings.seniority_levels or "[]")
    e_codes = sorted({_SENIORITY_TO_F_E[lvl] for lvl in seniority_levels if lvl in _SENIORITY_TO_F_E})

    urls = []
    for title in titles:
        params: dict[str, str] = {
            "keywords": title,
            "location": location,
            "f_TPR": "r604800",  # posted in last 7 days
        }
        if settings.remote_preference in _REMOTE_TO_F_WT:
            params["f_WT"] = _REMOTE_TO_F_WT[settings.remote_preference]
        if e_codes:
            params["f_E"] = ",".join(e_codes)

        urls.append(_BASE_URL + "?" + urllib.parse.urlencode(params))

    return urls
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_linkedin_url_builder.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/linkedin_url_builder.py backend/tests/test_linkedin_url_builder.py
git commit -m "feat: add LinkedIn URL builder from job preferences"
```

---

## Task 3: Preferences Schemas & API Endpoints

**Files:**
- Create: `backend/app/schemas/preferences.py`
- Modify: `backend/app/routes/settings.py`
- Create: `backend/tests/test_routes_preferences.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_routes_preferences.py`:

```python
"""Tests for GET/PUT /api/settings/preferences."""


def test_get_preferences_returns_defaults(client):
    resp = client.get("/api/settings/preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_titles"] == []
    assert body["locations"] == []
    assert body["remote_preference"] == "any"
    assert body["seniority_levels"] == []
    assert body["company_stage"] == "any"
    assert body["min_salary"] is None
    assert body["linkedin_auth_status"] == "disconnected"
    assert body["linkedin_search_urls"] == []


def test_put_preferences_saves_and_builds_urls(client):
    resp = client.put("/api/settings/preferences", json={
        "job_titles": ["Product Manager", "Senior PM"],
        "locations": ["United States"],
        "remote_preference": "remote",
        "seniority_levels": ["Senior"],
        "company_stage": "any",
        "min_salary": None,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_titles"] == ["Product Manager", "Senior PM"]
    assert body["remote_preference"] == "remote"
    # URLs should be auto-constructed (2 titles → 2 URLs)
    assert len(body["linkedin_search_urls"]) == 2
    assert all("linkedin.com/jobs/search" in u for u in body["linkedin_search_urls"])
    assert all("f_WT=2" in u for u in body["linkedin_search_urls"])  # remote
    # legacy field also populated
    assert body["linkedin_search_url"] is not None


def test_put_preferences_partial_update(client):
    client.put("/api/settings/preferences", json={"job_titles": ["PM"]})
    resp = client.put("/api/settings/preferences", json={"remote_preference": "hybrid"})
    assert resp.status_code == 200
    body = resp.json()
    # Previously set field preserved
    assert body["job_titles"] == ["PM"]
    assert body["remote_preference"] == "hybrid"


def test_put_preferences_empty_titles_clears_search_urls(client):
    client.put("/api/settings/preferences", json={"job_titles": ["PM"]})
    resp = client.put("/api/settings/preferences", json={"job_titles": []})
    assert resp.status_code == 200
    assert resp.json()["linkedin_search_urls"] == []
```

- [ ] **Step 2: Run failing tests**

```bash
cd backend && .venv/bin/pytest tests/test_routes_preferences.py -v
```
Expected: 404 errors — endpoints don't exist yet

- [ ] **Step 3: Create preferences schemas**

Create `backend/app/schemas/preferences.py`:

```python
import json
from typing import Optional
from pydantic import BaseModel, field_validator


class PreferencesResponse(BaseModel):
    job_titles: list[str]
    locations: list[str]
    remote_preference: str
    seniority_levels: list[str]
    company_stage: str
    min_salary: Optional[int]
    linkedin_auth_status: str
    linkedin_search_urls: list[str]
    linkedin_search_url: Optional[str]  # legacy field for backward compat

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    job_titles: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    remote_preference: Optional[str] = None
    seniority_levels: Optional[list[str]] = None
    company_stage: Optional[str] = None
    min_salary: Optional[int] = None
```

- [ ] **Step 4: Add the two endpoints to settings router**

In `backend/app/routes/settings.py`, add these imports at the top:

```python
import json
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.services.linkedin_url_builder import build_search_urls
```

Then append these two route functions after the existing `update_settings` function:

```python
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
```

- [ ] **Step 5: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_routes_preferences.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/preferences.py backend/app/routes/settings.py backend/tests/test_routes_preferences.py
git commit -m "feat: add job preferences GET/PUT endpoints"
```

---

## Task 4: Browser Service — `open_login_window()`

**Files:**
- Modify: `backend/app/services/browser.py`
- Create: `backend/tests/test_browser_login.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_browser_login.py`:

```python
"""Tests for open_login_window() — mocks Playwright to avoid real browser."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import UserSettings
from app.services.browser import open_login_window, _auth_sessions


@pytest.fixture()
def mem_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    # Seed a UserSettings row
    db = Session()
    db.add(UserSettings())
    db.commit()
    db.close()
    return Session


def _make_mock_playwright(li_at_value: str):
    """Build a mock playwright stack that returns li_at on second cookie poll."""
    mock_cookie = {"name": "li_at", "value": li_at_value}
    call_count = {"n": 0}

    async def fake_cookies():
        call_count["n"] += 1
        if call_count["n"] >= 2:
            return [mock_cookie]
        return []

    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.cookies = fake_cookies
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright_instance = AsyncMock()
    mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

    return mock_playwright_instance, mock_browser


@pytest.mark.asyncio
async def test_open_login_window_captures_cookie(mem_db):
    mock_pw, mock_browser = _make_mock_playwright("fake-li-at-token")
    session_id = "test-session-abc"

    with patch("app.services.browser.async_playwright") as mock_ap, \
         patch("app.services.browser.SessionLocal", mem_db):
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_pw)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_ap.return_value = cm

        await open_login_window(session_id)

    assert _auth_sessions[session_id]["status"] == "connected"
    # Verify cookie was saved to DB
    db = mem_db()
    s = db.query(UserSettings).first()
    assert s.linkedin_cookie_encrypted is not None
    assert s.linkedin_auth_status == "connected"
    db.close()
```

- [ ] **Step 2: Run failing test**

```bash
cd backend && .venv/bin/pytest tests/test_browser_login.py -v
```
Expected: ImportError — `open_login_window` and `_auth_sessions` not defined yet

- [ ] **Step 3: Implement `open_login_window` in browser.py**

Add the following to `backend/app/services/browser.py` — at the top, add `import asyncio` and `import uuid` (already has `asyncio`), then add after the existing class and before `get_browser_service()`:

First update the imports to include:
```python
import asyncio
import logging
import uuid
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
```

Then add the `_auth_sessions` dict and `open_login_window` function before `get_browser_service`:

```python
# Module-level dict tracking in-progress LinkedIn auth sessions.
# Safe for single-process local deployment.
# Key: session_id (uuid4 string), Value: {"status": "waiting"|"connected"|"timeout"}
_auth_sessions: dict[str, dict] = {}


async def open_login_window(session_id: str) -> None:
    """Spawn a visible Chromium window for LinkedIn login.

    Polls for the li_at session cookie, saves it encrypted to DB, then closes.
    Updates _auth_sessions[session_id] to reflect outcome.
    """
    from app.database import SessionLocal
    from app.models.settings import UserSettings
    from app.services.crypto import encrypt

    _auth_sessions[session_id] = {"status": "waiting"}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            await page.goto("https://www.linkedin.com/login")

            deadline = asyncio.get_event_loop().time() + 300  # 5-minute timeout
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(2)
                cookies = await context.cookies()
                li_at = next(
                    (c["value"] for c in cookies if c["name"] == "li_at"), None
                )
                if li_at:
                    db = SessionLocal()
                    try:
                        s = db.query(UserSettings).first()
                        if not s:
                            s = UserSettings()
                            db.add(s)
                        s.linkedin_cookie_encrypted = encrypt(li_at)
                        s.linkedin_auth_status = "connected"
                        db.commit()
                    finally:
                        db.close()
                    _auth_sessions[session_id] = {"status": "connected"}
                    logger.info("LinkedIn auth captured for session %s", session_id)
                    return

            _auth_sessions[session_id] = {"status": "timeout"}
            logger.warning("LinkedIn auth timed out for session %s", session_id)
        finally:
            await browser.close()
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_browser_login.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/browser.py backend/tests/test_browser_login.py
git commit -m "feat: add open_login_window() to BrowserService for guided LinkedIn auth"
```

---

## Task 5: LinkedIn Auth API Endpoints

**Files:**
- Modify: `backend/app/routes/settings.py`
- Create: `backend/tests/test_routes_linkedin_auth.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_routes_linkedin_auth.py`:

```python
"""Tests for LinkedIn auth endpoints."""
from unittest.mock import patch, AsyncMock


def test_start_auth_returns_session_id(client):
    with patch("app.routes.settings.asyncio") as mock_asyncio, \
         patch("app.routes.settings.open_login_window"):
        mock_asyncio.create_task = lambda coro: None
        mock_asyncio.get_event_loop = lambda: None
        resp = client.post("/api/settings/linkedin/start-auth")
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert len(body["session_id"]) == 36  # uuid4 format


def test_auth_status_waiting(client):
    from app.services.browser import _auth_sessions
    _auth_sessions["test-wait-id"] = {"status": "waiting"}
    resp = client.get("/api/settings/linkedin/auth-status/test-wait-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "waiting"


def test_auth_status_connected(client):
    from app.services.browser import _auth_sessions
    _auth_sessions["test-conn-id"] = {"status": "connected"}
    resp = client.get("/api/settings/linkedin/auth-status/test-conn-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "connected"


def test_auth_status_unknown_session_returns_404(client):
    resp = client.get("/api/settings/linkedin/auth-status/nonexistent-id")
    assert resp.status_code == 404


def test_disconnect_clears_cookie_and_status(client):
    # First set a cookie
    client.put("/api/settings", json={"linkedin_cookie": "fake-cookie"})
    resp = client.delete("/api/settings/linkedin/disconnect")
    assert resp.status_code == 200
    # Verify cookie cleared
    settings = client.get("/api/settings").json()
    assert settings["linkedin_cookie_present"] is False
    # Verify status
    prefs = client.get("/api/settings/preferences").json()
    assert prefs["linkedin_auth_status"] == "disconnected"
```

- [ ] **Step 2: Run failing tests**

```bash
cd backend && .venv/bin/pytest tests/test_routes_linkedin_auth.py -v
```
Expected: 404 errors — endpoints don't exist

- [ ] **Step 3: Add LinkedIn auth endpoints to settings router**

In `backend/app/routes/settings.py`, add these imports at the top:

```python
import asyncio
import uuid
from fastapi import HTTPException
from app.services.browser import open_login_window, _auth_sessions
```

Then append after the `update_preferences` function:

```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_routes_linkedin_auth.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/settings.py backend/tests/test_routes_linkedin_auth.py
git commit -m "feat: add LinkedIn start-auth, auth-status, disconnect endpoints"
```

---

## Task 6: Discovery Workflow — Expiry Status & Multi-URL Support

**Files:**
- Modify: `backend/app/workflows/discovery.py`
- Modify: `backend/tests/test_scraper.py` (add new test)

- [ ] **Step 1: Write failing test**

Add these tests to `backend/tests/test_scraper.py` (or create a new file `backend/tests/test_discovery_workflow.py` if the existing file doesn't have a `client` or `db` fixture):

```python
# In backend/tests/test_discovery_workflow.py
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import UserSettings
from app.scrapers.linkedin import SessionExpiredError
from app.workflows.discovery import run_discovery


@pytest.fixture()
def db_with_settings():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    s = UserSettings()
    s.linkedin_cookie_encrypted = "fake-encrypted"
    s.linkedin_search_urls = json.dumps([
        "https://www.linkedin.com/jobs/search/?keywords=PM",
        "https://www.linkedin.com/jobs/search/?keywords=Senior+PM",
    ])
    s.discovery_enabled = True
    db.add(s)
    db.commit()
    db.close()
    return Session


@pytest.mark.asyncio
async def test_session_expired_sets_auth_status(db_with_settings):
    db = db_with_settings()

    with patch("app.workflows.discovery.YCScraper") as MockYC, \
         patch("app.workflows.discovery.LinkedInScraper") as MockLI, \
         patch("app.workflows.discovery.decrypt", return_value="fake-cookie"), \
         patch("app.workflows.discovery.get_browser_service", return_value=MagicMock()):
        mock_li_instance = AsyncMock()
        mock_li_instance.source_name = "linkedin"
        mock_li_instance.scrape = AsyncMock(side_effect=SessionExpiredError("expired"))
        MockLI.return_value = mock_li_instance

        mock_yc_instance = AsyncMock()
        mock_yc_instance.source_name = "yc"
        mock_yc_instance.scrape = AsyncMock(return_value=[])
        MockYC.return_value = mock_yc_instance

        await run_discovery(db)

    s = db.query(UserSettings).first()
    assert s.linkedin_auth_status == "expired"
    db.close()
```

- [ ] **Step 2: Run failing test**

```bash
cd backend && .venv/bin/pytest tests/test_discovery_workflow.py -v
```
Expected: FAIL — `linkedin_auth_status` not updated on `SessionExpiredError`

- [ ] **Step 3: Update `_get_enabled_scrapers` to use `linkedin_search_urls`**

In `backend/app/workflows/discovery.py`, update `_get_enabled_scrapers`:

```python
def _get_enabled_scrapers(settings: UserSettings, browser) -> list[BaseJobScraper]:
    scrapers: list[BaseJobScraper] = [YCScraper()]
    cookie = decrypt(settings.linkedin_cookie_encrypted)
    search_urls = json.loads(settings.linkedin_search_urls or "[]")
    # Fall back to legacy single URL if new list is empty
    if not search_urls and settings.linkedin_search_url:
        search_urls = [settings.linkedin_search_url]
    if cookie and search_urls:
        scrapers.append(LinkedInScraper(browser=browser, cookie=cookie))
    return scrapers
```

Add `import json` to the imports at the top of `discovery.py`.

- [ ] **Step 4: Update `run_discovery` to loop through multiple URLs and set `auth_status`**

Replace the `run_discovery` function body. The key changes are:
1. Set `settings.linkedin_auth_status = "expired"` on `SessionExpiredError`
2. Loop through all `linkedin_search_urls` for the LinkedIn scraper

```python
async def run_discovery(db: Session) -> int:
    """Run all enabled scrapers, dedup jobs by URL, insert new ones, enqueue parse+score.

    Returns the number of new jobs inserted.
    """
    settings = _get_or_create_settings(db)
    if not settings.discovery_enabled:
        logger.info("Discovery is disabled")
        return 0

    browser = get_browser_service()
    scrapers = _get_enabled_scrapers(settings, browser)
    new_count = 0

    # Build the list of (scraper, params) pairs.
    # LinkedIn runs once per URL; other scrapers run once with their own params.
    scraper_runs: list[tuple] = []
    search_urls = json.loads(settings.linkedin_search_urls or "[]")
    if not search_urls and settings.linkedin_search_url:
        search_urls = [settings.linkedin_search_url]

    for scraper in scrapers:
        if scraper.source_name == "linkedin" and search_urls:
            for url in search_urls:
                scraper_runs.append((scraper, {"search_url": url}))
        else:
            scraper_runs.append((scraper, _build_params_for(scraper, settings)))

    for scraper, params in scraper_runs:
        try:
            raw_jobs = await scraper.scrape(params)
        except SessionExpiredError as e:
            logger.warning("LinkedIn session expired: %s", e)
            settings.linkedin_auth_status = "expired"
            db.commit()
            continue
        except Exception as e:
            logger.exception("Scraper %s failed: %s", scraper.source_name, e)
            continue

        for raw in raw_jobs:
            existing = db.query(Job).filter(Job.job_url == raw.url).first()
            if existing:
                continue
            job = Job(
                job_url=raw.url,
                role_title=raw.title,
                company_name=raw.company,
                job_description=raw.raw_text,
                source=raw.source,
                application_status="discovered",
                discovered_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            _enqueue_parse_and_score(job.id)
            new_count += 1

    settings.discovery_last_run_at = datetime.utcnow()
    settings.discovery_last_count = new_count
    db.commit()
    logger.info("Discovery complete: %d new jobs", new_count)
    return new_count
```

Also remove the old `_build_params_for` usage inside the loop (it's now only called for non-LinkedIn scrapers). Keep the `_build_params_for` function as-is for YC.

- [ ] **Step 5: Run tests**

```bash
cd backend && .venv/bin/pytest tests/test_discovery_workflow.py -v
```
Expected: PASS

- [ ] **Step 6: Run full backend test suite to catch regressions**

```bash
cd backend && .venv/bin/pytest tests/ -v --tb=short
```
Expected: all existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/workflows/discovery.py backend/tests/test_discovery_workflow.py
git commit -m "feat: set auth_status=expired on SessionExpiredError, loop through linkedin_search_urls"
```

---

## Task 7: Frontend API Client Additions

**Files:**
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: Add new types and functions to `frontend/lib/api.ts`**

Append the following to the end of `frontend/lib/api.ts`:

```typescript
// ----- Preferences -----
export interface JobPreferences {
  job_titles: string[];
  locations: string[];
  remote_preference: "any" | "remote" | "hybrid" | "onsite";
  seniority_levels: string[];
  company_stage: "any" | "startup" | "growth" | "public";
  min_salary: number | null;
  linkedin_auth_status: "disconnected" | "connected" | "expired";
  linkedin_search_urls: string[];
  linkedin_search_url: string | null;
}

export async function getPreferences(): Promise<JobPreferences> {
  const r = await fetch(`${API_BASE}/api/settings/preferences`);
  if (!r.ok) throw new Error("Failed to load preferences");
  return r.json();
}

export async function updatePreferences(
  patch: Partial<Omit<JobPreferences, "linkedin_auth_status" | "linkedin_search_urls" | "linkedin_search_url">>
): Promise<JobPreferences> {
  const r = await fetch(`${API_BASE}/api/settings/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!r.ok) throw new Error("Failed to update preferences");
  return r.json();
}

// ----- LinkedIn Auth -----
export async function startLinkedInAuth(): Promise<{ session_id: string }> {
  const r = await fetch(`${API_BASE}/api/settings/linkedin/start-auth`, {
    method: "POST",
  });
  if (!r.ok) throw new Error("Failed to start LinkedIn auth");
  return r.json();
}

export async function getLinkedInAuthStatus(
  sessionId: string
): Promise<{ status: "waiting" | "connected" | "timeout" }> {
  const r = await fetch(
    `${API_BASE}/api/settings/linkedin/auth-status/${sessionId}`
  );
  if (!r.ok) throw new Error("Failed to get auth status");
  return r.json();
}

export async function disconnectLinkedIn(): Promise<void> {
  const r = await fetch(`${API_BASE}/api/settings/linkedin/disconnect`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error("Failed to disconnect LinkedIn");
}
```

- [ ] **Step 2: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.ts
git commit -m "feat: add preferences and LinkedIn auth API client functions"
```

---

## Task 8: TagInput UI Component

**Files:**
- Create: `frontend/components/ui/tag-input.tsx`

- [ ] **Step 1: Create the TagInput component**

Create `frontend/components/ui/tag-input.tsx`:

```tsx
"use client";
import { useState, KeyboardEvent } from "react";

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  suggestions?: string[];
}

export function TagInput({
  tags,
  onChange,
  placeholder = "Type and press Enter...",
  suggestions = [],
}: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addTag = (value: string) => {
    const trimmed = value.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInputValue("");
  };

  const removeTag = (index: number) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(inputValue);
    } else if (e.key === "Backspace" && inputValue === "" && tags.length > 0) {
      removeTag(tags.length - 1);
    }
  };

  const filteredSuggestions = suggestions.filter(
    (s) =>
      inputValue.length > 0 &&
      s.toLowerCase().includes(inputValue.toLowerCase()) &&
      !tags.includes(s)
  );

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 min-h-[42px] focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
        {tags.map((tag, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(i)}
              className="text-blue-500 hover:text-blue-700 leading-none"
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => inputValue.trim() && addTag(inputValue)}
          placeholder={tags.length === 0 ? placeholder : ""}
          className="flex-1 min-w-[120px] outline-none text-sm bg-transparent"
        />
      </div>
      {filteredSuggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
          {filteredSuggestions.slice(0, 5).map((s) => (
            <li
              key={s}
              onClick={() => addTag(s)}
              className="cursor-pointer px-3 py-2 text-sm hover:bg-gray-100"
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/ui/tag-input.tsx
git commit -m "feat: add reusable TagInput component"
```

---

## Task 9: PreferencesStep Component (Step 1)

**Files:**
- Create: `frontend/components/setup/preferences-step.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/components/setup/preferences-step.tsx`:

```tsx
"use client";
import { useState } from "react";
import { TagInput } from "@/components/ui/tag-input";
import { JobPreferences, updatePreferences } from "@/lib/api";

const ROLE_SUGGESTIONS = [
  "Product Manager", "Senior PM", "Lead PM", "Head of Product",
  "Director of Product", "VP of Product", "Principal PM",
  "Software Engineer", "Senior Software Engineer", "Staff Engineer",
];

const SENIORITY_OPTIONS = ["Entry", "Mid", "Senior", "Lead", "Director+"];
const REMOTE_OPTIONS = [
  { value: "any", label: "Any" },
  { value: "remote", label: "Remote only" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
] as const;

interface PreferencesStepProps {
  initial: JobPreferences;
  onComplete: (prefs: JobPreferences) => void;
}

export function PreferencesStep({ initial, onComplete }: PreferencesStepProps) {
  const [jobTitles, setJobTitles] = useState<string[]>(initial.job_titles);
  const [locations, setLocations] = useState<string[]>(initial.locations);
  const [remotePreference, setRemotePreference] = useState(
    initial.remote_preference
  );
  const [seniorityLevels, setSeniorityLevels] = useState<string[]>(
    initial.seniority_levels
  );
  const [minSalary, setMinSalary] = useState<string>(
    initial.min_salary ? String(initial.min_salary) : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchPreview = () => {
    const parts: string[] = [];
    if (jobTitles.length > 0) parts.push(jobTitles.join(" / "));
    if (remotePreference !== "any") parts.push(remotePreference.charAt(0).toUpperCase() + remotePreference.slice(1));
    if (locations.length > 0) parts.push(locations.join(", "));
    if (seniorityLevels.length > 0) parts.push(seniorityLevels.join(", "));
    return parts.length > 0 ? parts.join(" · ") : "Add roles above to see preview";
  };

  const handleNext = async () => {
    if (jobTitles.length === 0) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updatePreferences({
        job_titles: jobTitles,
        locations,
        remote_preference: remotePreference,
        seniority_levels: seniorityLevels,
        min_salary: minSalary ? parseInt(minSalary, 10) : null,
      });
      onComplete(updated);
    } catch (e) {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">What are you looking for?</h2>
        <p className="mt-1 text-sm text-gray-500">
          Describe your ideal role — we'll build the search for you.
        </p>
      </div>

      {/* Job titles */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Job Titles / Roles
        </label>
        <TagInput
          tags={jobTitles}
          onChange={setJobTitles}
          placeholder="e.g. Product Manager (press Enter to add)"
          suggestions={ROLE_SUGGESTIONS}
        />
        {jobTitles.length === 0 && (
          <p className="text-xs text-red-500">Add at least one role to continue</p>
        )}
      </div>

      {/* Location + remote */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Locations</label>
          <TagInput
            tags={locations}
            onChange={setLocations}
            placeholder="e.g. United States"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">
            Work Arrangement
          </label>
          <div className="space-y-1.5">
            {REMOTE_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className="flex cursor-pointer items-center gap-2 text-sm"
              >
                <input
                  type="radio"
                  name="remote"
                  value={opt.value}
                  checked={remotePreference === opt.value}
                  onChange={() => setRemotePreference(opt.value)}
                  className="h-3.5 w-3.5 text-blue-600"
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Seniority */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Seniority Level
        </label>
        <div className="flex flex-wrap gap-2">
          {SENIORITY_OPTIONS.map((level) => {
            const active = seniorityLevels.includes(level);
            return (
              <button
                key={level}
                type="button"
                onClick={() =>
                  setSeniorityLevels(
                    active
                      ? seniorityLevels.filter((l) => l !== level)
                      : [...seniorityLevels, level]
                  )
                }
                className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "border-blue-500 bg-blue-100 text-blue-800"
                    : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {level}
              </button>
            );
          })}
        </div>
      </div>

      {/* Min salary */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Minimum Salary{" "}
          <span className="font-normal text-gray-400">(optional)</span>
        </label>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">$</span>
          <input
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="e.g. 130000"
            className="w-40 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-500">/ year</span>
        </div>
      </div>

      {/* Search preview */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
          🔍 Search Preview
        </p>
        <p className="mt-1 text-sm italic text-blue-800">{searchPreview()}</p>
        <p className="mt-1 text-xs text-blue-500">
          LinkedIn search URL will be constructed automatically
        </p>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={jobTitles.length === 0 || saving}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? "Saving…" : "Next: Connect LinkedIn →"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/setup/preferences-step.tsx
git commit -m "feat: add PreferencesStep component (wizard step 1)"
```

---

## Task 10: LinkedInAuthStep Component (Step 2)

**Files:**
- Create: `frontend/components/setup/linkedin-auth-step.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/components/setup/linkedin-auth-step.tsx`:

```tsx
"use client";
import { useState, useEffect, useRef } from "react";
import { startLinkedInAuth, getLinkedInAuthStatus } from "@/lib/api";

type AuthStatus = "idle" | "waiting" | "connected" | "timeout" | "error";

interface LinkedInAuthStepProps {
  onComplete: () => void;
}

export function LinkedInAuthStep({ onComplete }: LinkedInAuthStepProps) {
  const [status, setStatus] = useState<AuthStatus>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    return () => clearPolling(); // cleanup on unmount
  }, []);

  useEffect(() => {
    if (!sessionId || status !== "waiting") return;

    intervalRef.current = setInterval(async () => {
      try {
        const result = await getLinkedInAuthStatus(sessionId);
        if (result.status !== "waiting") {
          clearPolling();
          setStatus(result.status as AuthStatus);
          if (result.status === "connected") {
            // Small delay so user sees the success state before advancing
            setTimeout(onComplete, 1500);
          }
        }
      } catch {
        clearPolling();
        setStatus("error");
      }
    }, 2000);

    return () => clearPolling();
  }, [sessionId, status, onComplete]);

  const handleStartAuth = async () => {
    setStatus("waiting");
    try {
      const { session_id } = await startLinkedInAuth();
      setSessionId(session_id);
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Connect LinkedIn</h2>
        <p className="mt-1 text-sm text-gray-500">
          We need access to LinkedIn to find matching jobs.
        </p>
      </div>

      <div className="flex flex-col items-center gap-6 rounded-xl border border-gray-200 bg-gray-50 py-10 px-8 text-center">
        {/* LinkedIn logo */}
        <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-[#0077b5] text-2xl font-bold text-white">
          in
        </div>

        {status === "idle" && (
          <>
            <div>
              <p className="font-medium text-gray-800">Log into LinkedIn</p>
              <p className="mt-1 text-sm text-gray-500">
                A browser window will open. Log in normally — the app captures
                your session automatically.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-[#0077b5] px-6 py-3 text-sm font-semibold text-white hover:bg-[#005f8f] transition-colors"
            >
              🔗 Open LinkedIn Login Window
            </button>
            <p className="text-xs text-gray-400">
              Works with 2FA · CAPTCHA · SSO · No passwords stored
            </p>
          </>
        )}

        {status === "waiting" && (
          <>
            <div>
              <p className="font-medium text-gray-800">
                Waiting for login…
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Complete login in the Chromium window, then come back here.
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-amber-400" />
              Watching for LinkedIn session…
            </div>
            <p className="text-xs text-gray-400">
              Window will close automatically when done (5-minute timeout)
            </p>
          </>
        )}

        {status === "connected" && (
          <>
            <div className="flex items-center gap-2 text-green-600">
              <span className="text-2xl">✅</span>
              <span className="font-semibold">LinkedIn Connected!</span>
            </div>
            <p className="text-sm text-gray-500">
              Session captured successfully. Moving to next step…
            </p>
          </>
        )}

        {status === "timeout" && (
          <>
            <div className="text-amber-600">
              <p className="font-medium">Login window timed out</p>
              <p className="mt-1 text-sm text-gray-500">
                The 5-minute window expired. Please try again.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-[#0077b5] px-6 py-3 text-sm font-semibold text-white hover:bg-[#005f8f]"
            >
              🔗 Try Again
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <div className="text-red-600">
              <p className="font-medium">Something went wrong</p>
              <p className="mt-1 text-sm text-gray-500">
                The backend may not be running. Check the backend logs.
              </p>
            </div>
            <button
              onClick={handleStartAuth}
              className="rounded-lg bg-gray-700 px-6 py-3 text-sm font-semibold text-white hover:bg-gray-800"
            >
              Retry
            </button>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/setup/linkedin-auth-step.tsx
git commit -m "feat: add LinkedInAuthStep component (wizard step 2)"
```

---

## Task 11: ReadyStep Component (Step 3)

**Files:**
- Create: `frontend/components/setup/ready-step.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/components/setup/ready-step.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { runDiscoveryNow } from "@/lib/api";

interface ReadyStepProps {
  searchPreview: string;
}

export function ReadyStep({ searchPreview }: ReadyStepProps) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handleRunNow = async () => {
    setRunning(true);
    try {
      await runDiscoveryNow();
      setMsg("Discovery started! Redirecting to jobs…");
      setTimeout(() => router.push("/jobs"), 2000);
    } catch {
      setMsg("Failed to start discovery. You can trigger it from Settings.");
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="text-5xl">🎉</div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            JobFlow is ready to find jobs!
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Your preferences and LinkedIn session are saved.
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">LinkedIn</span>
          <span className="font-medium text-green-600">✅ Connected</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Searching for</span>
          <span className="font-medium text-gray-800 text-right max-w-[240px] truncate">
            {searchPreview}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Auto-discovery</span>
          <span className="font-medium text-gray-800">Every 6 hours</span>
        </div>
      </div>

      {msg && (
        <p className="text-center text-sm text-green-600">{msg}</p>
      )}

      <div className="flex flex-col gap-3">
        <button
          onClick={handleRunNow}
          disabled={running}
          className="w-full rounded-lg bg-green-600 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
        >
          {running ? "Starting…" : "▶ Run Discovery Now"}
        </button>
        <button
          onClick={() => router.push("/settings")}
          className="w-full rounded-lg border border-gray-300 bg-white py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          View Settings
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/setup/ready-step.tsx
git commit -m "feat: add ReadyStep component (wizard step 3)"
```

---

## Task 12: Setup Wizard Page `/setup`

**Files:**
- Create: `frontend/app/setup/page.tsx`

- [ ] **Step 1: Create the page**

Create `frontend/app/setup/page.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getPreferences, JobPreferences } from "@/lib/api";
import { PreferencesStep } from "@/components/setup/preferences-step";
import { LinkedInAuthStep } from "@/components/setup/linkedin-auth-step";
import { ReadyStep } from "@/components/setup/ready-step";

const STEP_LABELS = ["Job Preferences", "Connect LinkedIn", "Ready"];

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0 mb-10">
      {STEP_LABELS.map((label, i) => {
        const stepNum = i + 1;
        const done = stepNum < current;
        const active = stepNum === current;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div className="flex items-center gap-2 shrink-0">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold ${
                  done
                    ? "bg-green-500 text-white"
                    : active
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {done ? "✓" : stepNum}
              </div>
              <span
                className={`text-sm font-medium ${
                  active ? "text-blue-600" : done ? "text-green-600" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEP_LABELS.length - 1 && (
              <div
                className={`mx-3 h-0.5 flex-1 ${
                  done ? "bg-green-400" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function SetupPage() {
  const searchParams = useSearchParams();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [prefs, setPrefs] = useState<JobPreferences | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPreferences()
      .then((p) => {
        setPrefs(p);
        // Honor ?step=2 param (for re-auth flow from expired session)
        const stepParam = searchParams.get("step");
        if (stepParam === "2") setStep(2);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchParams]);

  const searchPreview = () => {
    if (!prefs) return "";
    const parts: string[] = [];
    if (prefs.job_titles.length > 0) parts.push(prefs.job_titles.join(" / "));
    if (prefs.remote_preference !== "any") parts.push(prefs.remote_preference);
    if (prefs.locations.length > 0) parts.push(prefs.locations[0]);
    return parts.join(" · ");
  };

  if (loading || !prefs) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-start justify-center py-16 px-4">
      <div className="w-full max-w-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">JobFlow AI</h1>
          <p className="mt-2 text-gray-500">Let's set up your job search</p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <StepIndicator current={step} />

          {step === 1 && (
            <PreferencesStep
              initial={prefs}
              onComplete={(updated) => {
                setPrefs(updated);
                setStep(2);
              }}
            />
          )}

          {step === 2 && (
            <LinkedInAuthStep onComplete={() => setStep(3)} />
          )}

          {step === 3 && <ReadyStep searchPreview={searchPreview()} />}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Start dev server and manually verify the wizard**

```bash
cd frontend && npm run dev
```
Open `http://localhost:3000/setup` in a browser. Verify:
- Step 1 form renders with all fields
- "Next" button disabled until a role is added
- Adding a tag and clicking "Next" saves + advances to Step 2
- Step 2 shows the LinkedIn login button
- `http://localhost:3000/setup?step=2` jumps directly to Step 2

- [ ] **Step 4: Commit**

```bash
git add frontend/app/setup/
git commit -m "feat: add /setup wizard page (3-step job discovery onboarding)"
```

---

## Task 13: Settings Page — LinkedIn Summary Card

**Files:**
- Modify: `frontend/app/settings/page.tsx`

- [ ] **Step 1: Read the current settings page**

Read `frontend/app/settings/page.tsx` in full to understand the current structure before editing.

- [ ] **Step 2: Replace the LinkedIn section**

In `frontend/app/settings/page.tsx`:

1. Add these imports at the top:
```tsx
import Link from "next/link";
import { getPreferences, JobPreferences, disconnectLinkedIn } from "@/lib/api";
```

2. Add a `prefs` state variable inside the component:
```tsx
const [prefs, setPrefs] = useState<JobPreferences | null>(null);
```

3. Load preferences in the `useEffect`:
```tsx
useEffect(() => {
  getSettings().then(setS).catch(console.error);
  getPreferences().then(setPrefs).catch(console.error);
}, []);
```

4. Replace the entire `LinkedInCookieInput` + URL input `<div>` block (the two child elements inside the `<section>` that currently render the cookie input and search URL input) with this `LinkedInCard` inline component placed just above the `return`:

```tsx
function LinkedInCard({
  prefs,
  onDisconnect,
}: {
  prefs: JobPreferences;
  onDisconnect: () => void;
}) {
  const searchSummary = [
    ...prefs.job_titles.slice(0, 2),
    prefs.remote_preference !== "any" ? prefs.remote_preference : null,
    prefs.locations[0] ?? null,
  ]
    .filter(Boolean)
    .join(" · ");

  const handleDisconnect = async () => {
    await disconnectLinkedIn();
    onDisconnect();
  };

  if (prefs.linkedin_auth_status === "disconnected") {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-4 text-sm text-gray-500">
        <p className="font-medium text-gray-700">LinkedIn not connected</p>
        <p className="mt-1">Set up LinkedIn discovery to start finding jobs automatically.</p>
        <Link
          href="/setup"
          className="mt-3 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Set Up LinkedIn →
        </Link>
      </div>
    );
  }

  if (prefs.linkedin_auth_status === "expired") {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
        <p className="font-semibold text-amber-800">⚠️ Session expired — discovery is paused</p>
        {searchSummary && (
          <p className="mt-1 text-amber-700">Searching for: {searchSummary}</p>
        )}
        <Link
          href="/setup?step=2"
          className="mt-3 inline-block rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
        >
          Reconnect →
        </Link>
      </div>
    );
  }

  // Connected
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-700">LinkedIn Discovery</span>
        <span className="text-green-600 font-medium">✅ Connected</span>
      </div>
      {searchSummary && (
        <p className="mt-2 text-gray-500">Searching for: {searchSummary}</p>
      )}
      <div className="mt-3 flex gap-2">
        <Link
          href="/setup"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Edit Preferences
        </Link>
        <Link
          href="/setup?step=2"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Reconnect
        </Link>
        <button
          onClick={handleDisconnect}
          className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
}
```

5. In the JSX, replace the `<LinkedInCookieInput ... />` and the URL `<div>` with:
```tsx
{prefs ? (
  <LinkedInCard
    prefs={prefs}
    onDisconnect={() =>
      setPrefs((p) => p ? { ...p, linkedin_auth_status: "disconnected", linkedin_cookie_present: false } : p)
    }
  />
) : (
  <p className="text-sm text-gray-400">Loading…</p>
)}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 4: Visually verify in browser**

Open `http://localhost:3000/settings`. Verify:
- If not connected: shows "Set Up LinkedIn →" link
- If connected (after going through setup): shows summary card with "Edit Preferences" and "Reconnect" buttons
- Old cookie input and URL field are gone

- [ ] **Step 5: Commit**

```bash
git add frontend/app/settings/page.tsx
git commit -m "feat: replace LinkedIn cookie/URL inputs with smart summary card in settings"
```

---

## Task 14: Sidebar Auto-redirect

**Files:**
- Modify: `frontend/components/layout/sidebar.tsx`

- [ ] **Step 1: Add auto-redirect and expired-session banner to sidebar**

In `frontend/components/layout/sidebar.tsx`, replace the full file content with:

```tsx
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { getPreferences, JobPreferences } from "@/lib/api";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/profile", label: "Profile", icon: "👤" },
  { href: "/jobs", label: "Jobs", icon: "💼" },
  { href: "/outreach", label: "Outreach", icon: "📨" },
  { href: "/crm", label: "CRM", icon: "📋" },
  { href: "/interviews", label: "Interviews", icon: "🎯" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

// Pages that should never trigger the setup redirect
const SETUP_EXEMPT = ["/setup", "/profile/ingest"];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [prefs, setPrefs] = useState<JobPreferences | null>(null);

  useEffect(() => {
    getPreferences()
      .then((p) => {
        setPrefs(p);
        // Redirect to setup if preferences not configured yet
        if (
          p.job_titles.length === 0 &&
          !SETUP_EXEMPT.some((exempt) => pathname.startsWith(exempt))
        ) {
          router.push("/setup");
        }
      })
      .catch(() => {
        // Backend not ready yet — fail silently
      });
  }, [pathname, router]);

  const sessionExpired = prefs?.linkedin_auth_status === "expired";

  return (
    <aside className="w-64 border-r bg-gray-50 min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold">JobFlow AI</h1>
        <p className="text-sm text-gray-500">Job Search Agent</p>
      </div>
      <nav className="space-y-1 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium",
              pathname === item.href
                ? "bg-gray-900 text-white"
                : "text-gray-700 hover:bg-gray-200"
            )}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Persistent amber banner when LinkedIn session expired */}
      {sessionExpired && (
        <Link
          href="/setup?step=2"
          className="mt-4 block rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700 hover:bg-amber-100"
        >
          ⚠️ LinkedIn session expired —{" "}
          <span className="font-semibold underline">Reconnect →</span>
        </Link>
      )}

      <div className="mt-4 pt-4 border-t">
        <Link
          href="/profile/ingest"
          className="block w-full text-center bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-md px-3 py-2 hover:opacity-90"
        >
          ✨ Ingest Profile
        </Link>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 3: Test auto-redirect behavior**

Open `http://localhost:3000/jobs` in a browser on a fresh DB (no preferences set). Verify:
- Browser redirects to `http://localhost:3000/setup`
- After completing setup, navigating to `/jobs` no longer redirects

Also verify that visiting `/setup` directly does NOT cause an infinite redirect loop.

- [ ] **Step 4: Run full backend test suite one final time**

```bash
cd backend && .venv/bin/pytest tests/ -v --tb=short
```
Expected: all tests PASS

- [ ] **Step 5: Final commit and push**

```bash
git add frontend/components/layout/sidebar.tsx
git commit -m "feat: auto-redirect to /setup wizard when job preferences not configured"
git push origin main
```

---

## Deferred: Active 401 Modal

The spec describes a modal that appears when the user manually triggers "Run Discovery Now" with an expired session (backend returns `401 {"detail": "linkedin_session_expired"}`). This is **not in this plan** — the passive expired-session banner in the sidebar covers the same user need with less complexity. The 401 modal can be added as a follow-up if the passive banner proves insufficient.

---

## Summary

| Task | What it builds |
|------|---------------|
| 1 | DB migration — 8 new columns on `UserSettings` |
| 2 | `linkedin_url_builder.py` — preferences → LinkedIn search URLs |
| 3 | `GET/PUT /api/settings/preferences` endpoints |
| 4 | `open_login_window()` in browser.py — visible Playwright auth |
| 5 | `POST/GET/DELETE /api/settings/linkedin/*` endpoints |
| 6 | Discovery workflow — `auth_status=expired` + multi-URL loop |
| 7 | Frontend API client additions |
| 8 | `TagInput` reusable component |
| 9 | `PreferencesStep` — wizard step 1 |
| 10 | `LinkedInAuthStep` — wizard step 2 with polling |
| 11 | `ReadyStep` — wizard step 3 |
| 12 | `/setup` page — 3-step orchestrator |
| 13 | Settings page LinkedIn summary card |
| 14 | Sidebar auto-redirect |
