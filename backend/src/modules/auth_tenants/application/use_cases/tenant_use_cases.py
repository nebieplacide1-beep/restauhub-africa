from __future__ import annotations

from uuid import UUID, uuid4

from src.modules.auth_tenants.application.dto import (
    RegisterTenantInput,
    RegisterTenantOutput,
    TenantSummary,
)
from src.modules.auth_tenants.application.ports import AuditRecorder, Clock, Hasher
from src.modules.auth_tenants.domain.entities import RoleCode, Tenant, TenantStatus, User
from src.modules.auth_tenants.domain.exceptions import (
    IdentifierAlreadyUsedError,
    TenantNotFoundError,
)
from src.modules.auth_tenants.domain.repositories import (
    RoleRepository,
    TenantRepository,
    UserRepository,
)
from src.modules.auth_tenants.domain.services import PasswordPolicy
from src.modules.auth_tenants.domain.value_objects import Email, PhoneNumber, TenantSlug


class RegisterTenant:
    """BR-01/BR-02 : inscription libre-service d'un établissement, avec
    création automatique de son premier utilisateur Administrateur."""

    def __init__(
        self,
        tenant_repository: TenantRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        hasher: Hasher,
        clock: Clock,
        audit: AuditRecorder,
    ) -> None:
        self._tenants = tenant_repository
        self._users = user_repository
        self._roles = role_repository
        self._hasher = hasher
        self._clock = clock
        self._audit = audit

    async def execute(self, data: RegisterTenantInput) -> RegisterTenantOutput:
        email = Email(data.admin_email) if data.admin_email else None
        phone = PhoneNumber(data.admin_phone_number) if data.admin_phone_number else None

        PasswordPolicy.validate(data.admin_password)

        if await self._users.identifier_exists(
            email=str(email) if email else None,
            phone_number=str(phone) if phone else None,
        ):
            raise IdentifierAlreadyUsedError("Cet email ou numéro de téléphone est déjà utilisé.")

        slug = await self._generate_unique_slug(data.tenant_name)

        tenant = Tenant(
            id=uuid4(),
            name=data.tenant_name,
            slug=str(slug),
            country=data.country.upper(),
            default_currency=data.default_currency.upper(),
            default_locale=data.default_locale,
            status=TenantStatus.EN_ESSAI,
            created_at=self._clock.now(),
        )
        await self._tenants.add(tenant)

        user = User(
            id=uuid4(),
            tenant_id=tenant.id,
            email=str(email) if email else None,
            phone_number=str(phone) if phone else None,
            password_hash=self._hasher.hash(data.admin_password),
            is_active=True,
            two_factor_enabled=False,
            created_at=self._clock.now(),
        )
        await self._users.add(user)

        admin_role = await self._roles.get_by_code(RoleCode.ADMINISTRATEUR)
        assert admin_role is not None, "le rôle 'administrateur' doit être seedé"
        await self._roles.assign_role(user_id=user.id, role_id=admin_role.id)

        await self._audit.record(
            action="tenant.registered",
            result="success",
            tenant_id=tenant.id,
            user_id=user.id,
        )

        return RegisterTenantOutput(
            tenant=TenantSummary(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                status=tenant.status.value,
                country=tenant.country,
                created_at=tenant.created_at,
            ),
            user_id=user.id,
        )

    async def _generate_unique_slug(self, tenant_name: str) -> TenantSlug:
        base = TenantSlug.slugify(tenant_name)
        candidate = base
        suffix = 1
        while await self._tenants.slug_exists(str(candidate)):
            suffix += 1
            candidate = TenantSlug(f"{base.value}-{suffix}")
        return candidate


class SuspendTenant:
    """BR-03. Réservé au Super Administrateur (BR-24)."""

    def __init__(self, tenant_repository: TenantRepository, audit: AuditRecorder) -> None:
        self._tenants = tenant_repository
        self._audit = audit

    async def execute(self, tenant_id: UUID) -> None:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFoundError()
        tenant.status = TenantStatus.SUSPENDU
        await self._tenants.update(tenant)
        await self._audit.record(action="tenant.suspended", result="success", tenant_id=tenant_id)


class ReactivateTenant:
    def __init__(self, tenant_repository: TenantRepository, audit: AuditRecorder) -> None:
        self._tenants = tenant_repository
        self._audit = audit

    async def execute(self, tenant_id: UUID) -> None:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFoundError()
        tenant.status = TenantStatus.ACTIF
        await self._tenants.update(tenant)
        await self._audit.record(action="tenant.reactivated", result="success", tenant_id=tenant_id)


class ListTenants:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenants = tenant_repository

    async def execute(self, *, status: str | None = None) -> list[TenantSummary]:
        tenants = await self._tenants.list_all(status=status)
        return [
            TenantSummary(
                id=t.id,
                name=t.name,
                slug=t.slug,
                status=t.status.value,
                country=t.country,
                created_at=t.created_at,
            )
            for t in tenants
        ]
