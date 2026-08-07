from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Réutilise directement les dépendances/ports du Module 1 (auth, session,
# Clock, AuditRecorder), voir docs/modules/02-restaurants-succursales/03-architecture.md#33.
from src.modules.auth_tenants.api.deps import (
    get_clock,
    get_current_user,
    get_request_db_session,
    require_permission,
)
from src.modules.auth_tenants.application.ports import AuditRecorder, Clock
from src.modules.auth_tenants.domain.entities import User
from src.modules.auth_tenants.domain.repositories import RoleRepository, UserRepository
from src.modules.auth_tenants.infrastructure.audit_recorder import SqlAlchemyAuditRecorder
from src.modules.succursales.api.deps import (
    SUCCURSALES_MANAGE,
    get_role_repository,
    get_succursale_repository,
    get_user_repository,
)
from src.modules.succursales.application.dto import (
    AssignStaffInput,
    CreateSuccursaleInput,
    RemoveStaffInput,
    StaffMember,
    SuccursaleSummary,
    UpdateSuccursaleInput,
)
from src.modules.succursales.application.use_cases.staffing_use_cases import (
    AssignEmployeeToSuccursale,
    ListStaff,
    RemoveStaffAssignment,
)
from src.modules.succursales.application.use_cases.succursale_use_cases import (
    CreateSuccursale,
    DeactivateSuccursale,
    GetSuccursale,
    ListSuccursales,
    ReactivateSuccursale,
    UpdateSuccursale,
)
from src.modules.succursales.domain.repositories import SuccursaleRepository

router = APIRouter(prefix="/succursales", tags=["succursales"])

MANAGE = require_permission(SUCCURSALES_MANAGE)


async def get_audit_recorder(
    session: AsyncSession = Depends(get_request_db_session),
) -> AuditRecorder:
    return SqlAlchemyAuditRecorder(session)


@router.get("", response_model=list[SuccursaleSummary], dependencies=[Depends(MANAGE)])
async def list_succursales(
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
) -> list[SuccursaleSummary]:
    return await ListSuccursales(succursales, roles).execute(user)


@router.post("", response_model=SuccursaleSummary, status_code=201, dependencies=[Depends(MANAGE)])
async def create_succursale(
    payload: CreateSuccursaleInput,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    clock: Clock = Depends(get_clock),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> SuccursaleSummary:
    return await CreateSuccursale(succursales, roles, clock, audit).execute(user, payload)


@router.get("/{succursale_id}", response_model=SuccursaleSummary, dependencies=[Depends(MANAGE)])
async def get_succursale(
    succursale_id: UUID,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
) -> SuccursaleSummary:
    return await GetSuccursale(succursales, roles).execute(user, succursale_id)


@router.patch("/{succursale_id}", response_model=SuccursaleSummary, dependencies=[Depends(MANAGE)])
async def update_succursale(
    succursale_id: UUID,
    payload: UpdateSuccursaleInput,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> SuccursaleSummary:
    return await UpdateSuccursale(succursales, roles, audit).execute(user, succursale_id, payload)


@router.post("/{succursale_id}/deactivate", status_code=204, dependencies=[Depends(MANAGE)])
async def deactivate_succursale(
    succursale_id: UUID,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    await DeactivateSuccursale(succursales, roles, audit).execute(user, succursale_id)


@router.post("/{succursale_id}/reactivate", status_code=204, dependencies=[Depends(MANAGE)])
async def reactivate_succursale(
    succursale_id: UUID,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    await ReactivateSuccursale(succursales, roles, audit).execute(user, succursale_id)


@router.get(
    "/{succursale_id}/staff", response_model=list[StaffMember], dependencies=[Depends(MANAGE)]
)
async def list_staff(
    succursale_id: UUID,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    users: UserRepository = Depends(get_user_repository),
) -> list[StaffMember]:
    return await ListStaff(succursales, roles, users).execute(user, succursale_id)


@router.post("/{succursale_id}/staff", status_code=204, dependencies=[Depends(MANAGE)])
async def assign_staff(
    succursale_id: UUID,
    payload: AssignStaffInput,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    users: UserRepository = Depends(get_user_repository),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    await AssignEmployeeToSuccursale(succursales, roles, users, audit).execute(
        user, succursale_id, payload
    )


@router.post("/{succursale_id}/staff/remove", status_code=204, dependencies=[Depends(MANAGE)])
async def remove_staff(
    succursale_id: UUID,
    payload: RemoveStaffInput,
    user: User = Depends(get_current_user),
    succursales: SuccursaleRepository = Depends(get_succursale_repository),
    roles: RoleRepository = Depends(get_role_repository),
    audit: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    await RemoveStaffAssignment(succursales, roles, audit).execute(user, succursale_id, payload)
