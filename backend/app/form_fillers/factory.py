from app.form_fillers.base import BaseFormFiller
from app.form_fillers.greenhouse import GreenhouseFormFiller
from app.form_fillers.lever import LeverFormFiller
from app.form_fillers.ashby import AshbyFormFiller


class UnsupportedATSError(Exception):
    """Raised when we can't auto-apply because the ATS isn't supported."""


_REGISTRY = {
    "greenhouse": GreenhouseFormFiller,
    "lever": LeverFormFiller,
    "ashby": AshbyFormFiller,
}


def get_form_filler(ats_type: str, browser) -> BaseFormFiller:
    cls = _REGISTRY.get(ats_type)
    if cls is None:
        raise UnsupportedATSError(f"No form filler for ATS '{ats_type}'")
    return cls(browser=browser)
