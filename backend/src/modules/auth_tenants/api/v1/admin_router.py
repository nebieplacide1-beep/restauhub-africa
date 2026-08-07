from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.modules.auth_tenants.api.deps import Repositories, get_repositories, require_super_admin
from src.modules.auth_tenants.application.dto import TenantSummary
from src.modules.auth_tenants.application.use_cases.tenant_use_cases import (
    ListTenants,
    ReactivateTenant,
    SuspendTenant,
)
from src.modules.auth_tenants.domain.exceptions import TenantNotFoundError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_super_admin)])


@router.get("/tenants", response_model=list[TenantSummary])
async def list_tenants(
    status: str | None = None, repos: Repositories = Depends(get_repositories)
) -> list[TenantSummary]:
    return await ListTenants(repos.tenants).execute(status=status)


@router.get("/tenants/{tenant_id}", response_model=TenantSummary)
async def get_tenant(
    tenant_id: UUID, repos: Repositories = Depends(get_repositories)
) -> TenantSummary:
    tenant = await repos.tenants.get_by_id(tenant_id)
    if tenant is None:
        raise TenantNotFoundError()
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status.value,
        country=tenant.country,
        created_at=tenant.created_at,
    )


@router.post("/tenants/{tenant_id}/suspend", status_code=204)
async def suspend_tenant(tenant_id: UUID, repos: Repositories = Depends(get_repositories)) -> None:
    await SuspendTenant(repos.tenants, repos.audit).execute(tenant_id)


@router.post("/tenants/{tenant_id}/reactivate", status_code=204)
async def reactivate_tenant(
    tenant_id: UUID, repos: Repositories = Depends(get_repositories)
) -> None:
    await ReactivateTenant(repos.tenants, repos.audit).execute(tenant_id)
