from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.auth_tenants.api.deps import (
    Repositories,
    get_activation_base_url,
    get_clock,
    get_current_user,
    get_hasher,
    get_mailer,
    get_public_repositories,
    get_repositories,
    require_permission,
)
from src.modules.auth_tenants.application.dto import (
    AcceptInvitationInput,
    InvitationOutput,
    InviteUserInput,
    UpdateUserRolesInput,
    UserSummary,
)
from src.modules.auth_tenants.application.ports import Clock, Hasher, Mailer
from src.modules.auth_tenants.application.use_cases.user_use_cases import (
    AcceptInvitation,
    DeactivateUser,
    GetInvitationPreview,
    InviteUser,
    ListUsers,
    ReactivateUser,
    ResendInvitation,
    UpdateUserRoles,
)
from src.modules.auth_tenants.domain.entities import User
from src.shared_kernel.config import get_settings

router = APIRouter(tags=["users"])

USERS_MANAGE = require_permission("users:manage")


# --- Invitations (publiques, cf. docs/.../06-api-specification.md#61) ---


@router.get("/invitations/{token}", response_model=InvitationOutput)
async def get_invitation(
    token: str,
    repos: Repositories = Depends(get_public_repositories),
    clock: Clock = Depends(get_clock),
) -> InvitationOutput:
    return await GetInvitationPreview(repos.invitations, repos.tenants, repos.roles, clock).execute(
        token
    )


@router.post("/invitations/{token}/accept", response_model=UserSummary, status_code=201)
async def accept_invitation(
    token: str,
    payload: AcceptInvitationInput,
    repos: Repositories = Depends(get_public_repositories),
    hasher: Hasher = Depends(get_hasher),
    clock: Clock = Depends(get_clock),
) -> UserSummary:
    use_case = AcceptInvitation(
        repos.invitations, repos.users, repos.roles, hasher, clock, repos.audit
    )
    return await use_case.execute(token, payload)


# --- Gestion des utilisateurs du tenant (BR-09/BR-10/BR-11, permission users:manage) ---


@router.get("/users", response_model=list[UserSummary], dependencies=[Depends(USERS_MANAGE)])
async def list_users(
    user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)
) -> list[UserSummary]:
    assert user.tenant_id is not None
    return await ListUsers(repos.users, repos.roles).execute(user.tenant_id)


@router.post(
    "/users/invitations",
    response_model=InvitationOutput,
    status_code=201,
    dependencies=[Depends(USERS_MANAGE)],
)
async def invite_user(
    payload: InviteUserInput,
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
    mailer: Mailer = Depends(get_mailer),
    clock: Clock = Depends(get_clock),
    activation_base_url: str = Depends(get_activation_base_url),
) -> InvitationOutput:
    settings = get_settings()
    use_case = InviteUser(
        repos.invitations,
        repos.users,
        repos.roles,
        repos.tenants,
        mailer,
        clock,
        repos.audit,
        invitation_ttl_hours=settings.invitation_ttl_hours,
        activation_base_url=activation_base_url,
    )
    return await use_case.execute(user, payload)


@router.post(
    "/users/invitations/{invitation_id}/resend",
    response_model=InvitationOutput,
    dependencies=[Depends(USERS_MANAGE)],
)
async def resend_invitation(
    invitation_id: UUID,
    repos: Repositories = Depends(get_repositories),
    mailer: Mailer = Depends(get_mailer),
    clock: Clock = Depends(get_clock),
    activation_base_url: str = Depends(get_activation_base_url),
) -> InvitationOutput:
    settings = get_settings()
    use_case = ResendInvitation(
        repos.invitations,
        repos.tenants,
        repos.roles,
        mailer,
        clock,
        invitation_ttl_hours=settings.invitation_ttl_hours,
        activation_base_url=activation_base_url,
    )
    return await use_case.execute(invitation_id)


@router.patch("/users/{user_id}/roles", status_code=204, dependencies=[Depends(USERS_MANAGE)])
async def update_user_roles(
    user_id: UUID,
    payload: UpdateUserRolesInput,
    actor: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    await UpdateUserRoles(repos.users, repos.roles, repos.audit).execute(actor, user_id, payload)


@router.post("/users/{user_id}/deactivate", status_code=204, dependencies=[Depends(USERS_MANAGE)])
async def deactivate_user(
    user_id: UUID,
    actor: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    await DeactivateUser(repos.users, repos.refresh_tokens, repos.audit).execute(actor, user_id)


@router.post("/users/{user_id}/reactivate", status_code=204, dependencies=[Depends(USERS_MANAGE)])
async def reactivate_user(
    user_id: UUID,
    actor: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    await ReactivateUser(repos.users, repos.audit).execute(actor, user_id)
