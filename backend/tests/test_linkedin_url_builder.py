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
