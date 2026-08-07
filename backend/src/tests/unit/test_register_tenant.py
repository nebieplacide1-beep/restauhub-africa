from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.application.dto import RegisterTenantInput
from src.modules.auth_tenants.application.use_cases.tenant_use_cases import RegisterTenant
from src.modules.auth_tenants.domain.entities import Role, RoleCode
from src.modules.auth_tenants.domain.exceptions import IdentifierAlreadyUsedError
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeClock,
    FakeHasher,
    FakeRoleRepository,
    FakeTenantRepository,
    FakeUserRepository,
)


def _build_use_case() -> tuple[
    RegisterTenant, FakeTenantRepository, FakeUserRepository, FakeRoleRepository
]:
    tenants = FakeTenantRepository()
    users = FakeUserRepository()
    roles = FakeRoleRepository(
        [Role(id=uuid4(), code=RoleCode.ADMINISTRATEUR, label="Administrateur")]
    )
    use_case = RegisterTenant(
        tenants,
        users,
        roles,
        FakeHasher(),
        FakeClock(datetime(2026, 1, 1, tzinfo=UTC)),
        FakeAuditRecorder(),
    )
    return use_case, tenants, users, roles


@pytest.mark.asyncio
async def test_register_tenant_creates_tenant_and_admin_user() -> None:
    use_case, _tenants, users, roles = _build_use_case()

    result = await use_case.execute(
        RegisterTenantInput(
            tenant_name="Le Bon Maquis",
            country="CI",
            default_currency="XOF",
            default_locale="fr",
            admin_email="owner@lebonmaquis.ci",
            admin_password="Str0ng!Passw0rd",
        )
    )

    assert result.tenant.slug == "le-bon-maquis"
    assert result.tenant.status == "en_essai"
    stored_user = users.by_id[result.user_id]
    assert stored_user.tenant_id == result.tenant.id
    assert stored_user.email == "owner@lebonmaquis.ci"
    admin_role_id = next(iter(roles.roles))
    assert admin_role_id in roles.assignments[result.user_id]


@pytest.mark.asyncio
async def test_register_tenant_deduplicates_slug() -> None:
    use_case, *_ = _build_use_case()
    await use_case.execute(
        RegisterTenantInput(
            tenant_name="Chez Awa",
            country="CI",
            default_currency="XOF",
            default_locale="fr",
            admin_email="a@chezawa.ci",
            admin_password="Str0ng!Passw0rd",
        )
    )
    second = await use_case.execute(
        RegisterTenantInput(
            tenant_name="Chez Awa",
            country="CI",
            default_currency="XOF",
            default_locale="fr",
            admin_email="b@chezawa.ci",
            admin_password="Str0ng!Passw0rd",
        )
    )
    assert second.tenant.slug == "chez-awa-2"


@pytest.mark.asyncio
async def test_register_tenant_rejects_duplicate_identifier() -> None:
    use_case, *_ = _build_use_case()
    payload = RegisterTenantInput(
        tenant_name="Chez Awa",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        admin_email="a@chezawa.ci",
        admin_password="Str0ng!Passw0rd",
    )
    await use_case.execute(payload)

    with pytest.raises(IdentifierAlreadyUsedError):
        await use_case.execute(
            RegisterTenantInput(
                tenant_name="Autre Tenant",
                country="CI",
                default_currency="XOF",
                default_locale="fr",
                admin_email="a@chezawa.ci",
                admin_password="Str0ng!Passw0rd",
            )
        )
