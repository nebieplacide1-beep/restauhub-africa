from __future__ import annotations

from src.modules.auth_tenants.application.dto import (
    ConfirmTwoFactorInput,
    ConfirmTwoFactorOutput,
    DisableTwoFactorInput,
    EnableTwoFactorOutput,
)
from src.modules.auth_tenants.application.ports import AuditRecorder, Hasher, TwoFactorService
from src.modules.auth_tenants.domain.entities import TwoFactorSecret, User
from src.modules.auth_tenants.domain.exceptions import (
    InvalidCredentialsError,
    InvalidTwoFactorCodeError,
    TwoFactorAlreadyEnabledError,
)
from src.modules.auth_tenants.domain.repositories import TwoFactorRepository, UserRepository


class EnableTwoFactor:
    """BR-18, étape 1/2 : génère le secret et l'URI de provisioning (QR)."""

    def __init__(
        self, two_factor_repository: TwoFactorRepository, two_factor_service: TwoFactorService
    ) -> None:
        self._secrets = two_factor_repository
        self._totp = two_factor_service

    async def execute(self, user: User) -> EnableTwoFactorOutput:
        if user.two_factor_enabled:
            raise TwoFactorAlreadyEnabledError()

        existing = await self._secrets.get_by_user(user.id)
        if existing is not None:
            await self._secrets.delete(user.id)

        plain_secret = self._totp.generate_secret()
        await self._secrets.add(
            TwoFactorSecret(
                user_id=user.id,
                tenant_id=user.tenant_id,
                encrypted_secret=self._totp.encrypt_secret(plain_secret),
            )
        )
        account_name = user.email or user.phone_number or str(user.id)
        return EnableTwoFactorOutput(
            secret=plain_secret,
            otpauth_uri=self._totp.provisioning_uri(secret=plain_secret, account_name=account_name),
        )


class ConfirmTwoFactor:
    """BR-18, étape 2/2 : confirme avec un premier code valide, génère les
    10 codes de récupération à usage unique."""

    def __init__(
        self,
        two_factor_repository: TwoFactorRepository,
        user_repository: UserRepository,
        two_factor_service: TwoFactorService,
        audit: AuditRecorder,
    ) -> None:
        self._secrets = two_factor_repository
        self._users = user_repository
        self._totp = two_factor_service
        self._audit = audit

    async def execute(self, user: User, data: ConfirmTwoFactorInput) -> ConfirmTwoFactorOutput:
        secret = await self._secrets.get_by_user(user.id)
        if secret is None or not self._totp.verify_code(
            encrypted_secret=secret.encrypted_secret, code=data.code
        ):
            raise InvalidTwoFactorCodeError()

        recovery_codes = self._totp.generate_recovery_codes()
        secret.recovery_codes_hashed = [self._totp.hash_recovery_code(c) for c in recovery_codes]
        await self._secrets.update(secret)

        user.two_factor_enabled = True
        await self._users.update(user)

        await self._audit.record(
            action="auth.2fa_enabled", result="success", tenant_id=user.tenant_id, user_id=user.id
        )
        return ConfirmTwoFactorOutput(recovery_codes=recovery_codes)


class DisableTwoFactor:
    """BR-19 : nécessite mot de passe + code 2FA courant."""

    def __init__(
        self,
        two_factor_repository: TwoFactorRepository,
        user_repository: UserRepository,
        two_factor_service: TwoFactorService,
        hasher: Hasher,
        audit: AuditRecorder,
    ) -> None:
        self._secrets = two_factor_repository
        self._users = user_repository
        self._totp = two_factor_service
        self._hasher = hasher
        self._audit = audit

    async def execute(self, user: User, data: DisableTwoFactorInput) -> None:
        if not self._hasher.verify(plain=data.password, hashed=user.password_hash):
            raise InvalidCredentialsError()

        secret = await self._secrets.get_by_user(user.id)
        if secret is None or not self._totp.verify_code(
            encrypted_secret=secret.encrypted_secret, code=data.code
        ):
            raise InvalidTwoFactorCodeError()

        await self._secrets.delete(user.id)
        user.two_factor_enabled = False
        await self._users.update(user)
        await self._audit.record(
            action="auth.2fa_disabled", result="success", tenant_id=user.tenant_id, user_id=user.id
        )
