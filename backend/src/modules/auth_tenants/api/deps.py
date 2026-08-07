"""Dépendances FastAPI de la couche présentation : authentification,
autorisation par permission, et construction des repositories/ports liés à
la session de la requête courante.

Choix délibéré : `HTTPBearer` plutôt que `OAuth2PasswordBearer` — l'API
attend un corps JSON (`LoginInput`), pas un formulaire `grant_type=password`.
Le support OAuth2 complet (authorization code, fournisseurs tiers) reste une
extension possible sans changer ce fichier (décision à valider #3,
docs/modules/01-auth-tenants/03-architecture.md).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth_tenants.application.ports import (
    AccessTokenClaims,
    AuditRecorder,
    Clock,
    Hasher,
    Mailer,
    TokenService,
    TwoFactorService,
)
from src.modules.auth_tenants.domain.entities import User
from src.modules.auth_tenants.domain.repositories import (
    InvitationRepository,
    PermissionRepository,
    RefreshTokenRepository,
    RoleRepository,
    TenantRepository,
    TwoFactorRepository,
    UserRepository,
)
from src.modules.auth_tenants.infrastructure.audit_recorder import SqlAlchemyAuditRecorder
from src.modules.auth_tenants.infrastructure.clock import SystemClock
from src.modules.auth_tenants.infrastructure.db.repositories import (
    SqlAlchemyInvitationRepository,
    SqlAlchemyPermissionRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyTenantRepository,
    SqlAlchemyTwoFactorRepository,
    SqlAlchemyUserRepository,
)
from src.modules.auth_tenants.infrastructure.notifications.console_mailer import ConsoleMailer
from src.modules.auth_tenants.infrastructure.security.argon2_hasher import Argon2Hasher
from src.modules.auth_tenants.infrastructure.security.jwt_service import JWTService
from src.modules.auth_tenants.infrastructure.security.totp_service import TOTPService
from src.shared_kernel.config import get_settings
from src.shared_kernel.db.session import auth_lookup_session, tenant_scoped_session
from src.shared_kernel.exceptions import ForbiddenError, UnauthenticatedError
from src.shared_kernel.security.symmetric_encryption import SymmetricEncryptor

bearer_scheme = HTTPBearer(auto_error=False)


# --- Ports d'infrastructure (sans état, sûrs à réutiliser entre requêtes) ---


def get_hasher() -> Hasher:
    return Argon2Hasher()


def get_token_service() -> TokenService:
    settings = get_settings()
    return JWTService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes,
    )


def get_two_factor_service() -> TwoFactorService:
    return TOTPService(SymmetricEncryptor(get_settings().two_factor_encryption_key))


def get_mailer() -> Mailer:
    return ConsoleMailer()


def get_clock() -> Clock:
    return SystemClock()


def get_activation_base_url() -> str:
    return f"{get_settings().frontend_url}/invitations"


# --- Authentification ---


async def get_access_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
) -> AccessTokenClaims:
    if credentials is None:
        raise UnauthenticatedError("En-tête Authorization manquant.")
    return token_service.decode_access_token(credentials.credentials)


async def get_request_db_session(
    claims: AccessTokenClaims = Depends(get_access_claims),
) -> AsyncIterator[AsyncSession]:
    """Session bornée au tenant de l'utilisateur authentifié (ou transverse
    si Super Administrateur, BR-24)."""
    async with tenant_scoped_session(
        tenant_id=claims.tenant_id, is_super_admin=claims.is_super_admin
    ) as session:
        yield session


async def get_current_user(
    claims: AccessTokenClaims = Depends(get_access_claims),
    session: AsyncSession = Depends(get_request_db_session),
) -> User:
    user = await SqlAlchemyUserRepository(session).get_by_id(claims.user_id)
    if user is None or not user.is_active:
        raise UnauthenticatedError("Compte introuvable ou désactivé.")
    return user


def require_permission(permission_code: str):
    async def _check(claims: AccessTokenClaims = Depends(get_access_claims)) -> AccessTokenClaims:
        if permission_code not in claims.permissions:
            raise ForbiddenError(f"Permission requise : {permission_code}")
        return claims

    return _check


async def require_super_admin(
    claims: AccessTokenClaims = Depends(get_access_claims),
) -> AccessTokenClaims:
    if not claims.is_super_admin:
        raise ForbiddenError("Réservé au Super Administrateur.")
    return claims


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# --- Sessions publiques (pré-authentification, voir 05-modele-donnees.md#54) ---


async def get_auth_lookup_session() -> AsyncIterator[AsyncSession]:
    async with auth_lookup_session() as session:
        yield session


# --- Regroupement des repositories pour limiter le nombre de paramètres des routers ---


@dataclass
class Repositories:
    tenants: TenantRepository
    users: UserRepository
    roles: RoleRepository
    permissions: PermissionRepository
    refresh_tokens: RefreshTokenRepository
    two_factor: TwoFactorRepository
    invitations: InvitationRepository
    audit: AuditRecorder


def build_repositories(session: AsyncSession) -> Repositories:
    return Repositories(
        tenants=SqlAlchemyTenantRepository(session),
        users=SqlAlchemyUserRepository(session),
        roles=SqlAlchemyRoleRepository(session),
        permissions=SqlAlchemyPermissionRepository(session),
        refresh_tokens=SqlAlchemyRefreshTokenRepository(session),
        two_factor=SqlAlchemyTwoFactorRepository(session),
        invitations=SqlAlchemyInvitationRepository(session),
        audit=SqlAlchemyAuditRecorder(session),
    )


async def get_repositories(session: AsyncSession = Depends(get_request_db_session)) -> Repositories:
    return build_repositories(session)


async def get_public_repositories(
    session: AsyncSession = Depends(get_auth_lookup_session),
) -> Repositories:
    return build_repositories(session)
