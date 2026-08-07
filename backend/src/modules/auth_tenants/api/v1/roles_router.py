from __future__ import annotations

from fastapi import APIRouter, Depends

from src.modules.auth_tenants.api.deps import (
    Repositories,
    get_current_user,
    get_repositories,
    require_permission,
)
from src.modules.auth_tenants.application.dto import (
    PermissionSummary,
    RoleSummary,
    UpdateRolePermissionsInput,
)
from src.modules.auth_tenants.application.use_cases.role_use_cases import (
    ListPermissions,
    ListRoles,
    UpdateRolePermissions,
)
from src.modules.auth_tenants.domain.entities import User

router = APIRouter(tags=["roles"])

ROLES_MANAGE = require_permission("roles:manage")


@router.get("/roles", response_model=list[RoleSummary], dependencies=[Depends(ROLES_MANAGE)])
async def list_roles(
    user: User = Depends(get_current_user), repos: Repositories = Depends(get_repositories)
) -> list[RoleSummary]:
    assert user.tenant_id is not None
    return await ListRoles(repos.roles, repos.permissions).execute(user.tenant_id)


@router.patch(
    "/roles/{role_code}/permissions", status_code=204, dependencies=[Depends(ROLES_MANAGE)]
)
async def update_role_permissions(
    role_code: str,
    payload: UpdateRolePermissionsInput,
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
) -> None:
    await UpdateRolePermissions(repos.roles, repos.permissions, repos.audit).execute(
        user, role_code, payload
    )


@router.get(
    "/permissions", response_model=list[PermissionSummary], dependencies=[Depends(ROLES_MANAGE)]
)
async def list_permissions(
    repos: Repositories = Depends(get_repositories),
) -> list[PermissionSummary]:
    return await ListPermissions(repos.permissions).execute()
