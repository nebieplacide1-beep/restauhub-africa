# RestauHub Africa — API Backend

Implémentation du **Module 1 : Authentification & gestion des tenants**, conforme à la conception validée dans [`docs/modules/01-auth-tenants/`](../docs/modules/01-auth-tenants/).

## Stack

Python 3.13+, FastAPI, SQLAlchemy 2 (async) + Alembic, PostgreSQL (avec Row-Level Security), Argon2id, JWT (PyJWT), TOTP (pyotp).

## Architecture

Clean Architecture / DDD / Hexagonale (AMD section 3) :

```
src/
├── shared_kernel/        transverse : config, session DB + isolation tenant, sécurité, audit
├── modules/
│   └── auth_tenants/     ce module (bounded context)
│       ├── domain/        entités, value objects, interfaces de repository, règles pures
│       ├── application/   cas d'usage, DTO, ports vers l'infrastructure
│       ├── infrastructure/ SQLAlchemy, JWT/Argon2/TOTP, seed
│       └── api/           routers FastAPI
├── tests/
│   ├── unit/       aucune dépendance (repositories en mémoire, `tests/fakes.py`)
│   ├── integration/ nécessitent PostgreSQL (Row-Level Security)
│   └── api/         bout-en-bout via ASGI, nécessitent PostgreSQL
└── main.py
```

## Démarrage local

```bash
python -m venv .venv
.venv/Scripts/activate        # ou source .venv/bin/activate sous Linux/macOS
pip install -e ".[dev]"
cp .env.example .env          # ajuster les secrets

docker compose up -d          # PostgreSQL + Redis
alembic upgrade head
python scripts/seed_reference_data.py   # 12 rôles + permissions par défaut

uvicorn src.main:app --reload
```

L'API est alors sur `http://localhost:8000`, documentation interactive sur `/docs`.

Pour créer le premier compte Super Administrateur (jamais via l'API publique, voir BR-24) :
```bash
python scripts/create_super_admin.py admin@restauhub.africa "Str0ng!Passw0rd"
```

## Tests

```bash
pytest              # unitaires (toujours) + intégration/API (si PostgreSQL joignable, sinon skip)
ruff check src alembic scripts
ruff format src alembic scripts
```

Les tests unitaires (`src/tests/unit/`) tournent sans base de données via des repositories en mémoire (`src/tests/fakes.py`). Les tests d'intégration et API nécessitent PostgreSQL car ils vérifient la Row-Level Security (absente de SQLite) — ils se désactivent automatiquement si `docker compose up -d db` n'a pas été lancé.

## État par rapport à la spécification validée

Conforme intégralement à [`docs/modules/01-auth-tenants/06-api-specification.md`](../docs/modules/01-auth-tenants/06-api-specification.md) : inscription, connexion, 2FA, rafraîchissement de token, mot de passe oublié, invitations, gestion des utilisateurs/rôles, administration des tenants — implémenté et testé (28/28 tests, dont le flux complet oubli/réinitialisation de mot de passe en bout-en-bout).

## Corrections apportées à la conception pendant l'implémentation

L'implémentation a révélé quelques lacunes dans les documents de conception validés (steps 1-6), corrigées directement dans ces documents avec une note explicite — voir la section « Amendement post-validation » de [`05-modele-donnees.md`](../docs/modules/01-auth-tenants/05-modele-donnees.md#52-amendement-post-validation-implémentation-2026-08-07) :
- unicité globale (et non par tenant) d'email/téléphone, pour lever l'ambiguïté du login ;
- ajout de la table `invitations`, décrite dans les règles métier mais absente du schéma ;
- `users.tenant_id` rendu nullable pour le Super Administrateur ;
- ajout de `failed_login_attempts`/`locked_until` (verrouillage de compte, BR-12) ;
- policies RLS étendues à un contexte `app.auth_lookup`, nécessaire aux flux qui s'exécutent avant que le tenant ne soit connu.

**Deux bugs de sécurité réels, trouvés par le test d'intégration `test_tenant_isolation.py` en l'exécutant contre une vraie base** (et non en le laissant seulement écrit-mais-jamais-lancé) :
1. `FORCE ROW LEVEL SECURITY` manquant — sans elle, PostgreSQL exempte le propriétaire d'une table de sa propre RLS.
2. Plus sérieux : le rôle `restauhub` créé par l'image Docker PostgreSQL est un **superutilisateur**, systématiquement exempté de la RLS par PostgreSQL, sans possibilité de le forcer. Un rôle applicatif dédié et restreint (`restauhub_app`, provisionné par `db/init/01-app-role.sql`) a été introduit ; l'application s'y connecte via `DATABASE_URL`, tandis qu'Alembic continue d'utiliser le rôle superutilisateur via `MIGRATIONS_DATABASE_URL` pour le DDL.

Ces deux corrections illustrent pourquoi la règle absolue d'isolation multi-tenant de l'AMD ne peut pas se vérifier par lecture de code seule — `pytest` doit tourner contre une vraie base PostgreSQL avant de considérer ce module validé.

**Mot de passe oublié** (`POST /auth/password/forgot`/`reset`) a été ajouté après coup : prévu dans la spécification API validée mais initialement laissé de côté par souci de ne pas livrer d'implémentation bâclée. Nécessite une nouvelle table (`password_reset_tokens`, migration `0002`), documentée dans le même esprit d'amendement post-validation que les corrections ci-dessus — voir [`05-modele-donnees.md`](../docs/modules/01-auth-tenants/05-modele-donnees.md#password_reset_tokens-ajoutée-après-validation-initiale-br-16bis).
