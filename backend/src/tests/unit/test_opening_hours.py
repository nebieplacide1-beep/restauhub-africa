import pytest

from src.modules.succursales.domain.entities import OpeningHours
from src.modules.succursales.domain.exceptions import InvalidOpeningHoursError


def test_valid_schedule_is_accepted() -> None:
    OpeningHours({"lundi": [{"ouverture": "08:00", "fermeture": "22:00"}], "dimanche": []})


def test_rejects_unknown_day() -> None:
    with pytest.raises(InvalidOpeningHoursError):
        OpeningHours({"lundimanche": [{"ouverture": "08:00", "fermeture": "22:00"}]})


def test_rejects_closing_before_opening() -> None:
    with pytest.raises(InvalidOpeningHoursError):
        OpeningHours({"lundi": [{"ouverture": "22:00", "fermeture": "08:00"}]})


def test_rejects_malformed_time() -> None:
    with pytest.raises(InvalidOpeningHoursError):
        OpeningHours({"lundi": [{"ouverture": "8h", "fermeture": "22:00"}]})


def test_is_open_at() -> None:
    from datetime import UTC, datetime

    hours = OpeningHours({"lundi": [{"ouverture": "08:00", "fermeture": "22:00"}]})
    monday_noon = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)  # un lundi
    monday_late = datetime(2026, 1, 5, 23, 0, tzinfo=UTC)
    assert hours.is_open_at(monday_noon) is True
    assert hours.is_open_at(monday_late) is False
