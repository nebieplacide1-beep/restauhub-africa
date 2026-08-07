from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.modules.auth_tenants.api.deps import (
    Repositories,
    client_ip,
    get_access_claims,
    get_clock,
    get_current_user,
    get_hasher,
    get_public_repositories,
    get_repositories,
    get_token_service,
    get_two_factor_service,
)
from src.modules.auth_tenants.application.dto import (
    ConfirmTwoFactorInput,
    ConfirmTwoFactorOutput,
    DisableTwoFactorInput,
    EnableTwoFactorOutput,
    LoginInput,
    RefreshTokenInput,
    TokenPair,
    TwoFactorChallenge,
    VerifyTwoFactorInput,
)
from src.modules.auth_tenants.application.ports import (
    AccessTokenClaims,
    Clock,
    Hasher,
    TokenService,
    TwoFactorService,
)
from src.modules.auth_tenants.application.use_cases.auth_use_cases import (
    GetCurrentUser,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    VerifyTwoFactorChallenge,
)
from src.modules.auth_tenants.application.use_cases.two_factor_use_cases import (
    ConfirmTwoFactor,
    DisableTwoFactor,
    EnableTwoFactor,
)
from src.modules.auth_tenants.domain.entities import User
from src.shared_kernel.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=None)
async def login(
    payload: LoginInput,
    request: Request,
    repos: Repositories = Depends(get_public_repositories),
    hasher: Hasher = Depends(get_hasher),
    token_service: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
) -> TokenPair | TwoFactorChallenge:
    settings = get_settings()
    use_case = LoginUser(
        repos.users,
        repos.tenants,
        repos.roles,
        repos.permissions,
        repos.refresh_tokens,
        hasher,
        token_service,
        clock,
        repos.audit,
        max_failed_attempts=settings.failed_login_max_attempts,
        lockout_minutes=settings.failed_login_lockout_minutes,
        refresh_token_ttl_days=settings.jwt_refresh_token_ttl_days,
        access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes,
    )
    return await use_case.execute(payload, ip_address=client_ip(request))


@router.post("/2fa/verify", response_model=TokenPair)
async def verify_two_factor(
    payload: VerifyTwoFactorInput,
    repos: Repositories = Depends(get_public_repositories),
    token_service: TokenService = Depends(get_token_service),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    clock: Clock = Depends(get_clock),
) -> TokenPair:
    settings = get_settings()
    use_case = VerifyTwoFactorChallenge(
        repos.users,
        repos.two_factor,
        repos.roles,
        repos.permissions,
        repos.refresh_tokens,
        two_factor_service,
        token_service,
        clock,
        repos.audit,
        refresh_token_ttl_days=settings.jwt_refresh_token_ttl_days,
        access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes,
    )
    return await use_case.execute(payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshTokenInput,
    repos: Repositories = Depends(get_public_repositories),
    token_service: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
) -> TokenPair:
    settings = get_settings()
    use_case = RefreshAccessToken(
        repos.users,
        repos.roles,
        repos.permissions,
        repos.refresh_tokens,
        token_service,
        clock,
        repos.audit,
        refresh_token_ttl_days=settings.jwt_refresh_token_ttl_days,
        access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes,
    )
    return await use_case.execute(payload)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshTokenInput,
    claims: AccessTokenClaims = Depends(get_access_claims),
    repos: Repositories = Depends(get_repositories),
) -> None:
    await LogoutUser(repos.refresh_tokens, repos.audit).execute(
        payload.refresh_token, user_id=claims.user_id, tenant_id=claims.tenant_id
    )


@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
):
    return await GetCurrentUser(repos.roles, repos.permissions).execute(user)


@router.post("/2fa/enable", response_model=EnableTwoFactorOutput)
async def enable_two_factor(
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> EnableTwoFactorOutput:
    return await EnableTwoFactor(repos.two_factor, two_factor_service).execute(user)


@router.post("/2fa/confirm", response_model=ConfirmTwoFactorOutput)
async def confirm_two_factor(
    payload: ConfirmTwoFactorInput,
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
) -> ConfirmTwoFactorOutput:
    return await ConfirmTwoFactor(
        repos.two_factor, repos.users, two_factor_service, repos.audit
    ).execute(user, payload)


@router.post("/2fa/disable", status_code=204)
async def disable_two_factor(
    payload: DisableTwoFactorInput,
    user: User = Depends(get_current_user),
    repos: Repositories = Depends(get_repositories),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    hasher: Hasher = Depends(get_hasher),
) -> None:
    await DisableTwoFactor(
        repos.two_factor, repos.users, two_factor_service, hasher, repos.audit
    ).execute(user, payload)
