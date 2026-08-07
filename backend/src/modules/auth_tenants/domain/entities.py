"""Entités du domaine `auth_tenants` — dataclasses pures, sans dépendance
framework ni ORM (Clean Architecture : le domaine ne connaît ni FastAPI ni
SQLAlchemy). La persistance est assurée par `infrastructure/db`, qui traduit
ces entités vers/depuis des modèles SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class TenantStatus(StrEnum):
    EN_ESSAI = "en_essai"
    ACTIF = "actif"
    SUSPENDU = "suspendu"
    RESILIE = "résilié"


class RoleCode(StrEnum):
    """Les 12 rôles système de l'AMD (section 7). Non supprimables (BR-20)."""

    CLIENT = "client"
    SERVEUR = "serveur"
    CUISINE = "cuisine"
    CAISSIER = "caissier"
    GERANT = "gerant"
    PDG = "pdg"
    COMPTABLE = "comptable"
    LIVREUR = "livreur"
    ANNONCEUR = "annonceur"
    FOURNISSEUR = "fournisseur"
    ADMINISTRATEUR = "administrateur"
    SUPER_ADMINISTRATEUR = "super_administrateur"


# BR-17 : 2FA obligatoire pour ces rôles à privilèges élevés.
ROLES_REQUIRING_TWO_FACTOR = frozenset(
    {RoleCode.ADMINISTRATEUR, RoleCode.SUPER_ADMINISTRATEUR, RoleCode.PDG, RoleCode.COMPTABLE}
)


@dataclass(slots=True)
class Tenant:
    id: UUID
    name: str
    slug: str
    country: str
    default_currency: str
    default_locale: str
    status: TenantStatus
    created_at: datetime

    @property
    def is_operational(self) -> bool:
        """Un tenant suspendu ou résilié bloque toute authentification (BR-03),
        sauf pour le Super Administrateur qui n'est jamais rattaché à un tenant."""
        return self.status in (TenantStatus.EN_ESSAI, TenantStatus.ACTIF)


@dataclass(slots=True)
class User:
    id: UUID
    tenant_id: UUID | None  # null uniquement pour le Super Administrateur (BR-24)
    email: str | None
    phone_number: str | None
    password_hash: str
    is_active: bool
    two_factor_enabled: bool
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    def is_locked(self, *, at: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > at


@dataclass(slots=True)
class Role:
    id: UUID
    code: RoleCode
    label: str
    is_system_role: bool = True


@dataclass(slots=True)
class Permission:
    id: UUID
    code: str  # format "domaine:action"
    domain: str
    action: str


@dataclass(slots=True)
class RefreshToken:
    id: UUID
    tenant_id: UUID | None
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by: UUID | None = None
    device_label: str | None = None
    created_at: datetime | None = None

    def is_valid(self, *, at: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > at


@dataclass(slots=True)
class TwoFactorSecret:
    user_id: UUID
    tenant_id: UUID | None
    encrypted_secret: str
    recovery_codes_hashed: list[str] = field(default_factory=list)


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(slots=True)
class Invitation:
    id: UUID
    tenant_id: UUID
    role_id: UUID
    invited_by: UUID
    token_hash: str
    status: InvitationStatus
    expires_at: datetime
    email: str | None = None
    phone_number: str | None = None
    accepted_at: datetime | None = None
    created_at: datetime | None = None

    def is_usable(self, *, at: datetime) -> bool:
        return self.status == InvitationStatus.PENDING and self.expires_at > at


@dataclass(slots=True)
class PasswordResetToken:
    """BR-16bis : token opaque à usage unique, durée de vie courte (1h)."""

    id: UUID
    tenant_id: UUID | None
    user_id: UUID
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime | None = None

    def is_usable(self, *, at: datetime) -> bool:
        return self.used_at is None and self.expires_at > at
