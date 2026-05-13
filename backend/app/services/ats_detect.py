from typing import Optional


def detect_ats(url: Optional[str]) -> str:
    """Detect which ATS powers a given apply URL."""
    if not url:
        return "unknown"
    u = url.lower()
    if "greenhouse.io" in u:
        return "greenhouse"
    if "lever.co" in u:
        return "lever"
    if "ashbyhq.com" in u or "ashby.io" in u:
        return "ashby"
    return "unknown"
