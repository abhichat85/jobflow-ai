# Job Discovery & Auto-Apply Pipeline — Design Spec

**Goal:** Autonomously discover relevant jobs from LinkedIn and YC, score them against the user's profile, surface high-scoring ones for review, and submit applications (with tailored resume + cover letter) on the user's behalf via browser automation.

**Architecture:** Three phased subsystems — Discovery, Pipeline, Auto-Apply — sharing a common job state machine. Each subsystem is independently extensible: new job boards plug in via `BaseJobScraper`, new ATS form fillers via `BaseFormFiller`.

**Tech Stack:** Playwright (scraping + form filling), Celery beat (scheduling), httpx + BeautifulSoup (YC), existing Claude agents (JobParserAgent, JobScorerAgent, ResumeTailorAgent, CoverLetterAgent), SQLite via SQLAlchemy.

---

## 1. Job State Machine

Every job moves through a single state machine. All subsystems read from and write to this state.

```
discovered → parsed → scored → pending_review → approved → applying → applied
                                    │                                 → failed
                                    └──────────────────────────────→ skipped
```

- `discovered` — raw job saved from scraper, not yet parsed
- `parsed` — JobParserAgent has extracted structured requirements
- `scored` — JobScorerAgent has produced a fit score
- `pending_review` — score ≥ threshold; waiting for user approval
- `skipped` — score < threshold; hidden by default in UI
- `approved` — user reviewed and approved the pre-filled application
- `applying` — Playwright is actively submitting the form (in-progress)
- `applied` — form submitted successfully; triggers outreach workflow
- `failed` — Playwright hit an unrecoverable error (CAPTCHA, unknown layout); user notified to apply manually

---

## 2. Data Model Changes

### `Job` model — new fields

```python
apply_url: Optional[str]        # The actual "Apply" button URL (may differ from job_url)
ats_type: Optional[str]         # "greenhouse" | "lever" | "ashby" | "unknown"
application_status: str         # Full state machine value (replaces/extends status)
```

ATS type is detected automatically during parsing: inspect `apply_url` for `greenhouse.io`, `lever.co`, `ashbyHQ.com` substrings.

### New: `UserSettings` table

```python
class UserSettings(Base):
    __tablename__ = "user_settings"

    id: int (PK)

    # Discovery
    linkedin_cookie: Optional[str]       # li_at cookie value (encrypted)
    linkedin_search_url: Optional[str]   # LinkedIn Jobs saved search URL
    yc_filters: Optional[dict]           # {"roles": ["Product","AI"], "remote": true}
    discovery_enabled: bool = True
    discovery_interval_hours: int = 6
    discovery_last_run_at: Optional[datetime]
    discovery_last_count: Optional[int]

    # Scoring
    auto_review_threshold: int = 65      # Score ≥ this → pending_review
    auto_apply_threshold: int = 80       # Reserved for Phase 2 (semi-auto)
    daily_apply_cap: int = 10            # Reserved for Phase 2

    # Apply
    default_resume_variant: Optional[str]   # e.g. "ai_pm"
    cover_letter_tone: str = "professional" # "professional" | "conversational" | "direct"

    created_at: datetime
    updated_at: datetime
```

### New: `ApplicationAttempt` table

```python
class ApplicationAttempt(Base):
    __tablename__ = "application_attempts"

    id: int (PK)
    job_id: int (FK → jobs.id)
    status: str              # "success" | "failed" | "in_progress"
    resume_variant: str      # Which variant was used
    cover_letter_text: str   # The cover letter that was submitted
    form_data: dict          # All field values that were filled (JSON)
    confirmation_text: Optional[str]
    screenshot_path: Optional[str]
    error_message: Optional[str]
    attempted_at: datetime
```

---

## 3. Phase 1 — Job Discovery

### Scraper Architecture

**Location:** `backend/app/scrapers/`

```
BaseJobScraper (abstract)          backend/app/scrapers/base.py
├── LinkedInScraper                backend/app/scrapers/linkedin.py
└── YCScraper                      backend/app/scrapers/yc.py
```

**`BaseJobScraper` interface:**

```python
@dataclass
class RawJob:
    url: str
    title: str
    company: str
    raw_text: str
    source: str  # "linkedin" | "yc"

class BaseJobScraper(ABC):
    @abstractmethod
    async def scrape(self, params: dict) -> list[RawJob]: ...

    @abstractmethod
    async def is_healthy(self) -> bool: ...
    # Quick check — LinkedIn: can we load a page with the cookie?
    # YC: can we reach workatastartup.com?
```

**LinkedInScraper:**
- Playwright headless Chromium with `li_at` cookie injected
- Navigates to `UserSettings.linkedin_search_url`
- Scrolls and extracts job cards: title, company, location, job URL
- For each card, opens the job detail pane and extracts full description text
- Rate limits to 1 request/2s to avoid triggering LinkedIn's bot detection
- On HTTP 401 or redirect to login: raises `SessionExpiredError` → sets `discovery_enabled=False`, notifies user in UI

**YCScraper:**
- Plain `httpx.AsyncClient` — no Playwright needed
- Scrapes `https://www.workatastartup.com/jobs` with role/remote filters from `UserSettings.yc_filters`
- Parses with BeautifulSoup; extracts job URL, title, company, description

**Deduplication:**
- Before inserting any job, check `jobs.job_url` for exact match
- If already exists: skip (never update an existing job's status from discovery)

### Discovery Workflow

**Location:** `backend/app/workflows/discovery.py`

```python
async def run_discovery(db: Session):
    settings = get_user_settings(db)
    scrapers = get_enabled_scrapers(settings)  # LinkedIn if cookie set, YC always

    new_count = 0
    for scraper in scrapers:
        raw_jobs = await scraper.scrape(settings)
        for raw in raw_jobs:
            if job_url_exists(db, raw.url):
                continue
            job = Job(job_url=raw.url, role_title=raw.title,
                      company_name=raw.company, job_description=raw.raw_text,
                      source=raw.source, application_status="discovered",
                      discovered_at=datetime.utcnow())
            db.add(job)
            db.commit()
            parse_and_score_job.delay(job.id)  # Celery task
            new_count += 1

    settings.discovery_last_run_at = datetime.utcnow()
    settings.discovery_last_count = new_count
    db.commit()
    return new_count
```

### Celery Scheduling

**`backend/celery_worker.py`** — add beat schedule:

```python
app.conf.beat_schedule = {
    "discover-jobs": {
        "task": "app.tasks.discover_jobs",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
}
```

### API Routes

**`POST /api/discovery/run`** — Triggers `run_discovery` immediately, returns `{"status": "started", "task_id": "..."}`.

**`GET /api/discovery/status`** — Returns `{ last_run_at, last_count, enabled, next_run_at }`.

---

## 4. Phase 2 — Parse + Score Pipeline

### Celery Task: `parse_and_score_job(job_id)`

This wires together the two already-built agents into a background task.

```python
@celery_app.task
async def parse_and_score_job(job_id: int):
    db = SessionLocal()
    job = db.query(Job).get(job_id)
    profile = db.query(UserProfile).first()
    settings = get_user_settings(db)

    # Step 1: Parse
    claude = ClaudeService()
    parsed = await JobParserAgent(claude).run(
        JobParseInput(raw_text=job.job_description, source_url=job.job_url),
        JobParseOutput
    )
    # Detect ATS type
    apply_url = parsed.apply_url or job.job_url
    ats_type = detect_ats(apply_url)

    # Save requirements + update job
    db.add(JobRequirement(job_id=job.id, ...))
    job.apply_url = apply_url
    job.ats_type = ats_type
    job.application_status = "parsed"
    db.commit()

    # Step 2: Score
    scored = await JobScorerAgent(claude).run(
        JobScoreInput(...profile fields..., ...parsed fields...),
        JobScoreOutput
    )
    db.add(JobScore(job_id=job.id, ...scored fields...))
    job.fit_score = scored.total_score
    job.application_status = "scored"
    db.commit()

    # Step 3: Route
    if scored.total_score >= settings.auto_review_threshold:
        job.application_status = "pending_review"
    else:
        job.application_status = "skipped"
    db.commit()
```

**ATS detection** — `detect_ats(url: str) -> str`:
```python
if "greenhouse.io" in url: return "greenhouse"
if "lever.co" in url: return "lever"
if "ashbyhq.com" in url or "ashby.io" in url: return "ashby"
return "unknown"
```

---

## 5. Phase 3 — Auto-Apply (Human-in-the-Loop)

### Review UI Flow

1. User opens `/jobs` — sees jobs with score badges, filter by status
2. Clicks **"Review"** on a `pending_review` job → opens `/jobs/{id}/review`
3. Review page triggers:
   - `ResumeTailorAgent` — tailors resume for this specific job (uses `resume_angle` from scorer)
   - `CoverLetterAgent` — generates cover letter
   - Pre-fills all known form fields from profile
4. User sees: job summary, score breakdown, tailored resume preview, cover letter (editable), form fields table (editable)
5. User edits anything needed, clicks **"Approve & Submit"**
6. `POST /api/apply/{job_id}` — enqueues `submit_application` Celery task, job → `approved`
7. UI polls `GET /api/apply/{job_id}/status` — shows progress indicator
8. On success: job → `applied`, shows confirmation screenshot
9. On failure: job → `failed`, shows error + screenshot, "Apply Manually" link

### Form Filler Architecture

**Location:** `backend/app/form_fillers/`

```
BaseFormFiller (abstract)         backend/app/form_fillers/base.py
├── GreenhouseFormFiller           backend/app/form_fillers/greenhouse.py
├── LeverFormFiller                backend/app/form_fillers/lever.py
└── AshbyFormFiller                backend/app/form_fillers/ashby.py
```

**`BaseFormFiller` interface:**

```python
@dataclass
class ApplicationData:
    name: str
    email: str
    phone: str
    linkedin_url: str
    resume_pdf_path: str
    cover_letter_text: str
    custom_answers: dict[str, str]  # question_text → answer

@dataclass
class ApplyResult:
    success: bool
    confirmation_text: Optional[str]
    screenshot_path: Optional[str]
    error_message: Optional[str]

class BaseFormFiller(ABC):
    def __init__(self, browser: BrowserService): ...

    @abstractmethod
    async def fill(self, apply_url: str, data: ApplicationData) -> ApplyResult: ...
```

**Each concrete filler:**
- Navigates to `apply_url` using shared `BrowserService` Playwright instance
- Fills fields by CSS selectors (stable across ATS versions; e.g. Greenhouse uses `#first_name`, `#last_name`, `#email`)
- Uploads resume via `input[type=file]`
- Handles custom screening questions: extract question text → `ClaudeService.generate_text(profile + question → answer)`
- Screenshots final confirmation page
- Returns `ApplyResult`

**`BrowserService`** — `backend/app/services/browser.py`:
- Singleton Playwright browser instance (launched once, reused)
- Provides `async def new_page() -> Page` with LinkedIn cookie pre-injected when needed
- Handles browser crash/restart gracefully

**`submit_application` Celery task:**

```python
@celery_app.task
async def submit_application(job_id: int, application_data: dict):
    job = db.query(Job).get(job_id)
    job.application_status = "applying"
    db.commit()

    filler = get_form_filler(job.ats_type)  # factory function
    result = await filler.fill(job.apply_url, ApplicationData(**application_data))

    attempt = ApplicationAttempt(job_id=job.id, **result.__dict__)
    db.add(attempt)
    job.application_status = "applied" if result.success else "failed"
    db.commit()

    if result.success:
        find_and_trigger_outreach.delay(job_id)  # auto-trigger outreach pipeline
```

### API Routes — `backend/app/routes/apply.py`

```
GET  /api/apply/{job_id}/preview   — Run tailor+cover letter, return pre-filled form data
POST /api/apply/{job_id}           — Approve + enqueue submission (body: edited form data)
GET  /api/apply/{job_id}/status    — Poll task status
POST /api/apply/{job_id}/skip      — Mark as skipped without applying
```

---

## 6. Settings

### `GET/PUT /api/settings` routes

Full CRUD for `UserSettings`. `PUT` is partial (only fields sent are updated).

### Settings page — `/settings`

Three sections:

**Discovery**
- LinkedIn cookie input (`li_at` value) with "Test Connection" button
- LinkedIn search URL input
- YC role filters (multi-select: Product, Engineering, AI, Design, etc.)
- Remote preference toggle
- Discovery enabled toggle
- Last run info: "Last run 2h ago — 14 new jobs found"

**Scoring**
- Review threshold slider (50–90, default 65)
- Auto-apply threshold slider (50–90, default 80) — labelled "(Phase 2)"

**Apply**
- Default resume variant selector
- Cover letter tone selector

---

## 7. File Structure

### New backend files

```
backend/app/scrapers/
  base.py              # BaseJobScraper, RawJob dataclass
  linkedin.py          # LinkedInScraper (Playwright + li_at)
  yc.py                # YCScraper (httpx + BeautifulSoup)

backend/app/form_fillers/
  base.py              # BaseFormFiller, ApplicationData, ApplyResult
  greenhouse.py        # GreenhouseFormFiller
  lever.py             # LeverFormFiller
  ashby.py             # AshbyFormFiller

backend/app/services/
  browser.py           # BrowserService — Playwright singleton

backend/app/workflows/
  discovery.py         # run_discovery() orchestrator
  apply.py             # prepare_application() — tailor + cover letter + form preview

backend/app/models/
  settings.py          # UserSettings model (new)
  application.py       # ApplicationAttempt model (new)

backend/app/routes/
  discovery.py         # Implement run + status (currently stubbed)
  apply.py             # Preview, approve, status, skip (new)
  settings.py          # GET/PUT /api/settings (new)
```

### Modified backend files

```
backend/app/models/job.py        # Add apply_url, ats_type, application_status fields
backend/app/tasks.py             # Add discover_jobs, parse_and_score_job, submit_application
backend/celery_worker.py         # Add beat schedule
backend/requirements.txt         # Add: playwright, playwright-stealth
backend/app/main.py              # Register new routers
```

### New frontend files

```
frontend/app/jobs/[id]/review/   # Review & approve page
frontend/app/settings/           # Settings page
frontend/components/jobs/        # ScoreBadge, StatusPill, ReviewQueue
frontend/components/settings/    # LinkedInCookieInput, ThresholdSlider
```

### Modified frontend files

```
frontend/app/jobs/page.tsx       # Add score badges, status column, Review button, filter bar
frontend/components/layout/sidebar.tsx   # Add Settings link
frontend/lib/api.ts              # Add discovery, apply, settings API calls
```

---

## 8. Implementation Phases

**Phase 1 — Discovery (build first, standalone value)**
- `UserSettings` model + migration
- `YCScraper` (no auth, easiest)
- `LinkedInScraper` (Playwright + cookie)
- `run_discovery` workflow + Celery task + beat schedule
- `POST /api/discovery/run` + `GET /api/discovery/status`
- Settings page (Discovery section only)
- Jobs page: show newly discovered jobs with source badge

**Phase 2 — Parse + Score Pipeline**
- `parse_and_score_job` Celery task (wires existing agents)
- `Job` model migration (add new fields)
- Jobs page: score badges, status filter, pending_review count in sidebar

**Phase 3 — Auto-Apply**
- `BrowserService`
- `ApplicationAttempt` model + migration
- `GreenhouseFormFiller`, `LeverFormFiller`, `AshbyFormFiller`
- `prepare_application` workflow (tailor + cover letter + form preview)
- `submit_application` Celery task
- `/api/apply/*` routes
- Review page UI
- Settings page: Apply section

---

## 9. Key Constraints & Decisions

- **LinkedIn cookie lifetime:** `li_at` lasts 2–4 weeks. App must surface a clear "session expired" warning and guide user to refresh it. Never auto-logout the user's real browser session.
- **Playwright install:** `playwright install chromium` must run once after `pip install playwright`. Add to `deploy.sh`.
- **No parallel Playwright sessions for apply:** Only one `submit_application` task runs at a time (Celery concurrency=1 for the apply queue) to prevent race conditions on the browser instance.
- **Resume PDF:** Generated by the existing `PDFGeneratorService` before form filling. Stored at `data/assets/{job_id}_resume.pdf`.
- **Custom screening questions:** Claude generates answers from profile + question text. Answers shown in review UI for editing before submission.
- **Failure is loud:** Any Playwright error → screenshot + `failed` status + visible notification. No silent failures.
- **Phase 2 fields stored now:** `auto_apply_threshold` and `daily_apply_cap` in `UserSettings` are stored in Phase 1 but unused until Phase 2, keeping the migration clean.
