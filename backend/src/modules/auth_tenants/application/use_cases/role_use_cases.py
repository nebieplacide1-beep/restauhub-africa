from __future__ import annotations

from uuid import UUID

from src.modules.auth_tenants.application.dto import (
    PermissionSummary,
    RoleSummary,
    UpdateRolePermissionsInput,
)
from src.modules.auth_tenants.application.ports import AuditRecorder
from src.modules.auth_tenants.domain.entities import RoleCode, User
from src.modules.auth_tenants.domain.exceptions import ValidationError
from src.modules.auth_tenants.domain.repositories import PermissionRepository, RoleRepository
from src.modules.auth_tenants.domain.services import PermissionResolver


class ListRoles:
    """BR-20 : les 12 rôles système avec leurs permissions effectives pour le
    tenant courant (défauts + surcharges éventuelles, BR-23)."""

    def __init__(
        self, role_repository: RoleRepository, permission_repository: PermissionRepository
    ) -> None:
        self._roles = role_repository
        self._permissions = permission_repository

    async def execute(self, tenant_id: UUID) -> list[RoleSummary]:
        roles = await self._roles.list_all()
        defaults = await self._permissions.get_default_permissions_by_role()
        overrides = await self._permissions.get_tenant_overrides_by_role(tenant_id)
        return [
            RoleSummary(
                id=role.id,
                code=role.code.value,
                label=role.label,
                permissions=sorted(
                    PermissionResolver.resolve(
                        role_ids=[role.id],
                        default_permissions_by_role=defaults,
                        tenant_overrides_by_role=overrides,
                    )
                ),
            )
            for role in roles
        ]


class ListPermissions:
    def __init__(self, permission_repository: PermissionRepository) -> None:
        self._permissions = permission_repository

    async def execute(self) -> list[PermissionSummary]:
        permissions = await self._permissions.list_all()
        return [
            PermissionSummary(id=p.id, code=p.code, domain=p.domain, action=p.action)
            for p in permissions
        ]


class UpdateRolePermissions:
    """BR-23 : surcharge, pour le tenant courant, l'ensemble de permissions
    d'un rôle."""

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit: AuditRecorder,
    ) -> None:
        self._roles = role_repository
        self._permissions = permission_repository
        self._audit = audit

    async def execute(self, actor: User, role_code: str, data: UpdateRolePermissionsInput) -> None:
        role = await self._roles.get_by_code(RoleCode(role_code))
        if role is None:
            raise ValidationError(f"Rôle inconnu : {role_code!r}")

        all_permission_codes = {p.code for p in await self._permissions.list_all()}
        unknown = set(data.permission_codes) - all_permission_codes
        if unknown:
            raise ValidationError(f"Permissions inconnues : {sorted(unknown)}")

        assert actor.tenant_id is not None
        await self._permissions.set_tenant_override(
            tenant_id=actor.tenant_id, role_id=role.id, permission_codes=set(data.permission_codes)
        )
        await self._audit.record(
            action="role.permissions_updated",
            result="success",
            tenant_id=actor.tenant_id,
            user_id=actor.id,
            metadata={"role_code": role_code, "permission_codes": data.permission_codes},
        )
