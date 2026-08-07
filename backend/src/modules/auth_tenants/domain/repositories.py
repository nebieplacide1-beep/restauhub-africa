"""Ports (interfaces) vers la persistance — implémentés par
`infrastructure/db/repositories.py`. Le domaine et l'application ne
dépendent que de ces abstractions, jamais de SQLAlchemy directement
(inversion de dépendance, architecture hexagonale).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.auth_tenants.domain.entities import (
    Invitation,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RoleCode,
    Tenant,
    TwoFactorSecret,
    User,
)


class TenantRepository(ABC):
    @abstractmethod
    async def add(self, tenant: Tenant) -> None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> Tenant | None: ...

    @abstractmethod
    async def slug_exists(self, slug: str) -> bool: ...

    @abstractmethod
    async def update(self, tenant: Tenant) -> None: ...

    @abstractmethod
    async def list_all(self, *, status: str | None = None) -> list[Tenant]: ...


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_identifier(self, identifier: str) -> User | None:
        """Recherche cross-tenant par email OU téléphone (identifiants globalement
        uniques, voir docs/modules/01-auth-tenants/05-modele-donnees.md#52).
        Ne doit être appelé que dans un `auth_lookup_session`."""

    @abstractmethod
    async def identifier_exists(self, *, email: str | None, phone_number: str | None) -> bool: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> list[User]: ...

    @abstractmethod
    async def update(self, user: User) -> None: ...


class RoleRepository(ABC):
    @abstractmethod
    async def get_by_code(self, code: RoleCode) -> Role | None: ...

    @abstractmethod
    async def list_all(self) -> list[Role]: ...

    @abstractmethod
    async def get_roles_for_user(self, user_id: UUID) -> list[Role]: ...

    @abstractmethod
    async def assign_role(self, *, user_id: UUID, role_id: UUID) -> None: ...

    @abstractmethod
    async def remove_role(self, *, user_id: UUID, role_id: UUID) -> None: ...


class PermissionRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[Permission]: ...

    @abstractmethod
    async def get_default_permissions_by_role(self) -> dict[UUID, set[str]]: ...

    @abstractmethod
    async def get_tenant_overrides_by_role(self, tenant_id: UUID) -> dict[UUID, set[str]]: ...

    @abstractmethod
    async def set_tenant_override(
        self, *, tenant_id: UUID, role_id: UUID, permission_codes: set[str]
    ) -> None: ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...


class TwoFactorRepository(ABC):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> TwoFactorSecret | None: ...

    @abstractmethod
    async def add(self, secret: TwoFactorSecret) -> None: ...

    @abstractmethod
    async def update(self, secret: TwoFactorSecret) -> None: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None: ...


class InvitationRepository(ABC):
    @abstractmethod
    async def add(self, invitation: Invitation) -> None: ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...

    @abstractmethod
    async def get_by_id(self, invitation_id: UUID) -> Invitation | None: ...

    @abstractmethod
    async def update(self, invitation: Invitation) -> None: ...


class PasswordResetTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: PasswordResetToken) -> None: ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    @abstractmethod
    async def mark_used(self, token_id: UUID) -> None: ...
