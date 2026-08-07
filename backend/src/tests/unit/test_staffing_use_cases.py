from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.auth_tenants.domain.entities import Role, RoleCode, User
from src.modules.auth_tenants.domain.exceptions import UserNotFoundError
from src.modules.succursales.application.dto import AssignStaffInput, RemoveStaffInput
from src.modules.succursales.application.use_cases.staffing_use_cases import (
    AssignEmployeeToSuccursale,
    ListStaff,
    RemoveStaffAssignment,
)
from src.modules.succursales.domain.entities import OpeningHours, Succursale, SuccursaleStatus
from src.modules.succursales.domain.exceptions import StaffAssignmentAlreadyExistsError
from src.shared_kernel.exceptions import ForbiddenError
from src.tests.fakes import (
    FakeAuditRecorder,
    FakeRoleRepository,
    FakeSuccursaleRepository,
    FakeUserRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _setup():
    tenant_id = uuid4()
    admin = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="admin@chezawa.ci",
        phone_number=None,
        password_hash="x",
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )
    employee = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="serveur@chezawa.ci",
        phone_number=None,
        password_hash="x",
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )
    users = FakeUserRepository()
    users.by_id[admin.id] = admin
    users.by_id[employee.id] = employee

    roles = FakeRoleRepository(
        [
            Role(id=uuid4(), code=RoleCode.ADMINISTRATEUR, label="Administrateur"),
            Role(id=uuid4(), code=RoleCode.SERVEUR, label="Serveur"),
        ]
    )
    admin_role_id = next(r.id for r in roles.roles.values() if r.code == RoleCode.ADMINISTRATEUR)
    roles.assignments[admin.id] = {(admin_role_id, None)}

    succursales = FakeSuccursaleRepository()
    succursale = Succursale(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Chez Awa",
        address_line="A",
        city="Abidjan",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    succursales.by_id[succursale.id] = succursale

    return admin, employee, users, roles, succursales, succursale


@pytest.mark.asyncio
async def test_assign_employee_to_succursale() -> None:
    admin, employee, users, roles, succursales, succursale = _setup()
    audit = FakeAuditRecorder()

    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        admin, succursale.id, AssignStaffInput(user_id=employee.id, role_code="serveur")
    )

    staff = await ListStaff(succursales, roles, users).execute(admin, succursale.id)
    assert len(staff) == 1
    assert staff[0].user_id == employee.id
    assert staff[0].role_codes == ["serveur"]


@pytest.mark.asyncio
async def test_assigning_narrows_a_pre_existing_tenant_wide_grant_of_the_same_role() -> None:
    """Reproduit le scénario réel : une invitation (Module 1) accorde le rôle
    tenant-wide par défaut ; le rattacher ensuite à une succursale doit
    restreindre l'accès, pas l'ajouter en plus (sans quoi BR2-09 ne
    s'appliquerait jamais après une invitation — bug trouvé par le test
    bout-en-bout tests/api/test_succursales_flow.py)."""
    admin, employee, users, roles, succursales, succursale = _setup()
    serveur_role_id = next(r.id for r in roles.roles.values() if r.code == RoleCode.SERVEUR)
    # accordé tenant-wide par l'invitation
    roles.assignments[employee.id] = {(serveur_role_id, None)}

    await AssignEmployeeToSuccursale(succursales, roles, users, FakeAuditRecorder()).execute(
        admin, succursale.id, AssignStaffInput(user_id=employee.id, role_code="serveur")
    )

    scope_ids = await roles.get_succursale_ids_for_user(employee.id)
    assert scope_ids == [succursale.id], "le rattachement tenant-wide aurait dû être retiré"


@pytest.mark.asyncio
async def test_assign_same_role_twice_raises_conflict() -> None:
    admin, employee, users, roles, succursales, succursale = _setup()
    audit = FakeAuditRecorder()
    payload = AssignStaffInput(user_id=employee.id, role_code="serveur")

    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        admin, succursale.id, payload
    )
    with pytest.raises(StaffAssignmentAlreadyExistsError):
        await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
            admin, succursale.id, payload
        )


@pytest.mark.asyncio
async def test_assign_unknown_user_raises_not_found() -> None:
    admin, _employee, users, roles, succursales, succursale = _setup()
    with pytest.raises(UserNotFoundError):
        await AssignEmployeeToSuccursale(succursales, roles, users, FakeAuditRecorder()).execute(
            admin, succursale.id, AssignStaffInput(user_id=uuid4(), role_code="serveur")
        )


@pytest.mark.asyncio
async def test_same_employee_can_be_assigned_same_role_at_two_succursales() -> None:
    """BR2-10 — la raison d'être du correctif de clé primaire sur user_roles."""
    admin, employee, users, roles, succursales, succursale_a = _setup()
    succursale_b = Succursale(
        id=uuid4(),
        tenant_id=succursale_a.tenant_id,
        name="Chez Awa 2",
        address_line="B",
        city="Abidjan",
        country="CI",
        default_currency="XOF",
        default_locale="fr",
        status=SuccursaleStatus.ACTIVE,
        opening_hours=OpeningHours({}),
        created_at=NOW,
    )
    succursales.by_id[succursale_b.id] = succursale_b
    audit = FakeAuditRecorder()
    payload = AssignStaffInput(user_id=employee.id, role_code="serveur")

    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        admin, succursale_a.id, payload
    )
    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        admin, succursale_b.id, payload
    )

    staff_a = await ListStaff(succursales, roles, users).execute(admin, succursale_a.id)
    staff_b = await ListStaff(succursales, roles, users).execute(admin, succursale_b.id)
    assert len(staff_a) == 1 and len(staff_b) == 1


@pytest.mark.asyncio
async def test_remove_staff_assignment() -> None:
    admin, employee, users, roles, succursales, succursale = _setup()
    audit = FakeAuditRecorder()
    payload = AssignStaffInput(user_id=employee.id, role_code="serveur")
    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        admin, succursale.id, payload
    )

    await RemoveStaffAssignment(succursales, roles, audit).execute(
        admin, succursale.id, RemoveStaffInput(user_id=employee.id, role_code="serveur")
    )

    staff = await ListStaff(succursales, roles, users).execute(admin, succursale.id)
    assert staff == []
    # BR2-12 : le compte reste actif malgré le retrait du rattachement.
    assert (await users.get_by_id(employee.id)).is_active is True


@pytest.mark.asyncio
async def test_staffing_action_outside_scope_is_forbidden() -> None:
    admin, employee, users, roles, succursales, succursale = _setup()
    gerant = User(
        id=uuid4(),
        tenant_id=admin.tenant_id,
        email="gerant@chezawa.ci",
        phone_number=None,
        password_hash="x",
        is_active=True,
        two_factor_enabled=False,
        created_at=NOW,
    )
    users.by_id[gerant.id] = gerant
    gerant_role_id = next(iter(roles.roles))
    roles.assignments[gerant.id] = {(gerant_role_id, uuid4())}  # rattaché à une AUTRE succursale

    with pytest.raises(ForbiddenError):
        await AssignEmployeeToSuccursale(succursales, roles, users, FakeAuditRecorder()).execute(
            gerant, succursale.id, AssignStaffInput(user_id=employee.id, role_code="serveur")
        )
