from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApplicationData:
    name: str
    email: str
    phone: str
    linkedin_url: str
    resume_pdf_path: str
    cover_letter_text: str
    custom_answers: dict[str, str] = field(default_factory=dict)


@dataclass
class ApplyResult:
    success: bool
    confirmation_text: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None


class BaseFormFiller(ABC):
    """Submits an application via a specific ATS's form UI."""

    ats_name: str = "base"

    def __init__(self, browser):
        self.browser = browser

    @abstractmethod
    async def fill(self, apply_url: str, data: ApplicationData) -> ApplyResult: ...
