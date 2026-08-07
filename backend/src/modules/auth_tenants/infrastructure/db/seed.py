"""Données de référence du Module 1 : les 12 rôles système (BR-20) et la
matrice de permissions par défaut
(docs/modules/01-auth-tenants/02-regles-metier.md#matrice-des-permissions-par-défaut).

Idempotent, rejouable sans risque. Exécuté par `scripts/seed_reference_data.py`
après `alembic upgrade head` — volontairement séparé de la migration de
schéma (voir `alembic/versions/0001_initial_auth_tenants.py`).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth_tenants.domain.entities import RoleCode
from src.modules.auth_tenants.infrastructure.db.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)

ROLE_LABELS: dict[RoleCode, str] = {
    RoleCode.CLIENT: "Client",
    RoleCode.SERVEUR: "Serveur",
    RoleCode.CUISINE: "Cuisine",
    RoleCode.CAISSIER: "Caissier",
    RoleCode.GERANT: "Gérant",
    RoleCode.PDG: "PDG",
    RoleCode.COMPTABLE: "Comptable",
    RoleCode.LIVREUR: "Livreur",
    RoleCode.ANNONCEUR: "Annonceur",
    RoleCode.FOURNISSEUR: "Fournisseur",
    RoleCode.ADMINISTRATEUR: "Administrateur",
    RoleCode.SUPER_ADMINISTRATEUR: "Super Administrateur",
}

# (code, domaine, action)
PERMISSION_CATALOG: list[tuple[str, str, str]] = [
    ("commandes:read", "commandes", "read"),
    ("commandes:write", "commandes", "write"),
    ("reservations:read", "reservations", "read"),
    ("reservations:write", "reservations", "write"),
    ("fidelite:read", "fidelite", "read"),
    ("avis:write", "avis", "write"),
    ("tables:read", "tables", "read"),
    ("tables:write", "tables", "write"),
    ("paiements:read", "paiements", "read"),
    ("paiements:write", "paiements", "write"),
    ("caisse:read", "caisse", "read"),
    ("caisse:write", "caisse", "write"),
    ("personnel:read", "personnel", "read"),
    ("personnel:write", "personnel", "write"),
    ("stocks:read", "stocks", "read"),
    ("stocks:write", "stocks", "write"),
    ("produits:read", "produits", "read"),
    ("produits:write", "produits", "write"),
    ("promotions:read", "promotions", "read"),
    ("promotions:write", "promotions", "write"),
    ("rapports:read", "rapports", "read"),
    ("finance:read", "finance", "read"),
    ("finance:write", "finance", "write"),
    ("factures:read", "factures", "read"),
    ("factures:write", "factures", "write"),
    ("livraisons:read", "livraisons", "read"),
    ("livraisons:write", "livraisons", "write"),
    ("publicites:read", "publicites", "read"),
    ("publicites:write", "publicites", "write"),
    ("marketplace:read", "marketplace", "read"),
    ("marketplace:write", "marketplace", "write"),
    ("users:manage", "users", "manage"),
    ("roles:manage", "roles", "manage"),
    ("parametres:manage", "parametres", "manage"),
    ("abonnement:manage", "abonnement", "manage"),
    ("platform:admin", "platform", "admin"),
    # Module 2 (Restaurants & succursales) — géré ici pour que le catalogue de
    # permissions reste une source unique, même si le seed applicatif vit dans
    # le Module 1 (voir docs/modules/02-restaurants-succursales/06-api-specification.md).
    ("succursales:manage", "succursales", "manage"),
]

ROLE_DEFAULT_PERMISSIONS: dict[RoleCode, list[str]] = {
    RoleCode.CLIENT: [
        "commandes:read",
        "commandes:write",
        "reservations:read",
        "reservations:write",
        "fidelite:read",
        "avis:write",
    ],
    RoleCode.SERVEUR: ["commandes:read", "commandes:write", "tables:read", "tables:write"],
    RoleCode.CUISINE: ["commandes:read", "commandes:write"],
    RoleCode.CAISSIER: [
        "commandes:read",
        "paiements:read",
        "paiements:write",
        "caisse:read",
        "caisse:write",
    ],
    RoleCode.GERANT: [
        "personnel:read",
        "personnel:write",
        "stocks:read",
        "stocks:write",
        "produits:read",
        "produits:write",
        "promotions:read",
        "promotions:write",
        "rapports:read",
        "succursales:manage",
    ],
    RoleCode.PDG: ["rapports:read", "finance:read", "succursales:manage"],
    RoleCode.COMPTABLE: [
        "finance:read",
        "finance:write",
        "factures:read",
        "factures:write",
        "rapports:read",
    ],
    RoleCode.LIVREUR: ["livraisons:read", "livraisons:write"],
    RoleCode.ANNONCEUR: ["publicites:read", "publicites:write"],
    RoleCode.FOURNISSEUR: ["marketplace:read", "marketplace:write"],
    RoleCode.ADMINISTRATEUR: [
        "users:manage",
        "roles:manage",
        "parametres:manage",
        "abonnement:manage",
        "rapports:read",
        "succursales:manage",
    ],
    RoleCode.SUPER_ADMINISTRATEUR: ["platform:admin"],
}


async def seed_roles_and_permissions(session: AsyncSession) -> None:
    role_ids: dict[RoleCode, uuid.UUID] = {}
    for code, label in ROLE_LABELS.items():
        stmt = (
            pg_insert(RoleModel)
            .values(id=uuid.uuid4(), code=code.value, label=label, is_system_role=True)
            .on_conflict_do_nothing(index_elements=["code"])
        )
        await session.execute(stmt)

    result = await session.execute(select(RoleModel))
    for model in result.scalars().all():
        role_ids[RoleCode(model.code)] = model.id

    permission_ids: dict[str, uuid.UUID] = {}
    for code, domain, action in PERMISSION_CATALOG:
        stmt = (
            pg_insert(PermissionModel)
            .values(id=uuid.uuid4(), code=code, domain=domain, action=action)
            .on_conflict_do_nothing(index_elements=["code"])
        )
        await session.execute(stmt)

    result = await session.execute(select(PermissionModel))
    for model in result.scalars().all():
        permission_ids[model.code] = model.id

    for role_code, permission_codes in ROLE_DEFAULT_PERMISSIONS.items():
        for permission_code in permission_codes:
            stmt = (
                pg_insert(RolePermissionModel)
                .values(
                    id=uuid.uuid4(),
                    tenant_id=None,
                    role_id=role_ids[role_code],
                    permission_id=permission_ids[permission_code],
                )
                .on_conflict_do_nothing(constraint="uq_role_permission_scope")
            )
            await session.execute(stmt)

    await session.flush()
