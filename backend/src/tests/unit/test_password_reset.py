from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.application.dto import ForgotPasswordInput, ResetPasswordInput
from src.modules.auth_tenants.application.use_cases.password_reset_use_cases import (
    ForgotPassword,
    ResetPassword,
)
from src.modules.auth_tenants.domain.entities import RefreshToken, User
from src.modules.auth_tenants.domain.exceptions import PasswordResetTokenInvalidError
from src.shared_kernel.security.token_hashing import generate_opaque_token, hash_token
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeClock,
    FakeHasher,
    FakeMailer,
    FakePasswordResetTokenRepository,
    FakeRefreshTokenRepository,
    FakeUserRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_user() -> User:
    return User(
        id=uuid4(),
        tenant_id=uuid4(),
        email="user@chezawa.ci",
        phone_number=None,
        password_hash=FakeHasher().hash("OldPassw0rd!"),
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )


def _setup():
    users, resets, refresh_tokens, mailer = (
        FakeUserRepository(),
        FakePasswordResetTokenRepository(),
        FakeRefreshTokenRepository(),
        FakeMailer(),
    )
    user = _make_user()
    users.by_id[user.id] = user

    forgot = ForgotPassword(
        users,
        resets,
        mailer,
        FakeClock(NOW),
        FakeAuditRecorder(),
        reset_token_ttl_minutes=60,
        reset_base_url="https://app.test/reset-password",
    )
    reset = ResetPassword(
        resets, users, refresh_tokens, FakeHasher(), FakeClock(NOW), FakeAuditRecorder()
    )
    return forgot, reset, users, resets, refresh_tokens, mailer, user


@pytest.mark.asyncio
async def test_forgot_password_sends_email_for_existing_user() -> None:
    forgot, _, _, resets, _, mailer, user = _setup()
    await forgot.execute(ForgotPasswordInput(identifier=user.email))

    assert len(mailer.password_resets) == 1
    assert len(resets.by_id) == 1


@pytest.mark.asyncio
async def test_forgot_password_is_silent_for_unknown_identifier() -> None:
    forgot, _, _, resets, _, mailer, _ = _setup()
    await forgot.execute(ForgotPasswordInput(identifier="nobody@nowhere.ci"))

    assert mailer.password_resets == []
    assert resets.by_id == {}


@pytest.mark.asyncio
async def test_reset_password_changes_password_and_revokes_tokens() -> None:
    forgot, reset, users, resets, refresh_tokens, mailer, user = _setup()
    await forgot.execute(ForgotPasswordInput(identifier=user.email))
    raw_token = mailer.password_resets[0]["reset_link"].rsplit("/", 1)[-1]

    stale_refresh = generate_opaque_token()
    refresh_tokens.by_hash[hash_token(stale_refresh)] = RefreshToken(
        id=uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=hash_token(stale_refresh),
        expires_at=datetime(2026, 2, 1, tzinfo=UTC),
        created_at=NOW,
    )

    await reset.execute(ResetPasswordInput(token=raw_token, new_password="NewStr0ng!Pass"))

    updated = users.by_id[user.id]
    assert FakeHasher().verify(plain="NewStr0ng!Pass", hashed=updated.password_hash)
    assert all(t.revoked_at is not None for t in refresh_tokens.by_hash.values())
    assert next(iter(resets.by_id.values())).used_at is not None


@pytest.mark.asyncio
async def test_reset_password_rejects_unknown_token() -> None:
    _, reset, *_ = _setup()
    with pytest.raises(PasswordResetTokenInvalidError):
        await reset.execute(
            ResetPasswordInput(token="not-a-real-token", new_password="NewStr0ng!Pass")
        )


@pytest.mark.asyncio
async def test_reset_password_rejects_already_used_token() -> None:
    forgot, reset, _, resets, _, mailer, user = _setup()
    await forgot.execute(ForgotPasswordInput(identifier=user.email))
    raw_token = mailer.password_resets[0]["reset_link"].rsplit("/", 1)[-1]
    token = next(iter(resets.by_id.values()))
    await resets.mark_used(token.id)

    with pytest.raises(PasswordResetTokenInvalidError):
        await reset.execute(ResetPasswordInput(token=raw_token, new_password="NewStr0ng!Pass"))
