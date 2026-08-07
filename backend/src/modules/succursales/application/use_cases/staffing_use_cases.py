from __future__ import annotations

from uuid import UUID

from src.modules.auth_tenants.application.ports import AuditRecorder
from src.modules.auth_tenants.domain.entities import RoleCode, User
from src.modules.auth_tenants.domain.exceptions import UserNotFoundError
from src.modules.auth_tenants.domain.repositories import RoleRepository, UserRepository
from src.modules.succursales.application.dto import AssignStaffInput, RemoveStaffInput, StaffMember
from src.modules.succursales.application.scope import ensure_in_scope, get_operational_scope
from src.modules.succursales.domain.exceptions import (
    StaffAssignmentAlreadyExistsError,
    SuccursaleNotFoundError,
)
from src.modules.succursales.domain.repositories import SuccursaleRepository
from src.shared_kernel.exceptions import ValidationError


async def _get_succursale_in_scope(
    actor: User, succursale_id: UUID, succursales: SuccursaleRepository, roles: RoleRepository
):
    succursale = await succursales.get_by_id(succursale_id)
    if succursale is None:
        raise SuccursaleNotFoundError()
    scope = await get_operational_scope(actor.id, roles)
    ensure_in_scope(scope, succursale_id)
    return succursale


class AssignEmployeeToSuccursale:
    """BR2-07/BR2-10.

    Un rôle « opérationnel » (Gérant, Serveur, ...) est accordé tenant-wide
    par défaut par le Module 1 lors d'une invitation (BR-09), qui ne connaît
    pas la notion de succursale. Rattacher explicitement ce rôle à une
    succursale exprime l'intention de le **restreindre** à ce périmètre :
    l'éventuel rattachement tenant-wide du même rôle est donc retiré plutôt
    que cumulé, sans quoi BR2-09 (Gérant limité à son établissement) ne
    pourrait jamais s'appliquer après une invitation."""

    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        user_repository: UserRepository,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._users = user_repository
        self._audit = audit

    async def execute(self, actor: User, succursale_id: UUID, data: AssignStaffInput) -> None:
        await _get_succursale_in_scope(actor, succursale_id, self._succursales, self._roles)

        target = await self._users.get_by_id(data.user_id)
        if target is None or target.tenant_id != actor.tenant_id:
            raise UserNotFoundError()

        role = await self._roles.get_by_code(RoleCode(data.role_code))
        if role is None:
            raise ValidationError(f"Rôle inconnu : {data.role_code!r}")

        existing = await self._roles.get_staff_for_succursale(succursale_id)
        if (data.user_id, role.code) in existing:
            raise StaffAssignmentAlreadyExistsError()

        # Narrowing : retire un éventuel rattachement tenant-wide du même rôle
        # avant d'ajouter le rattachement scopé (voir docstring de la classe).
        await self._roles.remove_role(user_id=data.user_id, role_id=role.id, succursale_id=None)
        await self._roles.assign_role(
            user_id=data.user_id, role_id=role.id, succursale_id=succursale_id
        )
        await self._audit.record(
            action="succursale.staff_assigned",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={
                "succursale_id": str(succursale_id),
                "target_user_id": str(data.user_id),
                "role_code": data.role_code,
            },
        )


class RemoveStaffAssignment:
    """BR2-12 : ne désactive jamais le compte utilisateur lui-même."""

    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._audit = audit

    async def execute(self, actor: User, succursale_id: UUID, data: RemoveStaffInput) -> None:
        await _get_succursale_in_scope(actor, succursale_id, self._succursales, self._roles)

        role = await self._roles.get_by_code(RoleCode(data.role_code))
        if role is None:
            raise ValidationError(f"Rôle inconnu : {data.role_code!r}")

        await self._roles.remove_role(
            user_id=data.user_id, role_id=role.id, succursale_id=succursale_id
        )
        await self._audit.record(
            action="succursale.staff_removed",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={
                "succursale_id": str(succursale_id),
                "target_user_id": str(data.user_id),
                "role_code": data.role_code,
            },
        )


class ListStaff:
    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        user_repository: UserRepository,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._users = user_repository

    async def execute(self, actor: User, succursale_id: UUID) -> list[StaffMember]:
        await _get_succursale_in_scope(actor, succursale_id, self._succursales, self._roles)

        pairs = await self._roles.get_staff_for_succursale(succursale_id)
        roles_by_user: dict[UUID, list[str]] = {}
        for user_id, role_code in pairs:
            roles_by_user.setdefault(user_id, []).append(role_code.value)

        staff: list[StaffMember] = []
        for user_id, role_codes in roles_by_user.items():
            user = await self._users.get_by_id(user_id)
            if user is None:
                continue
            staff.append(
                StaffMember(
                    user_id=user_id,
                    email=user.email,
                    phone_number=user.phone_number,
                    role_codes=role_codes,
                )
            )
        return staff
