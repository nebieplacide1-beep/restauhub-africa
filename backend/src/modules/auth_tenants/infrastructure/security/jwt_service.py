from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.modules.auth_tenants.application.ports import AccessTokenClaims, TokenService
from src.modules.auth_tenants.domain.exceptions import ChallengeExpiredError, UnauthenticatedError


class JWTService(TokenService):
    """BR-13/BR-14 : JWT HS256, secret unique par environnement (section 3.4
    de l'architecture — migration vers RS256 possible sans changer ce port)."""

    def __init__(self, *, secret_key: str, algorithm: str, access_token_ttl_minutes: int) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_ttl_minutes = access_token_ttl_minutes

    def create_access_token(self, claims: AccessTokenClaims) -> str:
        now = datetime.now(UTC)
        payload = {
            "type": "access",
            "sub": str(claims.user_id),
            "tenant_id": str(claims.tenant_id) if claims.tenant_id else None,
            "roles": claims.role_codes,
            "permissions": claims.permissions,
            "is_super_admin": claims.is_super_admin,
            "iat": now,
            "exp": now + timedelta(minutes=self._access_token_ttl_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.InvalidTokenError as exc:
            raise UnauthenticatedError("Token invalide ou expiré.") from exc

        if payload.get("type") != "access":
            raise UnauthenticatedError("Type de token invalide.")

        return AccessTokenClaims(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
            role_codes=list(payload.get("roles", [])),
            permissions=list(payload.get("permissions", [])),
            is_super_admin=bool(payload.get("is_super_admin", False)),
        )

    def create_challenge_token(self, *, user_id: UUID, purpose: str, ttl_minutes: int = 5) -> str:
        now = datetime.now(UTC)
        payload = {
            "type": "challenge",
            "purpose": purpose,
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=ttl_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_challenge_token(self, token: str, *, expected_purpose: str) -> UUID:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.InvalidTokenError as exc:
            raise ChallengeExpiredError("Défi expiré ou invalide.") from exc

        if payload.get("type") != "challenge" or payload.get("purpose") != expected_purpose:
            raise ChallengeExpiredError("Défi invalide pour cette opération.")

        return UUID(payload["sub"])
