from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from src.modules.auth_tenants.application.dto import ForgotPasswordInput, ResetPasswordInput
from src.modules.auth_tenants.application.ports import AuditRecorder, Clock, Hasher, Mailer
from src.modules.auth_tenants.domain.entities import PasswordResetToken
from src.modules.auth_tenants.domain.exceptions import (
    PasswordResetTokenInvalidError,
    UserNotFoundError,
)
from src.modules.auth_tenants.domain.repositories import (
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    UserRepository,
)
from src.modules.auth_tenants.domain.services import PasswordPolicy
from src.shared_kernel.security.token_hashing import generate_opaque_token, hash_token


class ForgotPassword:
    """BR-16bis. Réponse identique que l'identifiant existe ou non, pour ne
    pas révéler l'existence d'un compte (protection anti-énumération)."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_reset_repository: PasswordResetTokenRepository,
        mailer: Mailer,
        clock: Clock,
        audit: AuditRecorder,
        *,
        reset_token_ttl_minutes: int,
        reset_base_url: str,
    ) -> None:
        self._users = user_repository
        self._resets = password_reset_repository
        self._mailer = mailer
        self._clock = clock
        self._audit = audit
        self._reset_token_ttl_minutes = reset_token_ttl_minutes
        self._reset_base_url = reset_base_url

    async def execute(self, data: ForgotPasswordInput) -> None:
        user = await self._users.get_by_identifier(data.identifier)
        if user is None or not user.is_active:
            # Volontairement silencieux : ne confirme ni n'infirme l'existence du compte.
            return

        raw_token = generate_opaque_token()
        now = self._clock.now()
        await self._resets.add(
            PasswordResetToken(
                id=uuid4(),
                tenant_id=user.tenant_id,
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=now + timedelta(minutes=self._reset_token_ttl_minutes),
                created_at=now,
            )
        )

        if user.email:
            await self._mailer.send_password_reset(
                to=user.email, reset_link=f"{self._reset_base_url}/{raw_token}"
            )

        await self._audit.record(
            action="auth.password_forgot",
            result="success",
            tenant_id=user.tenant_id,
            user_id=user.id,
        )


class ResetPassword:
    """BR-16bis : applique la politique de mot de passe (BR-08) et révoque
    tous les refresh tokens actifs (BR-16)."""

    def __init__(
        self,
        password_reset_repository: PasswordResetTokenRepository,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        hasher: Hasher,
        clock: Clock,
        audit: AuditRecorder,
    ) -> None:
        self._resets = password_reset_repository
        self._users = user_repository
        self._refresh_tokens = refresh_token_repository
        self._hasher = hasher
        self._clock = clock
        self._audit = audit

    async def execute(self, data: ResetPasswordInput) -> None:
        record = await self._resets.get_by_token_hash(hash_token(data.token))
        if record is None or not record.is_usable(at=self._clock.now()):
            raise PasswordResetTokenInvalidError()

        PasswordPolicy.validate(data.new_password)

        user = await self._users.get_by_id(record.user_id)
        if user is None:
            raise UserNotFoundError()

        user.password_hash = self._hasher.hash(data.new_password)
        await self._users.update(user)
        await self._resets.mark_used(record.id)
        await self._refresh_tokens.revoke_all_for_user(user.id)

        await self._audit.record(
            action="auth.password_reset",
            result="success",
            tenant_id=user.tenant_id,
            user_id=user.id,
        )
