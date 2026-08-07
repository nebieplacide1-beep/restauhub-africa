"""DTO (Pydantic) d'entrée/sortie des use cases — servent aussi de schémas de
requête/réponse pour les routers FastAPI (voir
docs/modules/01-auth-tenants/06-api-specification.md), afin d'éviter une
double définition entre application et présentation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class RegisterTenantInput(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=120)
    country: str = Field(min_length=2, max_length=2, description="Code pays ISO 3166-1 alpha-2")
    default_currency: str = Field(min_length=3, max_length=3, description="Code devise ISO 4217")
    default_locale: str = Field(min_length=2, max_length=10)
    admin_email: str | None = None
    admin_phone_number: str | None = None
    admin_password: str

    @model_validator(mode="after")
    def _require_one_identifier(self) -> RegisterTenantInput:
        if not self.admin_email and not self.admin_phone_number:
            raise ValueError("admin_email ou admin_phone_number requis")
        return self


class TenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    country: str
    created_at: datetime


class RegisterTenantOutput(BaseModel):
    tenant: TenantSummary
    user_id: UUID


class LoginInput(BaseModel):
    identifier: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TwoFactorChallenge(BaseModel):
    challenge_token: str
    requires_two_factor: bool = True


class VerifyTwoFactorInput(BaseModel):
    challenge_token: str
    code: str


class RefreshTokenInput(BaseModel):
    refresh_token: str


class ForgotPasswordInput(BaseModel):
    identifier: str


class ResetPasswordInput(BaseModel):
    token: str
    new_password: str


class CurrentUserOutput(BaseModel):
    user_id: UUID
    tenant_id: UUID | None
    email: str | None
    phone_number: str | None
    role_codes: list[str]
    permissions: list[str]
    two_factor_enabled: bool


class EnableTwoFactorOutput(BaseModel):
    secret: str
    otpauth_uri: str


class ConfirmTwoFactorInput(BaseModel):
    code: str


class ConfirmTwoFactorOutput(BaseModel):
    recovery_codes: list[str]


class DisableTwoFactorInput(BaseModel):
    password: str
    code: str


class InviteUserInput(BaseModel):
    email: str | None = None
    phone_number: str | None = None
    role_code: str

    @model_validator(mode="after")
    def _require_one_identifier(self) -> InviteUserInput:
        if not self.email and not self.phone_number:
            raise ValueError("email ou phone_number requis")
        return self


class InvitationOutput(BaseModel):
    id: UUID
    email: str | None
    phone_number: str | None
    role_code: str
    tenant_name: str
    expires_at: datetime


class AcceptInvitationInput(BaseModel):
    password: str


class UserSummary(BaseModel):
    id: UUID
    email: str | None
    phone_number: str | None
    is_active: bool
    role_codes: list[str]
    created_at: datetime | None


class UpdateUserRolesInput(BaseModel):
    role_codes: list[str] = Field(min_length=1)


class RoleSummary(BaseModel):
    id: UUID
    code: str
    label: str
    permissions: list[str]


class PermissionSummary(BaseModel):
    id: UUID
    code: str
    domain: str
    action: str


class UpdateRolePermissionsInput(BaseModel):
    permission_codes: list[str]
