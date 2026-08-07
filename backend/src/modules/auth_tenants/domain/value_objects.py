"""Value objects du domaine `auth_tenants`.

Immuables, auto-validants : impossible de construire une instance invalide.
Contrairement à un simple `str`, ils portent la règle métier de validation de
format au plus près de la donnée (BR-06).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.modules.auth_tenants.domain.exceptions import InvalidIdentifierFormatError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")  # format E.164


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise InvalidIdentifierFormatError(f"Adresse email invalide : {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().replace(" ", "")
        if not _PHONE_RE.match(normalized):
            raise InvalidIdentifierFormatError(
                "Numéro de téléphone invalide (format E.164 attendu, "
                f"ex. +2250700000000) : {self.value!r}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class TenantSlug:
    value: str

    @staticmethod
    def slugify(name: str) -> TenantSlug:
        slug = name.strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        return TenantSlug(slug or "tenant")

    def __post_init__(self) -> None:
        if not re.match(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$", self.value):
            raise InvalidIdentifierFormatError(f"Slug de tenant invalide : {self.value!r}")

    def __str__(self) -> str:
        return self.value
