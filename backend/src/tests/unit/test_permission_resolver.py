from uuid import uuid4

from src.modules.auth_tenants.domain.services import PermissionResolver


def test_uses_default_when_no_override() -> None:
    role_id = uuid4()
    result = PermissionResolver.resolve(
        role_ids=[role_id],
        default_permissions_by_role={role_id: {"commandes:read"}},
        tenant_overrides_by_role={},
    )
    assert result == {"commandes:read"}


def test_tenant_override_replaces_default_for_that_role() -> None:
    role_id = uuid4()
    result = PermissionResolver.resolve(
        role_ids=[role_id],
        default_permissions_by_role={role_id: {"commandes:read"}},
        tenant_overrides_by_role={role_id: {"commandes:read", "commandes:write"}},
    )
    assert result == {"commandes:read", "commandes:write"}


def test_union_across_multiple_roles() -> None:
    role_a, role_b = uuid4(), uuid4()
    result = PermissionResolver.resolve(
        role_ids=[role_a, role_b],
        default_permissions_by_role={role_a: {"commandes:read"}, role_b: {"caisse:write"}},
        tenant_overrides_by_role={},
    )
    assert result == {"commandes:read", "caisse:write"}
