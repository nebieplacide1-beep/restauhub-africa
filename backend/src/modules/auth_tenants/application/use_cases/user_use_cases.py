from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

from src.modules.auth_tenants.application.dto import (
    AcceptInvitationInput,
    InvitationOutput,
    InviteUserInput,
    UpdateUserRolesInput,
    UserSummary,
)
from src.modules.auth_tenants.application.ports import AuditRecorder, Clock, Hasher, Mailer
from src.modules.auth_tenants.domain.entities import Invitation, InvitationStatus, RoleCode, User
from src.modules.auth_tenants.domain.exceptions import (
    IdentifierAlreadyUsedError,
    InvitationExpiredError,
    InvitationNotFoundError,
    UserNotFoundError,
    ValidationError,
)
from src.modules.auth_tenants.domain.repositories import (
    InvitationRepository,
    RefreshTokenRepository,
    RoleRepository,
    TenantRepository,
    UserRepository,
)
from src.modules.auth_tenants.domain.services import PasswordPolicy
from src.modules.auth_tenants.domain.value_objects import Email, PhoneNumber
from src.shared_kernel.security.token_hashing import generate_opaque_token, hash_token


class InviteUser:
    """BR-09 : invitation à durée de vie limitée (72h par défaut)."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        tenant_repository: TenantRepository,
        mailer: Mailer,
        clock: Clock,
        audit: AuditRecorder,
        *,
        invitation_ttl_hours: int,
        activation_base_url: str,
    ) -> None:
        self._invitations = invitation_repository
        self._users = user_repository
        self._roles = role_repository
        self._tenants = tenant_repository
        self._mailer = mailer
        self._clock = clock
        self._audit = audit
        self._invitation_ttl_hours = invitation_ttl_hours
        self._activation_base_url = activation_base_url

    async def execute(self, inviter: User, data: InviteUserInput) -> InvitationOutput:
        email = Email(data.email) if data.email else None
        phone = PhoneNumber(data.phone_number) if data.phone_number else None

        if await self._users.identifier_exists(
            email=str(email) if email else None, phone_number=str(phone) if phone else None
        ):
            raise IdentifierAlreadyUsedError()

        role = await self._roles.get_by_code(RoleCode(data.role_code))
        if role is None:
            raise ValidationError(f"Rôle inconnu : {data.role_code!r}")

        assert inviter.tenant_id is not None
        tenant = await self._tenants.get_by_id(inviter.tenant_id)
        assert tenant is not None

        raw_token = generate_opaque_token()
        now = self._clock.now()
        invitation = Invitation(
            id=uuid4(),
            tenant_id=inviter.tenant_id,
            role_id=role.id,
            invited_by=inviter.id,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=now + timedelta(hours=self._invitation_ttl_hours),
            email=str(email) if email else None,
            phone_number=str(phone) if phone else None,
            created_at=now,
        )
        await self._invitations.add(invitation)

        if email:
            await self._mailer.send_invitation(
                to=str(email),
                tenant_name=tenant.name,
                activation_link=f"{self._activation_base_url}/{raw_token}",
            )

        await self._audit.record(
            action="user.invited", result="success", tenant_id=inviter.tenant_id, user_id=inviter.id
        )
        return InvitationOutput(
            id=invitation.id,
            email=invitation.email,
            phone_number=invitation.phone_number,
            role_code=role.code.value,
            tenant_name=tenant.name,
            expires_at=invitation.expires_at,
        )


class ResendInvitation:
    def __init__(
        self,
        invitation_repository: InvitationRepository,
        tenant_repository: TenantRepository,
        role_repository: RoleRepository,
        mailer: Mailer,
        clock: Clock,
        *,
        invitation_ttl_hours: int,
        activation_base_url: str,
    ) -> None:
        self._invitations = invitation_repository
        self._tenants = tenant_repository
        self._roles = role_repository
        self._mailer = mailer
        self._clock = clock
        self._invitation_ttl_hours = invitation_ttl_hours
        self._activation_base_url = activation_base_url

    async def execute(self, invitation_id: UUID) -> InvitationOutput:
        invitation = await self._invitations.get_by_id(invitation_id)
        if invitation is None:
            raise InvitationNotFoundError()

        raw_token = generate_opaque_token()
        invitation.token_hash = hash_token(raw_token)
        invitation.expires_at = self._clock.now() + timedelta(hours=self._invitation_ttl_hours)
        invitation.status = InvitationStatus.PENDING
        await self._invitations.update(invitation)

        tenant = await self._tenants.get_by_id(invitation.tenant_id)
        role = next((r for r in await self._roles.list_all() if r.id == invitation.role_id), None)
        assert tenant is not None and role is not None

        if invitation.email:
            await self._mailer.send_invitation(
                to=invitation.email,
                tenant_name=tenant.name,
                activation_link=f"{self._activation_base_url}/{raw_token}",
            )
        return InvitationOutput(
            id=invitation.id,
            email=invitation.email,
            phone_number=invitation.phone_number,
            role_code=role.code.value,
            tenant_name=tenant.name,
            expires_at=invitation.expires_at,
        )


class AcceptInvitation:
    """BR-09/BR-10 : active le compte invité en définissant son mot de passe."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        hasher: Hasher,
        clock: Clock,
        audit: AuditRecorder,
    ) -> None:
        self._invitations = invitation_repository
        self._users = user_repository
        self._roles = role_repository
        self._hasher = hasher
        self._clock = clock
        self._audit = audit

    async def execute(self, token: str, data: AcceptInvitationInput) -> UserSummary:
        invitation = await self._invitations.get_by_token_hash(hash_token(token))
        now = self._clock.now()
        if invitation is None:
            raise InvitationNotFoundError()
        if not invitation.is_usable(at=now):
            raise InvitationExpiredError()

        PasswordPolicy.validate(data.password)

        if await self._users.identifier_exists(
            email=invitation.email, phone_number=invitation.phone_number
        ):
            raise IdentifierAlreadyUsedError()

        user = User(
            id=uuid4(),
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            phone_number=invitation.phone_number,
            password_hash=self._hasher.hash(data.password),
            is_active=True,
            two_factor_enabled=False,
            created_at=now,
        )
        await self._users.add(user)
        await self._roles.assign_role(user_id=user.id, role_id=invitation.role_id)

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now
        await self._invitations.update(invitation)

        await self._audit.record(
            action="user.invitation_accepted",
            result="success",
            tenant_id=invitation.tenant_id,
            user_id=user.id,
        )

        roles = await self._roles.get_roles_for_user(user.id)
        return UserSummary(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            is_active=user.is_active,
            role_codes=[r.code.value for r in roles],
            created_at=user.created_at,
        )


class GetInvitationPreview:
    """Consultation publique d'une invitation (`GET /invitations/{token}`),
    pour afficher le formulaire d'activation avant authentification."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        tenant_repository: TenantRepository,
        role_repository: RoleRepository,
        clock: Clock,
    ) -> None:
        self._invitations = invitation_repository
        self._tenants = tenant_repository
        self._roles = role_repository
        self._clock = clock

    async def execute(self, token: str) -> InvitationOutput:
        invitation = await self._invitations.get_by_token_hash(hash_token(token))
        if invitation is None:
            raise InvitationNotFoundError()
        if not invitation.is_usable(at=self._clock.now()):
            raise InvitationExpiredError()

        tenant = await self._tenants.get_by_id(invitation.tenant_id)
        role = next((r for r in await self._roles.list_all() if r.id == invitation.role_id), None)
        assert tenant is not None and role is not None
        return InvitationOutput(
            id=invitation.id,
            email=invitation.email,
            phone_number=invitation.phone_number,
            role_code=role.code.value,
            tenant_name=tenant.name,
            expires_at=invitation.expires_at,
        )


class ListUsers:
    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository) -> None:
        self._users = user_repository
        self._roles = role_repository

    async def execute(self, tenant_id: UUID) -> list[UserSummary]:
        users = await self._users.list_by_tenant(tenant_id)
        summaries = []
        for user in users:
            roles = await self._roles.get_roles_for_user(user.id)
            summaries.append(
                UserSummary(
                    id=user.id,
                    email=user.email,
                    phone_number=user.phone_number,
                    is_active=user.is_active,
                    role_codes=[r.code.value for r in roles],
                    created_at=user.created_at,
                )
            )
        return summaries


class UpdateUserRoles:
    """BR-22 : un utilisateur peut cumuler plusieurs rôles."""

    def __init__(
        self, user_repository: UserRepository, role_repository: RoleRepository, audit: AuditRecorder
    ) -> None:
        self._users = user_repository
        self._roles = role_repository
        self._audit = audit

    async def execute(self, actor: User, target_user_id: UUID, data: UpdateUserRolesInput) -> None:
        target = await self._users.get_by_id(target_user_id)
        if target is None:
            raise UserNotFoundError()

        requested_codes = {RoleCode(c) for c in data.role_codes}
        current_roles = await self._roles.get_roles_for_user(target.id)
        current_codes = {r.code for r in current_roles}

        for code in requested_codes - current_codes:
            role = await self._roles.get_by_code(code)
            assert role is not None
            await self._roles.assign_role(user_id=target.id, role_id=role.id)

        for role in current_roles:
            if role.code not in requested_codes:
                await self._roles.remove_role(user_id=target.id, role_id=role.id)

        await self._audit.record(
            action="user.roles_updated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={"target_user_id": str(target.id), "role_codes": list(data.role_codes)},
        )


class DeactivateUser:
    """BR-11."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        audit: AuditRecorder,
    ) -> None:
        self._users = user_repository
        self._refresh_tokens = refresh_token_repository
        self._audit = audit

    async def execute(self, actor: User, target_user_id: UUID) -> None:
        target = await self._users.get_by_id(target_user_id)
        if target is None:
            raise UserNotFoundError()
        target.is_active = False
        await self._users.update(target)
        await self._refresh_tokens.revoke_all_for_user(target.id)
        await self._audit.record(
            action="user.deactivated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={"target_user_id": str(target.id)},
        )


class ReactivateUser:
    def __init__(self, user_repository: UserRepository, audit: AuditRecorder) -> None:
        self._users = user_repository
        self._audit = audit

    async def execute(self, actor: User, target_user_id: UUID) -> None:
        target = await self._users.get_by_id(target_user_id)
        if target is None:
            raise UserNotFoundError()
        target.is_active = True
        await self._users.update(target)
        await self._audit.record(
            action="user.reactivated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={"target_user_id": str(target.id)},
        )
