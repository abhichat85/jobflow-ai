import pytest
from app.services.ats_detect import detect_ats


@pytest.mark.parametrize("url,expected", [
    ("https://boards.greenhouse.io/anthropic/jobs/12345", "greenhouse"),
    ("https://jobs.lever.co/openai/abc-123", "lever"),
    ("https://jobs.ashbyhq.com/notion/abc", "ashby"),
    ("https://ashby.io/anthropic/jobs/123", "ashby"),
    ("https://www.linkedin.com/jobs/view/12345", "unknown"),
    ("https://example.com/careers/123", "unknown"),
    ("", "unknown"),
    (None, "unknown"),
])
def test_detect_ats(url, expected):
    assert detect_ats(url) == expected
