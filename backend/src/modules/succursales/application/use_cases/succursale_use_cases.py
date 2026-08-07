from __future__ import annotations

from uuid import UUID, uuid4

from src.modules.auth_tenants.application.ports import AuditRecorder, Clock
from src.modules.auth_tenants.domain.entities import User
from src.modules.auth_tenants.domain.repositories import RoleRepository
from src.modules.succursales.application.dto import (
    CreateSuccursaleInput,
    SuccursaleSummary,
    UpdateSuccursaleInput,
)
from src.modules.succursales.application.scope import ensure_in_scope, get_operational_scope
from src.modules.succursales.domain.entities import OpeningHours, Succursale, SuccursaleStatus
from src.modules.succursales.domain.exceptions import SuccursaleNotFoundError
from src.modules.succursales.domain.repositories import SuccursaleRepository
from src.shared_kernel.exceptions import ForbiddenError


def _to_summary(succursale: Succursale) -> SuccursaleSummary:
    return SuccursaleSummary(
        id=succursale.id,
        name=succursale.name,
        address_line=succursale.address_line,
        city=succursale.city,
        country=succursale.country,
        default_currency=succursale.default_currency,
        default_locale=succursale.default_locale,
        status=succursale.status.value,
        phone_number=succursale.phone_number,
        opening_hours=succursale.opening_hours.schedule,
        created_at=succursale.created_at,
    )


async def _require_tenant_wide(user_id: UUID, role_repository: RoleRepository) -> None:
    if await get_operational_scope(user_id, role_repository) is not None:
        raise ForbiddenError("Action réservée aux rôles tenant-wide (PDG, Administrateur).")


class CreateSuccursale:
    """BR2-01/BR2-02. Réservé aux rôles tenant-wide (BR2-08)."""

    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        clock: Clock,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._clock = clock
        self._audit = audit

    async def execute(self, actor: User, data: CreateSuccursaleInput) -> SuccursaleSummary:
        assert actor.tenant_id is not None
        await _require_tenant_wide(actor.id, self._roles)

        succursale = Succursale(
            id=uuid4(),
            tenant_id=actor.tenant_id,
            name=data.name,
            address_line=data.address_line,
            city=data.city,
            country=data.country.upper(),
            default_currency=data.default_currency.upper(),
            default_locale=data.default_locale,
            status=SuccursaleStatus.ACTIVE,
            opening_hours=OpeningHours(data.opening_hours),
            phone_number=data.phone_number,
            created_at=self._clock.now(),
        )
        await self._succursales.add(succursale)
        await self._audit.record(
            action="succursale.created",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
        )
        return _to_summary(succursale)


class UpdateSuccursale:
    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._audit = audit

    async def execute(
        self, actor: User, succursale_id: UUID, data: UpdateSuccursaleInput
    ) -> SuccursaleSummary:
        succursale = await self._succursales.get_by_id(succursale_id)
        if succursale is None:
            raise SuccursaleNotFoundError()

        scope = await get_operational_scope(actor.id, self._roles)
        ensure_in_scope(scope, succursale_id)

        if data.name is not None:
            succursale.name = data.name
        if data.address_line is not None:
            succursale.address_line = data.address_line
        if data.city is not None:
            succursale.city = data.city
        if data.phone_number is not None:
            succursale.phone_number = data.phone_number
        if data.opening_hours is not None:
            succursale.opening_hours = OpeningHours(data.opening_hours)

        await self._succursales.update(succursale)
        await self._audit.record(
            action="succursale.updated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
        )
        return _to_summary(succursale)


class DeactivateSuccursale:
    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._audit = audit

    async def execute(self, actor: User, succursale_id: UUID) -> None:
        await _require_tenant_wide(actor.id, self._roles)
        succursale = await self._succursales.get_by_id(succursale_id)
        if succursale is None:
            raise SuccursaleNotFoundError()
        succursale.status = SuccursaleStatus.INACTIVE
        await self._succursales.update(succursale)
        await self._audit.record(
            action="succursale.deactivated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
        )


class ReactivateSuccursale:
    def __init__(
        self,
        succursale_repository: SuccursaleRepository,
        role_repository: RoleRepository,
        audit: AuditRecorder,
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository
        self._audit = audit

    async def execute(self, actor: User, succursale_id: UUID) -> None:
        await _require_tenant_wide(actor.id, self._roles)
        succursale = await self._succursales.get_by_id(succursale_id)
        if succursale is None:
            raise SuccursaleNotFoundError()
        succursale.status = SuccursaleStatus.ACTIVE
        await self._succursales.update(succursale)
        await self._audit.record(
            action="succursale.reactivated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
        )


class ListSuccursales:
    """BR2-13/BR2-14 : tenant-wide voit tout, sinon uniquement le périmètre."""

    def __init__(
        self, succursale_repository: SuccursaleRepository, role_repository: RoleRepository
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository

    async def execute(self, actor: User) -> list[SuccursaleSummary]:
        assert actor.tenant_id is not None
        scope = await get_operational_scope(actor.id, self._roles)
        if scope is None:
            succursales = await self._succursales.list_by_tenant(actor.tenant_id)
        else:
            succursales = await self._succursales.list_by_ids(scope)
        return [_to_summary(s) for s in succursales]


class GetSuccursale:
    def __init__(
        self, succursale_repository: SuccursaleRepository, role_repository: RoleRepository
    ) -> None:
        self._succursales = succursale_repository
        self._roles = role_repository

    async def execute(self, actor: User, succursale_id: UUID) -> SuccursaleSummary:
        succursale = await self._succursales.get_by_id(succursale_id)
        if succursale is None:
            raise SuccursaleNotFoundError()
        scope = await get_operational_scope(actor.id, self._roles)
        ensure_in_scope(scope, succursale_id)
        return _to_summary(succursale)
