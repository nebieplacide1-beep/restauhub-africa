"""Doublures en mémoire des ports du domaine/application — utilisées par les
tests unitaires pour exercer les use cases sans base de données ni réseau.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.modules.auth_tenants.application.ports import (
    AccessTokenClaims,
    AuditRecorder,
    Clock,
    Hasher,
    Mailer,
    TokenService,
)
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
from src.modules.auth_tenants.domain.repositories import (
    InvitationRepository,
    PasswordResetTokenRepository,
    PermissionRepository,
    RefreshTokenRepository,
    RoleRepository,
    TenantRepository,
    TwoFactorRepository,
    UserRepository,
)
from src.modules.succursales.domain.entities import Succursale
from src.modules.succursales.domain.repositories import SuccursaleRepository


class FakeClock(Clock):
    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


class FakeHasher(Hasher):
    """Hachage trivial (préfixe) — jamais utilisé hors tests."""

    def hash(self, plain: str) -> str:
        return f"hashed:{plain}"

    def verify(self, *, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


class FakeTokenService(TokenService):
    def __init__(self) -> None:
        self.issued: dict[str, AccessTokenClaims] = {}
        self.challenges: dict[str, tuple[UUID, str]] = {}
        self._counter = 0

    def create_access_token(self, claims: AccessTokenClaims) -> str:
        self._counter += 1
        token = f"access-{self._counter}"
        self.issued[token] = claims
        return token

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        return self.issued[token]

    def create_challenge_token(self, *, user_id: UUID, purpose: str, ttl_minutes: int = 5) -> str:
        self._counter += 1
        token = f"challenge-{self._counter}"
        self.challenges[token] = (user_id, purpose)
        return token

    def decode_challenge_token(self, token: str, *, expected_purpose: str) -> UUID:
        user_id, purpose = self.challenges[token]
        assert purpose == expected_purpose
        return user_id


class FakeAuditRecorder(AuditRecorder):
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def record(
        self, *, action, result, tenant_id=None, user_id=None, ip_address=None, metadata=None
    ) -> None:
        self.events.append(
            {
                "action": action,
                "result": result,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "metadata": metadata,
            }
        )


class FakeTenantRepository(TenantRepository):
    def __init__(self) -> None:
        self.by_id: dict[UUID, Tenant] = {}

    async def add(self, tenant: Tenant) -> None:
        self.by_id[tenant.id] = tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        return self.by_id.get(tenant_id)

    async def slug_exists(self, slug: str) -> bool:
        return any(t.slug == slug for t in self.by_id.values())

    async def update(self, tenant: Tenant) -> None:
        self.by_id[tenant.id] = tenant

    async def list_all(self, *, status: str | None = None) -> list[Tenant]:
        values = list(self.by_id.values())
        return [t for t in values if status is None or t.status.value == status]


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.by_id: dict[UUID, User] = {}

    async def add(self, user: User) -> None:
        self.by_id[user.id] = user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.by_id.get(user_id)

    async def get_by_identifier(self, identifier: str) -> User | None:
        normalized = identifier.strip().lower()
        for user in self.by_id.values():
            if user.email == normalized or user.phone_number == normalized:
                return user
        return None

    async def identifier_exists(self, *, email: str | None, phone_number: str | None) -> bool:
        for user in self.by_id.values():
            if email and user.email == email:
                return True
            if phone_number and user.phone_number == phone_number:
                return True
        return False

    async def list_by_tenant(self, tenant_id: UUID) -> list[User]:
        return [u for u in self.by_id.values() if u.tenant_id == tenant_id]

    async def update(self, user: User) -> None:
        self.by_id[user.id] = user


class FakeRoleRepository(RoleRepository):
    def __init__(self, roles: list[Role] | None = None) -> None:
        self.roles: dict[UUID, Role] = {r.id: r for r in (roles or [])}
        # user_id -> {(role_id, succursale_id | None)}
        self.assignments: dict[UUID, set[tuple[UUID, UUID | None]]] = {}

    async def get_by_code(self, code: RoleCode) -> Role | None:
        return next((r for r in self.roles.values() if r.code == code), None)

    async def list_all(self) -> list[Role]:
        return list(self.roles.values())

    async def get_roles_for_user(self, user_id: UUID) -> list[Role]:
        role_ids = {role_id for role_id, _ in self.assignments.get(user_id, set())}
        return [self.roles[rid] for rid in role_ids]

    async def assign_role(
        self, *, user_id: UUID, role_id: UUID, succursale_id: UUID | None = None
    ) -> None:
        self.assignments.setdefault(user_id, set()).add((role_id, succursale_id))

    async def remove_role(
        self, *, user_id: UUID, role_id: UUID, succursale_id: UUID | None = None
    ) -> None:
        self.assignments.setdefault(user_id, set()).discard((role_id, succursale_id))

    async def get_staff_for_succursale(self, succursale_id: UUID) -> list[tuple[UUID, RoleCode]]:
        return [
            (user_id, self.roles[role_id].code)
            for user_id, pairs in self.assignments.items()
            for role_id, sid in pairs
            if sid == succursale_id
        ]

    async def get_succursale_ids_for_user(self, user_id: UUID) -> list[UUID | None]:
        return [sid for _, sid in self.assignments.get(user_id, set())]


class FakePermissionRepository(PermissionRepository):
    def __init__(self) -> None:
        self.permissions: list[Permission] = []
        self.defaults: dict[UUID, set[str]] = {}
        self.overrides: dict[UUID, dict[UUID, set[str]]] = {}

    async def list_all(self) -> list[Permission]:
        return self.permissions

    async def get_default_permissions_by_role(self) -> dict[UUID, set[str]]:
        return self.defaults

    async def get_tenant_overrides_by_role(self, tenant_id: UUID) -> dict[UUID, set[str]]:
        return self.overrides.get(tenant_id, {})

    async def set_tenant_override(
        self, *, tenant_id: UUID, role_id: UUID, permission_codes: set[str]
    ) -> None:
        self.overrides.setdefault(tenant_id, {})[role_id] = permission_codes


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        self.by_hash: dict[str, RefreshToken] = {}

    async def add(self, token: RefreshToken) -> None:
        self.by_hash[token.token_hash] = token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.by_hash.get(token_hash)

    async def revoke(self, token_id: UUID) -> None:
        for token in self.by_hash.values():
            if token.id == token_id:
                token.revoked_at = token.revoked_at or datetime.now(UTC)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for token in self.by_hash.values():
            if token.user_id == user_id:
                token.revoked_at = token.revoked_at or datetime.now(UTC)


class FakeTwoFactorRepository(TwoFactorRepository):
    def __init__(self) -> None:
        self.by_user: dict[UUID, TwoFactorSecret] = {}

    async def get_by_user(self, user_id: UUID) -> TwoFactorSecret | None:
        return self.by_user.get(user_id)

    async def add(self, secret: TwoFactorSecret) -> None:
        self.by_user[secret.user_id] = secret

    async def update(self, secret: TwoFactorSecret) -> None:
        self.by_user[secret.user_id] = secret

    async def delete(self, user_id: UUID) -> None:
        self.by_user.pop(user_id, None)


class FakeInvitationRepository(InvitationRepository):
    def __init__(self) -> None:
        self.by_id: dict[UUID, Invitation] = {}

    async def add(self, invitation: Invitation) -> None:
        self.by_id[invitation.id] = invitation

    async def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        return next((i for i in self.by_id.values() if i.token_hash == token_hash), None)

    async def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        return self.by_id.get(invitation_id)

    async def update(self, invitation: Invitation) -> None:
        self.by_id[invitation.id] = invitation


class FakePasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self) -> None:
        self.by_id: dict[UUID, PasswordResetToken] = {}

    async def add(self, token: PasswordResetToken) -> None:
        self.by_id[token.id] = token

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        return next((t for t in self.by_id.values() if t.token_hash == token_hash), None)

    async def mark_used(self, token_id: UUID) -> None:
        token = self.by_id.get(token_id)
        if token is not None:
            token.used_at = token.used_at or datetime.now(UTC)


class FakeMailer(Mailer):
    def __init__(self) -> None:
        self.invitations: list[dict] = []
        self.password_resets: list[dict] = []

    async def send_invitation(self, *, to: str, tenant_name: str, activation_link: str) -> None:
        self.invitations.append(
            {"to": to, "tenant_name": tenant_name, "activation_link": activation_link}
        )

    async def send_password_reset(self, *, to: str, reset_link: str) -> None:
        self.password_resets.append({"to": to, "reset_link": reset_link})


class FakeSuccursaleRepository(SuccursaleRepository):
    def __init__(self) -> None:
        self.by_id: dict[UUID, Succursale] = {}

    async def add(self, succursale: Succursale) -> None:
        self.by_id[succursale.id] = succursale

    async def get_by_id(self, succursale_id: UUID) -> Succursale | None:
        return self.by_id.get(succursale_id)

    async def list_by_tenant(self, tenant_id: UUID) -> list[Succursale]:
        return [s for s in self.by_id.values() if s.tenant_id == tenant_id]

    async def list_by_ids(self, succursale_ids: list[UUID]) -> list[Succursale]:
        return [s for sid in succursale_ids if (s := self.by_id.get(sid)) is not None]

    async def update(self, succursale: Succursale) -> None:
        self.by_id[succursale.id] = succursale
