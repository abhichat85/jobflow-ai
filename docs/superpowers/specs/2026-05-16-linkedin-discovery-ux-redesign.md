# LinkedIn Discovery UX Redesign

**Date:** 2026-05-16  
**Status:** Approved  
**Scope:** Replace the technical cookie+URL setup flow with a natural-language wizard

---

## Problem

The current LinkedIn discovery setup requires users to:
1. Extract the `li_at` cookie from browser DevTools
2. Manually construct a LinkedIn Jobs search URL with filters applied

This is technically intimidating, error-prone, and completely disconnected from what users care about: "find me Senior PM roles, remote, US." Non-technical users give up. Cookie expiry fails silently with no recovery path.

---

## Solution Overview

A 3-step guided setup wizard at `/setup` replaces the raw cookie/URL inputs:

1. **Step 1 — Job Preferences:** User describes what they want (roles, location, remote preference, seniority, company stage, salary). A live preview shows the constructed search query.
2. **Step 2 — Connect LinkedIn:** One button spawns a visible Playwright Chromium window. User logs in normally. App captures the `li_at` cookie automatically. Window closes.
3. **Step 3 — Ready:** Confirmation screen showing match count, auto-discovery schedule, and "Run Discovery Now" CTA.

The existing discovery pipeline (scraper → parse/score → review queue) is unchanged downstream.

---

## Architecture

### New Components

| Layer | Component | Purpose |
|-------|-----------|---------|
| Service | `linkedin_url_builder.py` | Translate structured preferences → LinkedIn search URLs |
| Service | `browser.py` (extended) | `open_login_window()` — non-headless Playwright auth capture |
| Routes | `settings.py` (extended) | Preferences CRUD + LinkedIn auth endpoints |
| Page | `frontend/app/setup/page.tsx` | 3-step wizard |
| Component | `preferences-step.tsx` | Step 1 form |
| Component | `linkedin-auth-step.tsx` | Step 2 auth with polling |
| Component | `ready-step.tsx` | Step 3 success state |
| Component | `tag-input.tsx` | Reusable multi-tag input |

### Auto-redirect Logic

On sidebar mount: if `GET /api/settings/preferences` returns empty `job_titles`, redirect to `/setup`. This ensures first-time users are always guided through setup before hitting the jobs page.

---

## Data Model

**Migration:** Add columns to existing `UserSettings` table (no new table).

```python
job_titles: str = "[]"           # JSON list — e.g. ["Product Manager", "Senior PM"]
locations: str = "[]"            # JSON list — e.g. ["United States"]
remote_preference: str = "any"   # "any" | "remote" | "hybrid" | "onsite"
seniority_levels: str = "[]"     # JSON list — e.g. ["Senior", "Lead"]
company_stage: str = "any"       # "any" | "startup" | "growth" | "public"
min_salary: int | None = None    # Annual, USD, optional
linkedin_auth_status: str = "disconnected"  # "disconnected" | "connected" | "expired"
```

**Derived field:** `linkedin_search_urls` (existing column) is written automatically whenever preferences are saved — the scraper continues to read it unchanged.

**Unchanged:** `linkedin_cookie_encrypted` column — same encryption as today.

---

## Backend: Services & Routes

### `linkedin_url_builder.py`

```python
def build_search_urls(settings: UserSettings) -> list[str]:
    """One URL per job title. Maps seniority → f_E codes, remote_preference → f_WT codes."""
```

LinkedIn URL parameter mapping:
- `f_WT=2` → remote, `f_WT=3` → hybrid, `f_WT=1` → onsite (omit for any)
- `f_E=4` → mid-senior, `f_E=5` → director, `f_E=3` → associate, `f_E=2` → entry
- `f_TPR=r604800` → posted in last 7 days (always applied)

**Note:** `company_stage` has no equivalent LinkedIn URL filter parameter. It is stored in preferences but is not applied to the LinkedIn search URL. It is reserved for future use as a post-discovery filter on the scoring/review step.

### `browser.py` — `open_login_window(session_id)`

1. Spawn non-headless Chromium page at `linkedin.com/login`
2. Background thread polls `context.cookies()` every 2s for `li_at`
3. On detection: encrypt + save to `UserSettings`, set `linkedin_auth_status = "connected"`, store `{"status": "connected"}` in a module-level dict keyed by `session_id` (in-process; safe for local single-process deployment)
4. Timeout after 5 minutes: store `{"status": "timeout"}`
5. `session_id` is a `uuid4` string generated at auth-start time

### New API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/settings/preferences` | Fetch current preferences |
| `PUT` | `/api/settings/preferences` | Save preferences + rebuild search URLs |
| `POST` | `/api/settings/linkedin/start-auth` | Spawn Playwright window → return `{session_id}` |
| `GET` | `/api/settings/linkedin/auth-status/{session_id}` | Poll: `waiting` \| `connected` \| `timeout` |
| `DELETE` | `/api/settings/linkedin/disconnect` | Clear cookie, set status → `disconnected` |

Existing `GET/PUT /api/settings` endpoints remain untouched.

---

## Frontend

### `/setup` Page — 3-Step Wizard

**State:** `currentStep: 1 | 2 | 3`, `sessionId: string | null`, `authStatus: "waiting" | "connected" | "timeout"`

**Step gating:**
- Step 1 → 2: requires `job_titles.length > 0`
- Step 2 → 3: requires `authStatus === "connected"`

**Step 2 polling:** `useEffect` with `setInterval(2000)` calls `/auth-status/{sessionId}` until status is not `"waiting"`, then clears interval.

### `/settings` Page — Compact Summary Card

Replaces current LinkedIn cookie + URL fields:

```
LinkedIn Discovery
─────────────────────────────────────────────
✅ Connected · Session valid
Searching for: Senior PM, Lead PM · Remote · US
Last discovered: 2h ago · 312 jobs in DB

[Edit Preferences]  [Reconnect]
```

The job count shown is the total count of jobs in the local DB — fetched from the existing `GET /api/jobs` count, not from LinkedIn directly.

If `linkedin_auth_status === "expired"`:
```
⚠️ Session expired — discovery is paused.
[Reconnect →]
```

If `linkedin_auth_status === "disconnected"`:
```
Not connected.
[Set Up LinkedIn →]  (→ navigates to /setup)
```

### Sidebar Auto-redirect

On mount, `useSWR("/api/settings/preferences")`. If response `job_titles === "[]"` or `[]`, `router.push("/setup")`.

---

## Cookie Expiry & Re-auth

**Backend:** `run_discovery()` catches `SessionExpiredError` and sets `settings.linkedin_auth_status = "expired"` before returning.

**Frontend — passive:** Sidebar and jobs page read `linkedin_auth_status`. If `"expired"`, persistent amber banner:
> ⚠️ LinkedIn session expired — discovery is paused. [Reconnect →]

Clicking "Reconnect" → `/setup?step=2` (wizard opens at Step 2, skipping preferences).

**Frontend — active:** Discovery triggered manually with expired cookie → API returns `401 {"detail": "linkedin_session_expired"}` → modal prompt with single "Reconnect" CTA.

---

## Out of Scope

- Browser extension for cookie capture (future, when cloud hosting is needed)
- OAuth / official LinkedIn API (requires LinkedIn partner approval)
- YC scraper improvements (known 406 limitation, separate concern)
- Industry preferences field (YAGNI — can be added later)

---

## Files Changed

### New files
- `backend/app/services/linkedin_url_builder.py`
- `backend/alembic/versions/<auto-generated>_add_job_preferences_to_settings.py`
- `frontend/app/setup/page.tsx`
- `frontend/components/setup/preferences-step.tsx`
- `frontend/components/setup/linkedin-auth-step.tsx`
- `frontend/components/setup/ready-step.tsx`
- `frontend/components/ui/tag-input.tsx`

### Modified files
- `backend/app/models/settings.py` — new columns
- `backend/app/services/browser.py` — `open_login_window()`
- `backend/app/routes/settings.py` — new endpoints
- `backend/app/workflows/discovery.py` — set `auth_status = "expired"` on `SessionExpiredError`
- `frontend/app/settings/page.tsx` — replace LinkedIn section with summary card
- `frontend/components/layout/sidebar.tsx` — auto-redirect logic
- `frontend/lib/api.ts` — new API client functions
