"""Résolution du périmètre opérationnel d'un utilisateur (BR2-08/BR2-09,
section 3.5 de l'architecture du Module 2) — construit sur `RoleRepository`
du Module 1, réutilisé directement plutôt que dupliqué."""

from __future__ import annotations

from uuid import UUID

from src.modules.auth_tenants.domain.repositories import RoleRepository
from src.shared_kernel.exceptions import ForbiddenError


async def get_operational_scope(
    user_id: UUID, role_repository: RoleRepository
) -> list[UUID] | None:
    """`None` = tout le tenant (au moins un rattachement tenant-wide, BR2-08).
    Sinon, la liste (dédupliquée) des succursales auxquelles l'utilisateur est
    explicitement rattaché (BR2-09)."""
    succursale_ids = await role_repository.get_succursale_ids_for_user(user_id)
    if any(s is None for s in succursale_ids):
        return None
    return list({s for s in succursale_ids if s is not None})


def ensure_in_scope(scope: list[UUID] | None, succursale_id: UUID) -> None:
    if scope is not None and succursale_id not in scope:
        raise ForbiddenError("Cette succursale n'est pas dans votre périmètre.")
