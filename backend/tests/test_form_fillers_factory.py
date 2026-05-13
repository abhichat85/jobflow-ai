import pytest

from app.form_fillers.factory import get_form_filler, UnsupportedATSError
from app.form_fillers.greenhouse import GreenhouseFormFiller
from app.form_fillers.lever import LeverFormFiller
from app.form_fillers.ashby import AshbyFormFiller


def test_factory_returns_greenhouse():
    f = get_form_filler("greenhouse", browser=None)
    assert isinstance(f, GreenhouseFormFiller)


def test_factory_returns_lever():
    f = get_form_filler("lever", browser=None)
    assert isinstance(f, LeverFormFiller)


def test_factory_returns_ashby():
    f = get_form_filler("ashby", browser=None)
    assert isinstance(f, AshbyFormFiller)


def test_factory_unknown_raises():
    with pytest.raises(UnsupportedATSError):
        get_form_filler("workday", browser=None)
