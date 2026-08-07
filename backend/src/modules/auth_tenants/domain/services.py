"""Services de domaine : règles métier pures, sans accès I/O.

Les données nécessaires (mots de passe en clair à valider, mappings de
permissions déjà chargés) sont fournies par l'appelant (use case) — ces
services ne connaissent ni la base de données ni le framework web.
"""

from __future__ import annotations

import re
from uuid import UUID

from src.shared_kernel.exceptions import ValidationError

_SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")


class PasswordPolicy:
    """BR-08 : 10 caractères minimum, une majuscule, un chiffre, un symbole."""

    MIN_LENGTH = 10

    @classmethod
    def validate(cls, password: str) -> None:
        errors: list[str] = []
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"au moins {cls.MIN_LENGTH} caractères")
        if not any(c.isupper() for c in password):
            errors.append("au moins une majuscule")
        if not any(c.isdigit() for c in password):
            errors.append("au moins un chiffre")
        if not _SYMBOL_RE.search(password):
            errors.append("au moins un symbole")
        if errors:
            raise ValidationError("Mot de passe invalide, requis : " + ", ".join(errors))


class PermissionResolver:
    """BR-22 (union des rôles) / BR-23 (surcharge par tenant)."""

    @staticmethod
    def resolve(
        *,
        role_ids: list[UUID],
        default_permissions_by_role: dict[UUID, set[str]],
        tenant_overrides_by_role: dict[UUID, set[str]],
    ) -> set[str]:
        effective: set[str] = set()
        for role_id in role_ids:
            if role_id in tenant_overrides_by_role:
                effective |= tenant_overrides_by_role[role_id]
            else:
                effective |= default_permissions_by_role.get(role_id, set())
        return effective
