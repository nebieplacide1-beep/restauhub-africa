from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.domain.entities import Role, RoleCode, User
from src.modules.succursales.application.dto import CreateSuccursaleInput, UpdateSuccursaleInput
from src.modules.succursales.application.use_cases.succursale_use_cases import (
    CreateSuccursale,
    ListSuccursales,
    UpdateSuccursale,
)
from src.modules.succursales.domain.entities import OpeningHours, Succursale, SuccursaleStatus
from src.shared_kernel.exceptions import ForbiddenError
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeClock,
    FakeRoleRepository,
    FakeSuccursaleRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_user(tenant_id) -> User:
    return User(
        id=uuid4(),
        tenant_id=tenant_id,
        email=f"{uuid4()}@chezawa.ci",
        phone_number=None,
        password_hash="x",
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )


def _payload(**overrides) -> CreateSuccursaleInput:
    data = {
        "name": "Chez Awa - Plateau",
        "address_line": "12 Avenue Chardy",
        "city": "Abidjan",
        "country": "ci",
        "default_currency": "xof",
        "default_locale": "fr",
    }
    data.update(overrides)
    return CreateSuccursaleInput(**data)


@pytest.mark.asyncio
async def test_tenant_wide_actor_can_create_succursale() -> None:
    tenant_id = uuid4()
    admin = _make_user(tenant_id)
    roles = FakeRoleRepository(
        [Role(id=uuid4(), code=RoleCode.ADMINISTRATEUR, label="Administrateur")]
    )
    admin_role_id = next(iter(roles.roles))
    roles.assignments[admin.id] = {(admin_role_id, None)}  # tenant-wide, BR2-08
    succursales = FakeSuccursaleRepository()

    result = await CreateSuccursale(
        succursales, roles, FakeClock(NOW), FakeAuditRecorder()
    ).execute(admin, _payload())

    assert result.country == "CI"
    assert result.default_currency == "XOF"
    assert len(succursales.by_id) == 1


@pytest.mark.asyncio
async def test_scoped_actor_cannot_create_succursale() -> None:
    tenant_id = uuid4()
    gerant = _make_user(tenant_id)
    roles = FakeRoleRepository([Role(id=uuid4(), code=RoleCode.GERANT, label="Gérant")])
    role_id = next(iter(roles.roles))
    roles.assignments[gerant.id] = {(role_id, uuid4())}  # rattaché à une succursale précise, BR2-09
    succursales = FakeSuccursaleRepository()

    with pytest.raises(ForbiddenError):
        await CreateSuccursale(succursales, roles, FakeClock(NOW), FakeAuditRecorder()).execute(
            gerant, _payload()
        )


@pytest.mark.asyncio
async def test_pdg_lists_all_tenant_succursales() -> None:
    tenant_id = uuid4()
    pdg = _make_user(tenant_id)
    roles = FakeRoleRepository([Role(id=uuid4(), code=RoleCode.PDG, label="PDG")])
    roles.assignments[pdg.id] = {(next(iter(roles.roles)), None)}
    succursales = FakeSuccursaleRepository()
    for _ in range(3):
        s = Succursale(
            id=uuid4(),
            tenant_id=tenant_id,
            name="X",
            address_line="Y",
            city="Abidjan",
            country="CI",
            default_currency="XOF",
            default_locale="fr",
            status=SuccursaleStatus.ACTIVE,
            opening_hours=OpeningHours({}),
            created_at=NOW,
        )
        succursales.by_id[s.id] = s
    # une succursale d'un autre tenant ne doit jamais apparaître
    other = Succursale(
        id=uuid4(),
        tenant_id=uuid4(),
        name="Autre",
        address_line="Z",
        city="Dakar",
        country="SN",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    succursales.by_id[other.id] = other

    result = await ListSuccursales(succursales, roles).execute(pdg)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_gerant_only_lists_assigned_succursale() -> None:
    tenant_id = uuid4()
    gerant = _make_user(tenant_id)
    roles = FakeRoleRepository([Role(id=uuid4(), code=RoleCode.GERANT, label="Gérant")])
    role_id = next(iter(roles.roles))
    succursales = FakeSuccursaleRepository()
    assigned = Succursale(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Assignée",
        address_line="A",
        city="Abidjan",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    not_assigned = Succursale(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Autre succursale",
        address_line="B",
        city="Abidjan",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    succursales.by_id[assigned.id] = assigned
    succursales.by_id[not_assigned.id] = not_assigned
    roles.assignments[gerant.id] = {(role_id, assigned.id)}

    result = await ListSuccursales(succursales, roles).execute(gerant)
    assert [s.id for s in result] == [assigned.id]


@pytest.mark.asyncio
async def test_update_rejected_outside_scope() -> None:
    tenant_id = uuid4()
    gerant = _make_user(tenant_id)
    roles = FakeRoleRepository([Role(id=uuid4(), code=RoleCode.GERANT, label="Gérant")])
    role_id = next(iter(roles.roles))
    succursales = FakeSuccursaleRepository()
    other_succursale = Succursale(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Pas la mienne",
        address_line="A",
        city="Abidjan",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    succursales.by_id[other_succursale.id] = other_succursale
    roles.assignments[gerant.id] = {(role_id, uuid4())}  # rattaché ailleurs

    with pytest.raises(ForbiddenError):
        await UpdateSuccursale(succursales, roles, FakeAuditRecorder()).execute(
            gerant, other_succursale.id, UpdateSuccursaleInput(name="Hack")
        )
