"""Même vérification que test_tenant_isolation.py (Module 1), appliquée à la
table `succursales` introduite par le Module 2 — s'assure que le correctif
RLS générique (FORCE ROW LEVEL SECURITY + rôle applicatif restreint) protège
aussi les tables ajoutées après coup, pas seulement celles du Module 1."""

from uuid import uuid4

import pytest

from src.modules.succursales.infrastructure.db.models import SuccursaleModel
from src.shared_kernel.db.session import auth_lookup_session, tenant_scoped_session


async def _create_tenant_with_succursale(*, tenant_name: str, email: str):
    from src.modules.auth_tenants.application.dto import RegisterTenantInput
    from src.modules.auth_tenants.application.use_cases.tenant_use_cases import RegisterTenant
    from src.modules.auth_tenants.infrastructure.clock import SystemClock
    from src.modules.auth_tenants.infrastructure.db.repositories import (
        SqlAlchemyRoleRepository,
        SqlAlchemyTenantRepository,
        SqlAlchemyUserRepository,
    )
    from src.modules.auth_tenants.infrastructure.security.argon2_hasher import Argon2Hasher
    from src.modules.succursales.application.dto import CreateSuccursaleInput
    from src.modules.succursales.application.use_cases.succursale_use_cases import CreateSuccursale
    from src.modules.succursales.infrastructure.db.repositories import (
        SqlAlchemySuccursaleRepository,
    )
    from src.tests.fakes import FakeAuditRecorder

    async with auth_lookup_session() as session:
        tenant_repo = SqlAlchemyTenantRepository(session)
        user_repo = SqlAlchemyUserRepository(session)
        role_repo = SqlAlchemyRoleRepository(session)
        result = await RegisterTenant(
            tenant_repo, user_repo, role_repo, Argon2Hasher(), SystemClock(), FakeAuditRecorder()
        ).execute(
            RegisterTenantInput(
                tenant_name=tenant_name,
                country="CI",
                default_currency="XOF",
                default_locale="fr",
                admin_email=email,
                admin_password="Str0ng!Passw0rd",
            )
        )
        admin = await user_repo.get_by_id(result.user_id)

    async with tenant_scoped_session(tenant_id=result.tenant.id) as session:
        succursale_repo = SqlAlchemySuccursaleRepository(session)
        succursale = await CreateSuccursale(
            succursale_repo, SqlAlchemyRoleRepository(session), SystemClock(), FakeAuditRecorder()
        ).execute(
            admin,
            CreateSuccursaleInput(
                name="Chez Awa",
                address_line="12 rue X",
                city="Abidjan",
                country="CI",
                default_currency="XOF",
                default_locale="fr",
            ),
        )
    return result.tenant.id, succursale.id


@pytest.mark.asyncio
async def test_a_tenant_cannot_read_another_tenants_succursale() -> None:
    tenant_a_id, _ = await _create_tenant_with_succursale(
        tenant_name=f"Tenant A {uuid4()}", email=f"a-{uuid4()}@test.ci"
    )
    tenant_b_id, succursale_b_id = await _create_tenant_with_succursale(
        tenant_name=f"Tenant B {uuid4()}", email=f"b-{uuid4()}@test.ci"
    )

    async with tenant_scoped_session(tenant_id=tenant_a_id) as session:
        leaked = await session.get(SuccursaleModel, succursale_b_id)
    assert leaked is None, "La RLS a laissé fuiter une succursale d'un autre tenant"

    async with tenant_scoped_session(tenant_id=tenant_b_id) as session:
        found = await session.get(SuccursaleModel, succursale_b_id)
    assert found is not None and found.tenant_id == tenant_b_id
