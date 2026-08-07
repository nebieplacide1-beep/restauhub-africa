"""Provisionne le tout premier compte Super Administrateur (BR-24).

Volontairement hors de l'API publique : le Super Administrateur n'est
rattaché à aucun tenant et ne peut donc pas naître de `POST /tenants` ni
d'une invitation, qui sont tous deux tenant-scopés (voir
docs/modules/01-auth-tenants/05-modele-donnees.md#52-amendement-post-validation-implémentation-2026-08-07).

Usage : python scripts/create_super_admin.py <email> <mot-de-passe>
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.auth_tenants.domain.entities import RoleCode, User
from src.modules.auth_tenants.domain.services import PasswordPolicy
from src.modules.auth_tenants.domain.value_objects import Email
from src.modules.auth_tenants.infrastructure.db.repositories import (
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)
from src.modules.auth_tenants.infrastructure.security.argon2_hasher import Argon2Hasher
from src.shared_kernel.db.session import tenant_scoped_session


async def main(email_raw: str, password: str) -> None:
    email = Email(email_raw)
    PasswordPolicy.validate(password)
    hasher = Argon2Hasher()

    async with tenant_scoped_session(tenant_id=None, is_super_admin=True) as session:
        users = SqlAlchemyUserRepository(session)
        roles = SqlAlchemyRoleRepository(session)

        if await users.identifier_exists(email=str(email), phone_number=None):
            print(f"Un compte existe déjà pour {email}.")
            return

        role = await roles.get_by_code(RoleCode.SUPER_ADMINISTRATEUR)
        if role is None:
            print(
                "Le rôle 'super_administrateur' n'existe pas — "
                "lancez d'abord seed_reference_data.py."
            )
            return

        user = User(
            id=uuid4(),
            tenant_id=None,
            email=str(email),
            phone_number=None,
            password_hash=hasher.hash(password),
            is_active=True,
            two_factor_enabled=False,
        )
        await users.add(user)
        await roles.assign_role(user_id=user.id, role_id=role.id)

    print(f"Super Administrateur créé : {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python scripts/create_super_admin.py <email> <mot-de-passe>")
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
