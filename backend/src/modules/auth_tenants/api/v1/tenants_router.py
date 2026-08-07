from __future__ import annotations

from fastapi import APIRouter, Depends

from src.modules.auth_tenants.api.deps import (
    Repositories,
    get_clock,
    get_hasher,
    get_public_repositories,
)
from src.modules.auth_tenants.application.dto import RegisterTenantInput, RegisterTenantOutput
from src.modules.auth_tenants.application.ports import Clock, Hasher
from src.modules.auth_tenants.application.use_cases.tenant_use_cases import RegisterTenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=RegisterTenantOutput, status_code=201)
async def register_tenant(
    payload: RegisterTenantInput,
    repos: Repositories = Depends(get_public_repositories),
    hasher: Hasher = Depends(get_hasher),
    clock: Clock = Depends(get_clock),
) -> RegisterTenantOutput:
    use_case = RegisterTenant(repos.tenants, repos.users, repos.roles, hasher, clock, repos.audit)
    return await use_case.execute(payload)
