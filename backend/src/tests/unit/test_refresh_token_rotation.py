from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.application.dto import RefreshTokenInput
from src.modules.auth_tenants.application.use_cases.auth_use_cases import RefreshAccessToken
from src.modules.auth_tenants.domain.entities import RefreshToken, Role, RoleCode, User
from src.modules.auth_tenants.domain.exceptions import InvalidOrRevokedTokenError
from src.shared_kernel.security.token_hashing import generate_opaque_token, hash_token
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeClock,
    FakePermissionRepository,
    FakeRefreshTokenRepository,
    FakeRoleRepository,
    FakeTokenService,
    FakeUserRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _setup():
    users, roles, permissions, refresh_tokens = (
        FakeUserRepository(),
        FakeRoleRepository(),
        FakePermissionRepository(),
        FakeRefreshTokenRepository(),
    )
    role = Role(id=uuid4(), code=RoleCode.SERVEUR, label="Serveur")
    roles.roles[role.id] = role
    user = User(
        id=uuid4(),
        tenant_id=uuid4(),
        email="serveur@chezawa.ci",
        phone_number=None,
        password_hash="x",
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )
    users.by_id[user.id] = user
    roles.assignments[user.id] = {role.id}

    raw_token = generate_opaque_token()
    original = RefreshToken(
        id=uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime(2026, 2, 1, tzinfo=UTC),
        created_at=NOW,
    )
    refresh_tokens.by_hash[original.token_hash] = original

    use_case = RefreshAccessToken(
        users,
        roles,
        permissions,
        refresh_tokens,
        FakeTokenService(),
        FakeClock(NOW),
        FakeAuditRecorder(),
        refresh_token_ttl_days=30,
        access_token_ttl_minutes=15,
    )
    return use_case, refresh_tokens, raw_token, user


@pytest.mark.asyncio
async def test_refresh_rotates_token() -> None:
    use_case, refresh_tokens, raw_token, _ = _setup()
    result = await use_case.execute(RefreshTokenInput(refresh_token=raw_token))
    assert result.refresh_token != raw_token
    assert len(refresh_tokens.by_hash) == 2


@pytest.mark.asyncio
async def test_reusing_a_revoked_token_revokes_the_whole_chain() -> None:
    use_case, refresh_tokens, raw_token, user = _setup()
    await use_case.execute(RefreshTokenInput(refresh_token=raw_token))  # rotation légitime

    with pytest.raises(InvalidOrRevokedTokenError):
        await use_case.execute(RefreshTokenInput(refresh_token=raw_token))  # réutilisation

    assert all(
        t.revoked_at is not None for t in refresh_tokens.by_hash.values() if t.user_id == user.id
    )
