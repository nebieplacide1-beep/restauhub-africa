"""Seed idempotent des données de référence du Module 1 (12 rôles système +
catalogue de permissions + matrice par défaut). À exécuter une fois après
`alembic upgrade head`, et à chaque déploiement (sans risque, idempotent).

Usage : python scripts/seed_reference_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.auth_tenants.infrastructure.db.seed import seed_roles_and_permissions
from src.shared_kernel.db.session import tenant_scoped_session


async def main() -> None:
    async with tenant_scoped_session(tenant_id=None, is_super_admin=True) as session:
        await seed_roles_and_permissions(session)
    print("Rôles et permissions de référence : à jour.")


if __name__ == "__main__":
    asyncio.run(main())
