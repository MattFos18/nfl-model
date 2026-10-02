"""Every test writes its warnings (nflmodel.warnlog) to a temporary file, never the committed data/weather/warnings.json."""
import pytest

from nflmodel import warnlog


@pytest.fixture(autouse=True)
def _warnlog_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(warnlog, "F", tmp_path / "warnings.json")
    monkeypatch.setattr(warnlog, "_SEEN", set())
