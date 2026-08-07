"""Entités du domaine `succursales` — voir docs/modules/02-restaurants-succursales/."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import StrEnum
from uuid import UUID

from src.modules.succursales.domain.exceptions import InvalidOpeningHoursError

WEEKDAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


class SuccursaleStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FERMETURE_TEMPORAIRE = "fermeture_temporaire"


@dataclass(frozen=True, slots=True)
class OpeningHours:
    """BR2-06 : créneaux d'ouverture par jour de semaine (plusieurs créneaux
    possibles par jour).

    `schedule` : `{"lundi": [{"ouverture": "08:00", "fermeture": "22:00"}], ...}`.
    """

    schedule: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for day, ranges in self.schedule.items():
            if day not in WEEKDAYS:
                raise InvalidOpeningHoursError(f"Jour invalide : {day!r}")
            for time_range in ranges:
                try:
                    opening = time.fromisoformat(time_range["ouverture"])
                    closing = time.fromisoformat(time_range["fermeture"])
                except (KeyError, ValueError) as exc:
                    raise InvalidOpeningHoursError(
                        f"Créneau invalide pour {day!r} : {time_range!r}"
                    ) from exc
                if closing <= opening:
                    raise InvalidOpeningHoursError(
                        f"Créneau invalide pour {day!r} : fermeture avant ouverture"
                    )

    def is_open_at(self, moment: datetime) -> bool:
        day = WEEKDAYS[moment.weekday()]
        for time_range in self.schedule.get(day, []):
            opening = time.fromisoformat(time_range["ouverture"])
            closing = time.fromisoformat(time_range["fermeture"])
            if opening <= moment.time() <= closing:
                return True
        return False


@dataclass(slots=True)
class Succursale:
    id: UUID
    tenant_id: UUID
    name: str
    address_line: str
    city: str
    country: str
    default_currency: str
    default_locale: str
    status: SuccursaleStatus
    opening_hours: OpeningHours
    phone_number: str | None = None
    created_at: datetime | None = None

    @property
    def is_operational(self) -> bool:
        return self.status == SuccursaleStatus.ACTIVE
