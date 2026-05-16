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
