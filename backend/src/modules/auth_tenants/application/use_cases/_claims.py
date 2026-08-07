"""Helper partagé par les use cases d'authentification pour construire les
claims du token d'accès (rôles + permissions effectives, BR-14)."""

from __future__ import annotations

from src.modules.auth_tenants.application.ports import AccessTokenClaims
from src.modules.auth_tenants.domain.entities import RoleCode, User
from src.modules.auth_tenants.domain.repositories import PermissionRepository, RoleRepository
from src.modules.auth_tenants.domain.services import PermissionResolver


async def build_access_claims(
    user: User, role_repository: RoleRepository, permission_repository: PermissionRepository
) -> AccessTokenClaims:
    roles = await role_repository.get_roles_for_user(user.id)
    is_super_admin = any(r.code == RoleCode.SUPER_ADMINISTRATEUR for r in roles)

    defaults = await permission_repository.get_default_permissions_by_role()
    overrides = (
        {}
        if is_super_admin or user.tenant_id is None
        else await permission_repository.get_tenant_overrides_by_role(user.tenant_id)
    )
    permissions = PermissionResolver.resolve(
        role_ids=[r.id for r in roles],
        default_permissions_by_role=defaults,
        tenant_overrides_by_role=overrides,
    )

    return AccessTokenClaims(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role_codes=[r.code.value for r in roles],
        permissions=sorted(permissions),
        is_super_admin=is_super_admin,
    )
