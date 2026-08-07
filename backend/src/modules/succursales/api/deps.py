"""Dépendances propres au Module 2 — réutilise directement les dépendances
d'authentification/session du Module 1 (`get_current_user`, `require_permission`,
`get_request_db_session`), voir docs/modules/02-restaurants-succursales/03-architecture.md#33."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth_tenants.api.deps import get_request_db_session
from src.modules.auth_tenants.domain.repositories import RoleRepository, UserRepository
from src.modules.auth_tenants.infrastructure.db.repositories import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from src.modules.succursales.domain.repositories import SuccursaleRepository
from src.modules.succursales.infrastructure.db.repositories import SqlAlchemySuccursaleRepository

SUCCURSALES_MANAGE = "succursales:manage"


async def get_succursale_repository(
    session: AsyncSession = Depends(get_request_db_session),
) -> SuccursaleRepository:
    return SqlAlchemySuccursaleRepository(session)


async def get_role_repository(
    session: AsyncSession = Depends(get_request_db_session),
) -> RoleRepository:
    return SqlAlchemyRoleRepository(session)


async def get_user_repository(
    session: AsyncSession = Depends(get_request_db_session),
) -> UserRepository:
    return SqlAlchemyUserRepository(session)
