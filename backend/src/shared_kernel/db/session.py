"""Gestion des sessions SQLAlchemy async et du contexte d'isolation tenant.

Le paramètre de session PostgreSQL `app.tenant_id` (et `app.is_super_admin`)
est positionné à chaque requête par `TenantScopedSession` ; les policies RLS
définies dans la migration Alembic s'appuient dessus pour garantir qu'aucune
requête ne peut lire ou écrire les données d'un autre tenant, même en cas
d'oubli d'un filtre applicatif (défense en profondeur, voir
docs/modules/01-auth-tenants/03-architecture.md#isolation-multi-tenant).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.shared_kernel.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def _apply_tenant_context(
    session: AsyncSession, *, tenant_id: UUID | None, is_super_admin: bool, auth_lookup: bool
) -> None:
    """Positionne les GUC PostgreSQL lus par les policies RLS.

    `set_config(..., is_local=True)` limite la portée à la transaction
    courante : aucun risque de fuite d'un contexte tenant vers la requête
    suivante sur une connexion réutilisée par le pool.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id) if tenant_id else ""},
    )
    await session.execute(
        text("SELECT set_config('app.is_super_admin', :flag, true)"),
        {"flag": "true" if is_super_admin else "false"},
    )
    await session.execute(
        text("SELECT set_config('app.auth_lookup', :flag, true)"),
        {"flag": "true" if auth_lookup else "false"},
    )


@asynccontextmanager
async def tenant_scoped_session(
    *, tenant_id: UUID | None, is_super_admin: bool = False
) -> AsyncIterator[AsyncSession]:
    """Ouvre une session dont toutes les requêtes sont bornées à `tenant_id`.

    `tenant_id=None, is_super_admin=True` est le seul cas légitime d'accès
    transverse (BR-24 : le Super Administrateur n'est jamais rattaché à un
    tenant). `tenant_id=None, is_super_admin=False` ne doit jamais arriver en
    dehors de l'inscription d'un nouveau tenant (BR-01) — dans ce cas précis,
    aucune table à `tenant_id` n'est encore concernée.
    """
    session_factory = get_session_factory()
    async with session_factory() as session, session.begin():
        await _apply_tenant_context(
            session, tenant_id=tenant_id, is_super_admin=is_super_admin, auth_lookup=False
        )
        yield session


@asynccontextmanager
async def auth_lookup_session() -> AsyncIterator[AsyncSession]:
    """Session restreinte aux lectures anonymes par identifiant/token opaque.

    Réservée aux cas d'usage de connexion (`LoginUser`) et d'invitation
    (`AcceptInvitation`, `GetInvitationPreview`), seuls endroits légitimes où
    le tenant n'est pas encore connu côté client (voir
    docs/modules/01-auth-tenants/05-modele-donnees.md#52-amendement-post-validation-implémentation-2026-08-07).
    Le GUC `app.auth_lookup` n'autorise, via les policies RLS, que la lecture
    de `users` par identifiant et d'`invitations` par token — jamais un accès
    large aux autres tables.
    """
    session_factory = get_session_factory()
    async with session_factory() as session, session.begin():
        await _apply_tenant_context(session, tenant_id=None, is_super_admin=False, auth_lookup=True)
        yield session
