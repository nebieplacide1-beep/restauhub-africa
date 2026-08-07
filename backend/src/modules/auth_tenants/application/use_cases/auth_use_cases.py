from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.modules.auth_tenants.application.dto import (
    CurrentUserOutput,
    LoginInput,
    RefreshTokenInput,
    TokenPair,
    TwoFactorChallenge,
    VerifyTwoFactorInput,
)
from src.modules.auth_tenants.application.ports import (
    AuditRecorder,
    Clock,
    Hasher,
    TokenService,
    TwoFactorService,
)
from src.modules.auth_tenants.application.use_cases._claims import build_access_claims
from src.modules.auth_tenants.domain.entities import RefreshToken, User
from src.modules.auth_tenants.domain.exceptions import (
    AccountLockedDomainError,
    InvalidCredentialsError,
    InvalidOrRevokedTokenError,
    InvalidTwoFactorCodeError,
    TenantNotFoundError,
    TenantSuspendedError,
    UserNotFoundError,
)
from src.modules.auth_tenants.domain.repositories import (
    PermissionRepository,
    RefreshTokenRepository,
    RoleRepository,
    TenantRepository,
    TwoFactorRepository,
    UserRepository,
)
from src.shared_kernel.security.token_hashing import generate_opaque_token, hash_token

CHALLENGE_PURPOSE_LOGIN_2FA = "login_2fa"


class LoginUser:
    """BR-13/BR-17 : authentification, avec déclenchement du défi 2FA si le
    compte l'a activé."""

    def __init__(
        self,
        user_repository: UserRepository,
        tenant_repository: TenantRepository,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        refresh_token_repository: RefreshTokenRepository,
        hasher: Hasher,
        token_service: TokenService,
        clock: Clock,
        audit: AuditRecorder,
        *,
        max_failed_attempts: int,
        lockout_minutes: int,
        refresh_token_ttl_days: int,
        access_token_ttl_minutes: int,
    ) -> None:
        self._users = user_repository
        self._tenants = tenant_repository
        self._roles = role_repository
        self._permissions = permission_repository
        self._refresh_tokens = refresh_token_repository
        self._hasher = hasher
        self._tokens = token_service
        self._clock = clock
        self._audit = audit
        self._max_failed_attempts = max_failed_attempts
        self._lockout_minutes = lockout_minutes
        self._refresh_token_ttl_days = refresh_token_ttl_days
        self._access_token_ttl_minutes = access_token_ttl_minutes

    async def execute(
        self, data: LoginInput, *, ip_address: str | None = None
    ) -> TokenPair | TwoFactorChallenge:
        now = self._clock.now()
        user = await self._users.get_by_identifier(data.identifier)
        if user is None:
            await self._audit.record(action="auth.login", result="failure", ip_address=ip_address)
            raise InvalidCredentialsError()

        if user.tenant_id is not None:
            tenant = await self._tenants.get_by_id(user.tenant_id)
            if tenant is None:
                raise TenantNotFoundError()
            if not tenant.is_operational:
                raise TenantSuspendedError()

        if user.is_locked(at=now):
            raise AccountLockedDomainError()

        if not user.is_active or not self._hasher.verify(
            plain=data.password, hashed=user.password_hash
        ):
            await self._register_failed_attempt(user, now=now)
            await self._audit.record(
                action="auth.login",
                result="failure",
                tenant_id=user.tenant_id,
                user_id=user.id,
                ip_address=ip_address,
            )
            raise InvalidCredentialsError()

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        await self._users.update(user)

        if user.two_factor_enabled:
            challenge_token = self._tokens.create_challenge_token(
                user_id=user.id, purpose=CHALLENGE_PURPOSE_LOGIN_2FA
            )
            await self._audit.record(
                action="auth.login",
                result="challenge_required",
                tenant_id=user.tenant_id,
                user_id=user.id,
                ip_address=ip_address,
            )
            return TwoFactorChallenge(challenge_token=challenge_token)

        await self._audit.record(
            action="auth.login",
            result="success",
            tenant_id=user.tenant_id,
            user_id=user.id,
            ip_address=ip_address,
        )
        return await self._issue_token_pair(user)

    async def _register_failed_attempt(self, user: User, *, now: datetime) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= self._max_failed_attempts:
            user.locked_until = now + timedelta(minutes=self._lockout_minutes)
        await self._users.update(user)

    async def _issue_token_pair(self, user: User) -> TokenPair:
        claims = await build_access_claims(user, self._roles, self._permissions)
        access_token = self._tokens.create_access_token(claims)

        opaque_refresh = generate_opaque_token()
        now = self._clock.now()
        await self._refresh_tokens.add(
            RefreshToken(
                id=uuid4(),
                tenant_id=user.tenant_id,
                user_id=user.id,
                token_hash=hash_token(opaque_refresh),
                expires_at=now + timedelta(days=self._refresh_token_ttl_days),
                created_at=now,
            )
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=opaque_refresh,
            expires_in=self._access_token_ttl_minutes * 60,
        )


class VerifyTwoFactorChallenge:
    def __init__(
        self,
        user_repository: UserRepository,
        two_factor_repository: TwoFactorRepository,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        refresh_token_repository: RefreshTokenRepository,
        two_factor_service: TwoFactorService,
        token_service: TokenService,
        clock: Clock,
        audit: AuditRecorder,
        *,
        refresh_token_ttl_days: int,
        access_token_ttl_minutes: int,
    ) -> None:
        self._users = user_repository
        self._two_factor = two_factor_repository
        self._roles = role_repository
        self._permissions = permission_repository
        self._refresh_tokens = refresh_token_repository
        self._totp = two_factor_service
        self._tokens = token_service
        self._clock = clock
        self._audit = audit
        self._refresh_token_ttl_days = refresh_token_ttl_days
        self._access_token_ttl_minutes = access_token_ttl_minutes

    async def execute(self, data: VerifyTwoFactorInput) -> TokenPair:
        user_id = self._tokens.decode_challenge_token(
            data.challenge_token, expected_purpose=CHALLENGE_PURPOSE_LOGIN_2FA
        )
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        secret = await self._two_factor.get_by_user(user.id)
        if secret is None or not self._totp.verify_code(
            encrypted_secret=secret.encrypted_secret, code=data.code
        ):
            await self._audit.record(
                action="auth.2fa_verify",
                result="failure",
                tenant_id=user.tenant_id,
                user_id=user.id,
            )
            raise InvalidTwoFactorCodeError()

        await self._audit.record(
            action="auth.2fa_verify", result="success", tenant_id=user.tenant_id, user_id=user.id
        )

        claims = await build_access_claims(user, self._roles, self._permissions)
        access_token = self._tokens.create_access_token(claims)
        opaque_refresh = generate_opaque_token()
        now = self._clock.now()
        await self._refresh_tokens.add(
            RefreshToken(
                id=uuid4(),
                tenant_id=user.tenant_id,
                user_id=user.id,
                token_hash=hash_token(opaque_refresh),
                expires_at=now + timedelta(days=self._refresh_token_ttl_days),
                created_at=now,
            )
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=opaque_refresh,
            expires_in=self._access_token_ttl_minutes * 60,
        )


class RefreshAccessToken:
    """BR-13/BR-15 : rotation à chaque usage, révocation de la chaîne en cas
    de réutilisation d'un token déjà consommé (section 3.4)."""

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        clock: Clock,
        audit: AuditRecorder,
        *,
        refresh_token_ttl_days: int,
        access_token_ttl_minutes: int,
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._permissions = permission_repository
        self._refresh_tokens = refresh_token_repository
        self._tokens = token_service
        self._clock = clock
        self._audit = audit
        self._refresh_token_ttl_days = refresh_token_ttl_days
        self._access_token_ttl_minutes = access_token_ttl_minutes

    async def execute(self, data: RefreshTokenInput) -> TokenPair:
        existing = await self._refresh_tokens.get_by_hash(hash_token(data.refresh_token))
        if existing is None:
            raise InvalidOrRevokedTokenError()

        now = self._clock.now()
        if existing.revoked_at is not None:
            # Réutilisation détectée : la totalité de la chaîne est révoquée.
            await self._refresh_tokens.revoke_all_for_user(existing.user_id)
            await self._audit.record(
                action="auth.refresh_reuse_detected",
                result="failure",
                tenant_id=existing.tenant_id,
                user_id=existing.user_id,
            )
            raise InvalidOrRevokedTokenError()

        if not existing.is_valid(at=now):
            raise InvalidOrRevokedTokenError()

        user = await self._users.get_by_id(existing.user_id)
        if user is None or not user.is_active:
            raise InvalidOrRevokedTokenError()

        claims = await build_access_claims(user, self._roles, self._permissions)
        access_token = self._tokens.create_access_token(claims)

        opaque_refresh = generate_opaque_token()
        new_token = RefreshToken(
            id=uuid4(),
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_hash=hash_token(opaque_refresh),
            expires_at=now + timedelta(days=self._refresh_token_ttl_days),
            created_at=now,
        )
        await self._refresh_tokens.add(new_token)
        existing.revoked_at = now
        existing.replaced_by = new_token.id
        await self._refresh_tokens.revoke(existing.id)

        await self._audit.record(
            action="auth.refresh", result="success", tenant_id=user.tenant_id, user_id=user.id
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=opaque_refresh,
            expires_in=self._access_token_ttl_minutes * 60,
        )


class LogoutUser:
    def __init__(
        self, refresh_token_repository: RefreshTokenRepository, audit: AuditRecorder
    ) -> None:
        self._refresh_tokens = refresh_token_repository
        self._audit = audit

    async def execute(self, refresh_token: str, *, user_id: UUID, tenant_id: UUID | None) -> None:
        existing = await self._refresh_tokens.get_by_hash(hash_token(refresh_token))
        if existing is not None:
            await self._refresh_tokens.revoke(existing.id)
        await self._audit.record(
            action="auth.logout", result="success", tenant_id=tenant_id, user_id=user_id
        )


class GetCurrentUser:
    def __init__(
        self, role_repository: RoleRepository, permission_repository: PermissionRepository
    ) -> None:
        self._roles = role_repository
        self._permissions = permission_repository

    async def execute(self, user: User) -> CurrentUserOutput:
        claims = await build_access_claims(user, self._roles, self._permissions)
        return CurrentUserOutput(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            phone_number=user.phone_number,
            role_codes=claims.role_codes,
            permissions=claims.permissions,
            two_factor_enabled=user.two_factor_enabled,
        )
