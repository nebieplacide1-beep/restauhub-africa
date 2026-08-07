"""Implémentations SQLAlchemy des ports de persistance (`domain/repositories.py`).

Chaque méthode traduit entre `UserModel`/`TenantModel`/... (ORM) et les
dataclasses du domaine — le reste de l'application ne voit jamais un objet
SQLAlchemy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth_tenants.domain.entities import (
    Invitation,
    InvitationStatus,
    Permission,
    RefreshToken,
    Role,
    RoleCode,
    Tenant,
    TenantStatus,
    TwoFactorSecret,
    User,
)
from src.modules.auth_tenants.domain.repositories import (
    InvitationRepository,
    PermissionRepository,
    RefreshTokenRepository,
    RoleRepository,
    TenantRepository,
    TwoFactorRepository,
    UserRepository,
)
from src.modules.auth_tenants.infrastructure.db.models import (
    InvitationModel,
    PermissionModel,
    RefreshTokenModel,
    RoleModel,
    RolePermissionModel,
    TenantModel,
    TwoFactorSecretModel,
    UserModel,
    UserRoleModel,
)


def _tenant_to_domain(m: TenantModel) -> Tenant:
    return Tenant(
        id=m.id,
        name=m.name,
        slug=m.slug,
        country=m.country,
        default_currency=m.default_currency,
        default_locale=m.default_locale,
        status=TenantStatus(m.status),
        created_at=m.created_at,
    )


def _user_to_domain(m: UserModel) -> User:
    return User(
        id=m.id,
        tenant_id=m.tenant_id,
        email=m.email,
        phone_number=m.phone_number,
        password_hash=m.password_hash,
        is_active=m.is_active,
        two_factor_enabled=m.two_factor_enabled,
        failed_login_attempts=m.failed_login_attempts,
        locked_until=m.locked_until,
        last_login_at=m.last_login_at,
        created_at=m.created_at,
    )


def _role_to_domain(m: RoleModel) -> Role:
    return Role(id=m.id, code=RoleCode(m.code), label=m.label, is_system_role=m.is_system_role)


def _invitation_to_domain(m: InvitationModel) -> Invitation:
    return Invitation(
        id=m.id,
        tenant_id=m.tenant_id,
        role_id=m.role_id,
        invited_by=m.invited_by,
        token_hash=m.token_hash,
        status=InvitationStatus(m.status),
        expires_at=m.expires_at,
        email=m.email,
        phone_number=m.phone_number,
        accepted_at=m.accepted_at,
        created_at=m.created_at,
    )


class SqlAlchemyTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tenant: Tenant) -> None:
        self._session.add(
            TenantModel(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                country=tenant.country,
                default_currency=tenant.default_currency,
                default_locale=tenant.default_locale,
                status=tenant.status.value,
            )
        )
        await self._session.flush()

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        model = await self._session.get(TenantModel, tenant_id)
        return _tenant_to_domain(model) if model else None

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(select(TenantModel.id).where(TenantModel.slug == slug))
        return result.first() is not None

    async def update(self, tenant: Tenant) -> None:
        model = await self._session.get(TenantModel, tenant.id)
        assert model is not None
        model.status = tenant.status.value
        await self._session.flush()

    async def list_all(self, *, status: str | None = None) -> list[Tenant]:
        stmt = select(TenantModel)
        if status:
            stmt = stmt.where(TenantModel.status == status)
        result = await self._session.execute(stmt.order_by(TenantModel.created_at.desc()))
        return [_tenant_to_domain(m) for m in result.scalars().all()]


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                phone_number=user.phone_number,
                password_hash=user.password_hash,
                is_active=user.is_active,
                two_factor_enabled=user.two_factor_enabled,
            )
        )
        await self._session.flush()

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _user_to_domain(model) if model else None

    async def get_by_identifier(self, identifier: str) -> User | None:
        normalized = identifier.strip().lower()
        result = await self._session.execute(
            select(UserModel).where(
                (UserModel.email == normalized) | (UserModel.phone_number == normalized)
            )
        )
        model = result.scalars().first()
        return _user_to_domain(model) if model else None

    async def identifier_exists(self, *, email: str | None, phone_number: str | None) -> bool:
        conditions = []
        if email:
            conditions.append(UserModel.email == email)
        if phone_number:
            conditions.append(UserModel.phone_number == phone_number)
        if not conditions:
            return False
        result = await self._session.execute(select(UserModel.id).where(or_(*conditions)))
        return result.first() is not None

    async def list_by_tenant(self, tenant_id: UUID) -> list[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.tenant_id == tenant_id).order_by(UserModel.created_at)
        )
        return [_user_to_domain(m) for m in result.scalars().all()]

    async def update(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        assert model is not None
        model.is_active = user.is_active
        model.two_factor_enabled = user.two_factor_enabled
        model.failed_login_attempts = user.failed_login_attempts
        model.locked_until = user.locked_until
        model.last_login_at = user.last_login_at
        model.password_hash = user.password_hash
        await self._session.flush()


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_code(self, code: RoleCode) -> Role | None:
        result = await self._session.execute(select(RoleModel).where(RoleModel.code == code.value))
        model = result.scalars().first()
        return _role_to_domain(model) if model else None

    async def list_all(self) -> list[Role]:
        result = await self._session.execute(select(RoleModel).order_by(RoleModel.label))
        return [_role_to_domain(m) for m in result.scalars().all()]

    async def get_roles_for_user(self, user_id: UUID) -> list[Role]:
        result = await self._session.execute(
            select(RoleModel)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user_id)
        )
        return [_role_to_domain(m) for m in result.scalars().all()]

    async def assign_role(self, *, user_id: UUID, role_id: UUID) -> None:
        # Cible directement les colonnes de la clé primaire composite (pas de
        # UniqueConstraint séparée, voir models.py) — c'est l'index sur lequel
        # PostgreSQL peut faire porter ON CONFLICT.
        stmt = (
            pg_insert(UserRoleModel)
            .values(user_id=user_id, role_id=role_id)
            .on_conflict_do_nothing(index_elements=["user_id", "role_id"])
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def remove_role(self, *, user_id: UUID, role_id: UUID) -> None:
        await self._session.execute(
            delete(UserRoleModel).where(
                UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
            )
        )
        await self._session.flush()


class SqlAlchemyPermissionRepository(PermissionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Permission]:
        result = await self._session.execute(select(PermissionModel).order_by(PermissionModel.code))
        return [
            Permission(id=m.id, code=m.code, domain=m.domain, action=m.action)
            for m in result.scalars().all()
        ]

    async def get_default_permissions_by_role(self) -> dict[UUID, set[str]]:
        return await self._get_permissions_by_role(tenant_id=None)

    async def get_tenant_overrides_by_role(self, tenant_id: UUID) -> dict[UUID, set[str]]:
        return await self._get_permissions_by_role(tenant_id=tenant_id)

    async def _get_permissions_by_role(self, *, tenant_id: UUID | None) -> dict[UUID, set[str]]:
        stmt = (
            select(RolePermissionModel.role_id, PermissionModel.code)
            .join(PermissionModel, PermissionModel.id == RolePermissionModel.permission_id)
            .where(
                RolePermissionModel.tenant_id == tenant_id
                if tenant_id
                else RolePermissionModel.tenant_id.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        by_role: dict[UUID, set[str]] = {}
        for role_id, code in result.all():
            by_role.setdefault(role_id, set()).add(code)
        return by_role

    async def set_tenant_override(
        self, *, tenant_id: UUID, role_id: UUID, permission_codes: set[str]
    ) -> None:
        await self._session.execute(
            delete(RolePermissionModel).where(
                RolePermissionModel.tenant_id == tenant_id, RolePermissionModel.role_id == role_id
            )
        )
        if permission_codes:
            result = await self._session.execute(
                select(PermissionModel.id).where(PermissionModel.code.in_(permission_codes))
            )
            for (permission_id,) in result.all():
                self._session.add(
                    RolePermissionModel(
                        tenant_id=tenant_id, role_id=role_id, permission_id=permission_id
                    )
                )
        await self._session.flush()


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> None:
        self._session.add(
            RefreshTokenModel(
                id=token.id,
                tenant_id=token.tenant_id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                device_label=token.device_label,
            )
        )
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalars().first()
        if model is None:
            return None
        return RefreshToken(
            id=model.id,
            tenant_id=model.tenant_id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by=model.replaced_by,
            device_label=model.device_label,
            created_at=model.created_at,
        )

    async def revoke(self, token_id: UUID) -> None:
        model = await self._session.get(RefreshTokenModel, token_id)
        if model is not None:
            model.revoked_at = model.revoked_at or datetime.now(UTC)
            await self._session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.flush()


class SqlAlchemyTwoFactorRepository(TwoFactorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: UUID) -> TwoFactorSecret | None:
        model = await self._session.get(TwoFactorSecretModel, user_id)
        if model is None:
            return None
        return TwoFactorSecret(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            encrypted_secret=model.encrypted_secret,
            recovery_codes_hashed=list(model.recovery_codes_hashed),
        )

    async def add(self, secret: TwoFactorSecret) -> None:
        self._session.add(
            TwoFactorSecretModel(
                user_id=secret.user_id,
                tenant_id=secret.tenant_id,
                encrypted_secret=secret.encrypted_secret,
                recovery_codes_hashed=secret.recovery_codes_hashed,
            )
        )
        await self._session.flush()

    async def update(self, secret: TwoFactorSecret) -> None:
        model = await self._session.get(TwoFactorSecretModel, secret.user_id)
        assert model is not None
        model.recovery_codes_hashed = secret.recovery_codes_hashed
        await self._session.flush()

    async def delete(self, user_id: UUID) -> None:
        model = await self._session.get(TwoFactorSecretModel, user_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invitation: Invitation) -> None:
        self._session.add(
            InvitationModel(
                id=invitation.id,
                tenant_id=invitation.tenant_id,
                role_id=invitation.role_id,
                invited_by=invitation.invited_by,
                token_hash=invitation.token_hash,
                status=invitation.status.value,
                expires_at=invitation.expires_at,
                email=invitation.email,
                phone_number=invitation.phone_number,
            )
        )
        await self._session.flush()

    async def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        result = await self._session.execute(
            select(InvitationModel).where(InvitationModel.token_hash == token_hash)
        )
        model = result.scalars().first()
        return _invitation_to_domain(model) if model else None

    async def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        model = await self._session.get(InvitationModel, invitation_id)
        return _invitation_to_domain(model) if model else None

    async def update(self, invitation: Invitation) -> None:
        model = await self._session.get(InvitationModel, invitation.id)
        assert model is not None
        model.status = invitation.status.value
        model.token_hash = invitation.token_hash
        model.expires_at = invitation.expires_at
        model.accepted_at = invitation.accepted_at
        await self._session.flush()
