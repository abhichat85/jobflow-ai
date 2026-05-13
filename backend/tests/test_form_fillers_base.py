import pytest
from app.form_fillers.base import ApplicationData, ApplyResult, BaseFormFiller


def test_application_data_dataclass():
    d = ApplicationData(
        name="Abhishek",
        email="a@example.com",
        phone="+1-555-0000",
        linkedin_url="https://linkedin.com/in/abhi",
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear hiring manager...",
        custom_answers={"Why us?": "Because AI."},
    )
    assert d.name == "Abhishek"


def test_apply_result_dataclass():
    r = ApplyResult(success=True, confirmation_text="Thanks!", screenshot_path="/tmp/x.png")
    assert r.success is True


def test_base_form_filler_is_abstract():
    with pytest.raises(TypeError):
        BaseFormFiller(browser=None)


def test_full_subclass_can_instantiate():
    class Mock(BaseFormFiller):
        ats_name = "mock"
        async def fill(self, apply_url, data):
            return ApplyResult(success=True)

    m = Mock(browser=None)
    assert m.ats_name == "mock"
