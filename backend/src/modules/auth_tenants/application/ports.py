"""Ports vers l'infrastructure technique (non liée à la persistance, voir
`domain/repositories.py` pour celle-ci). Implémentés dans
`infrastructure/security` et `infrastructure/notifications`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...


class Hasher(ABC):
    @abstractmethod
    def hash(self, plain: str) -> str: ...

    @abstractmethod
    def verify(self, *, plain: str, hashed: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    tenant_id: UUID | None
    role_codes: list[str]
    permissions: list[str]
    is_super_admin: bool


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, claims: AccessTokenClaims) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Lève `UnauthenticatedError` si le token est invalide ou expiré."""

    @abstractmethod
    def create_challenge_token(self, *, user_id: UUID, purpose: str, ttl_minutes: int = 5) -> str:
        """Token signé de très courte durée, jamais persisté, utilisé pour les
        flux à deux étapes (défi 2FA, section 4.4 des diagrammes)."""

    @abstractmethod
    def decode_challenge_token(self, token: str, *, expected_purpose: str) -> UUID:
        """Retourne le `user_id` si le token est valide pour ce `purpose`.
        Lève `ChallengeExpiredError` sinon."""


class TwoFactorService(ABC):
    """Possède l'intégralité du cycle de vie du secret TOTP, y compris son
    chiffrement au repos — les use cases ne manipulent jamais de secret en
    clair au-delà de l'écran de provisioning (BR-18)."""

    @abstractmethod
    def generate_secret(self) -> str:
        """Secret TOTP en clair, à chiffrer via `encrypt_secret` avant toute
        persistance."""

    @abstractmethod
    def encrypt_secret(self, plain_secret: str) -> str: ...

    @abstractmethod
    def provisioning_uri(
        self, *, secret: str, account_name: str, issuer: str = "RestauHub Africa"
    ) -> str: ...

    @abstractmethod
    def verify_code(self, *, encrypted_secret: str, code: str) -> bool: ...

    @abstractmethod
    def generate_recovery_codes(self, *, count: int = 10) -> list[str]: ...

    @abstractmethod
    def hash_recovery_code(self, code: str) -> str: ...


class AuditRecorder(ABC):
    """Adapte `shared_kernel.audit.service.record_audit_event` à la session
    liée à la requête courante, pour que les use cases n'aient jamais à
    manipuler une session SQLAlchemy directement (BR-25)."""

    @abstractmethod
    async def record(
        self,
        *,
        action: str,
        result: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None: ...


class Mailer(ABC):
    @abstractmethod
    async def send_invitation(self, *, to: str, tenant_name: str, activation_link: str) -> None: ...

    @abstractmethod
    async def send_password_reset(self, *, to: str, reset_link: str) -> None: ...
