"""Vérifie la règle absolue de l'AMD (section 5) au niveau base de données :
même une requête applicative qui « oublierait » de filtrer par tenant_id ne
peut pas lire les données d'un autre tenant, grâce à la Row-Level Security
(docs/modules/01-auth-tenants/03-architecture.md#isolation-multi-tenant).
"""

from uuid import uuid4

import pytest

from src.modules.auth_tenants.infrastructure.db.models import UserModel
from src.shared_kernel.db.session import auth_lookup_session, tenant_scoped_session


async def _create_tenant_and_user(*, tenant_name: str, email: str):
    from src.modules.auth_tenants.application.dto import RegisterTenantInput
    from src.modules.auth_tenants.application.use_cases.tenant_use_cases import RegisterTenant
    from src.modules.auth_tenants.infrastructure.clock import SystemClock
    from src.modules.auth_tenants.infrastructure.db.repositories import (
        SqlAlchemyRoleRepository,
        SqlAlchemyTenantRepository,
        SqlAlchemyUserRepository,
    )
    from src.modules.auth_tenants.infrastructure.security.argon2_hasher import Argon2Hasher
    from src.tests.fakes import FakeAuditRecorder

    async with auth_lookup_session() as session:
        use_case = RegisterTenant(
            SqlAlchemyTenantRepository(session),
            SqlAlchemyUserRepository(session),
            SqlAlchemyRoleRepository(session),
            Argon2Hasher(),
            SystemClock(),
            FakeAuditRecorder(),
        )
        result = await use_case.execute(
            RegisterTenantInput(
                tenant_name=tenant_name,
                country="CI",
                default_currency="XOF",
                default_locale="fr",
                admin_email=email,
                admin_password="Str0ng!Passw0rd",
            )
        )
    return result.tenant.id, result.user_id


@pytest.mark.asyncio
async def test_a_tenant_scoped_session_cannot_read_another_tenants_user() -> None:
    tenant_a_id, _ = await _create_tenant_and_user(
        tenant_name=f"Tenant A {uuid4()}", email=f"a-{uuid4()}@test.ci"
    )
    tenant_b_id, user_b_id = await _create_tenant_and_user(
        tenant_name=f"Tenant B {uuid4()}", email=f"b-{uuid4()}@test.ci"
    )

    # Requête volontairement "buguée" : elle cible directement l'ID de
    # l'utilisateur du tenant B, sans filtrer par tenant_id — exactement le
    # scénario qu'une policy RLS doit intercepter.
    async with tenant_scoped_session(tenant_id=tenant_a_id) as session:
        leaked = await session.get(UserModel, user_b_id)

    assert leaked is None, "La RLS a laissé fuiter un utilisateur d'un autre tenant"

    # Contrôle positif : le même utilisateur reste lisible depuis son propre tenant.
    async with tenant_scoped_session(tenant_id=tenant_b_id) as session:
        found = await session.get(UserModel, user_b_id)
    assert found is not None
    assert found.tenant_id == tenant_b_id
