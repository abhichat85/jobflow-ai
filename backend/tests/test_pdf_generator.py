import pytest
from pathlib import Path

weasyprint_available = True
try:
    from app.services.pdf_generator import generate_resume_pdf
except OSError:
    weasyprint_available = False


@pytest.mark.skipif(
    not weasyprint_available,
    reason="WeasyPrint system dependencies (pango/cairo/gobject) not installed — works in Docker",
)
def test_generate_pdf_creates_file(tmp_path):
    output_path = tmp_path / "test_resume.pdf"
    generate_resume_pdf(
        name="Abhishek Chatterjee",
        email="test@test.com",
        phone="+91-1234567890",
        summary="AI product builder focused on LLM-native products.",
        experiences=[
            {
                "role_title": "Founder",
                "company_name": "Einstein Labs",
                "date_range": "2023 — Present",
                "bullets": [
                    "Built AI-native SaaS products and agent workflows",
                    "Designed product strategy for venture studio portfolio",
                ],
            }
        ],
        skills=["Product Strategy", "AI/ML", "Python", "Next.js"],
        output_path=str(output_path),
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0
