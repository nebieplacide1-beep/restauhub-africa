from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.application.dto import LoginInput, TokenPair, TwoFactorChallenge
from src.modules.auth_tenants.application.use_cases.auth_use_cases import LoginUser
from src.modules.auth_tenants.domain.entities import Role, RoleCode, Tenant, TenantStatus, User
from src.modules.auth_tenants.domain.exceptions import (
    AccountLockedDomainError,
    InvalidCredentialsError,
    TenantSuspendedError,
)
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeClock,
    FakeHasher,
    FakePermissionRepository,
    FakeRefreshTokenRepository,
    FakeRoleRepository,
    FakeTenantRepository,
    FakeTokenService,
    FakeUserRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _setup(*, two_factor_enabled: bool = False, tenant_status: TenantStatus = TenantStatus.ACTIF):
    tenants, users, roles, permissions, refresh_tokens = (
        FakeTenantRepository(),
        FakeUserRepository(),
        FakeRoleRepository(),
        FakePermissionRepository(),
        FakeRefreshTokenRepository(),
    )
    hasher = FakeHasher()
    tenant = Tenant(
        id=uuid4(),
        name="Chez Awa",
        slug="chez-awa",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=tenant_status,
        created_at=NOW,
    )
    tenants.by_id[tenant.id] = tenant

    role = Role(id=uuid4(), code=RoleCode.SERVEUR, label="Serveur")
    roles.roles[role.id] = role

    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="serveur@chezawa.ci",
        phone_number=None,
        password_hash=hasher.hash("Str0ng!Passw0rd"),
        is_active=True,
        two_factor_enabled=two_factor_enabled,
        created_at=NOW,
    )
    users.by_id[user.id] = user
    roles.assignments[user.id] = {(role.id, None)}

    use_case = LoginUser(
        users,
        tenants,
        roles,
        permissions,
        refresh_tokens,
        hasher,
        FakeTokenService(),
        FakeClock(NOW),
        FakeAuditRecorder(),
        max_failed_attempts=5,
        lockout_minutes=15,
        refresh_token_ttl_days=30,
        access_token_ttl_minutes=15,
    )
    return use_case, tenant, user, users


@pytest.mark.asyncio
async def test_successful_login_returns_token_pair() -> None:
    use_case, _, user, _ = _setup()
    result = await use_case.execute(LoginInput(identifier=user.email, password="Str0ng!Passw0rd"))
    assert isinstance(result, TokenPair)


@pytest.mark.asyncio
async def test_login_with_two_factor_returns_challenge() -> None:
    use_case, _, user, _ = _setup(two_factor_enabled=True)
    result = await use_case.execute(LoginInput(identifier=user.email, password="Str0ng!Passw0rd"))
    assert isinstance(result, TwoFactorChallenge)


@pytest.mark.asyncio
async def test_wrong_password_raises_invalid_credentials() -> None:
    use_case, _, user, _ = _setup()
    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(LoginInput(identifier=user.email, password="wrong"))


@pytest.mark.asyncio
async def test_account_locks_after_max_failed_attempts() -> None:
    use_case, _, user, users = _setup()
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginInput(identifier=user.email, password="wrong"))

    assert users.by_id[user.id].locked_until is not None
    with pytest.raises(AccountLockedDomainError):
        await use_case.execute(LoginInput(identifier=user.email, password="Str0ng!Passw0rd"))


@pytest.mark.asyncio
async def test_suspended_tenant_blocks_login() -> None:
    use_case, _, user, _ = _setup(tenant_status=TenantStatus.SUSPENDU)
    with pytest.raises(TenantSuspendedError):
        await use_case.execute(LoginInput(identifier=user.email, password="Str0ng!Passw0rd"))
