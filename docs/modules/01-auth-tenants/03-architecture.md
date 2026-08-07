# 3. Architecture — Authentification & gestion des tenants

## 3.1 Position dans le monorepo

Le repo `restauhub-africa` devient un monorepo à deux racines de déploiement indépendantes :

```
restauhub-africa/
├── app/, components/, lib/, public/   ← frontend Next.js existant (déployé sur Vercel)
├── backend/                            ← nouveau : API Python/FastAPI (ce module)
└── docs/modules/                       ← documentation de conception, module par module
```

- **Vercel** est configuré avec *Root Directory* = racine du repo pour le frontend (déjà en place, aucun changement) et un `.vercelignore`/`Ignored Build Step` pour ne jamais tenter de builder `backend/`.
- **Le backend n'est pas déployé sur Vercel** (serverless Python de Vercel incompatible avec les besoins de connexions PostgreSQL persistantes, Celery et WebSocket de l'AMD). Il sera déployé sur une plateforme orientée conteneurs (Railway/Render/Fly.io — choix précis à faire à l'étape 7, hors périmètre de ce document). Un `Dockerfile` sera fourni dans `backend/` à cette étape.

## 3.2 Style architectural

Conforme à l'AMD (section 3) : **Clean Architecture + DDD + Hexagonale**, un module = un *bounded context*, les dépendances pointent toujours vers l'intérieur (`api` → `application` → `domain`, jamais l'inverse).

```
backend/
├── src/
│   ├── shared_kernel/                  # transverse à tous les modules
│   │   ├── config.py                   # settings (Pydantic Settings)
│   │   ├── db/session.py               # session SQLAlchemy async, gestion du contexte tenant
│   │   ├── security/                   # primitives partagées (hashing, jwt bas niveau)
│   │   ├── exceptions.py               # exceptions métier communes → HTTP
│   │   ├── audit/                      # écriture dans audit_logs, réutilisable par tous les modules
│   │   └── middleware/tenant_context.py
│   │
│   ├── modules/
│   │   └── auth_tenants/               # ce module (bounded context)
│   │       ├── domain/                 # cœur métier — aucune dépendance framework
│   │       │   ├── entities/           # Tenant, User, Role, Permission, RefreshToken
│   │       │   ├── value_objects/      # Email, PhoneNumber, PasswordHash, TenantSlug
│   │       │   ├── repositories/       # interfaces (ports) : TenantRepository, UserRepository...
│   │       │   ├── services/           # règles pures : PermissionResolver, PasswordPolicy
│   │       │   └── exceptions.py
│   │       │
│   │       ├── application/            # cas d'usage — orchestrent domaine + ports
│   │       │   ├── use_cases/          # RegisterTenant, LoginUser, RefreshAccessToken,
│   │       │   │                       # EnableTwoFactor, InviteUser, SuspendTenant, ...
│   │       │   ├── dto/                # schémas Pydantic d'entrée/sortie des use cases
│   │       │   └── ports/              # interfaces vers l'infra : TokenService, Mailer, Hasher, Clock
│   │       │
│   │       ├── infrastructure/         # adaptateurs concrets
│   │       │   ├── db/                 # modèles SQLAlchemy + implémentation des repositories
│   │       │   ├── security/           # JWTService (PyJWT), Argon2Hasher, TOTPService (pyotp)
│   │       │   └── notifications/      # envoi d'email d'invitation / de réinitialisation
│   │       │
│   │       ├── api/                    # présentation — routers FastAPI
│   │       │   └── v1/
│   │       │       ├── auth_router.py
│   │       │       ├── tenants_router.py
│   │       │       ├── users_router.py
│   │       │       ├── roles_router.py
│   │       │       └── dependencies.py # get_current_user, require_permission(...), get_tenant
│   │       │
│   │       └── tests/
│   │           ├── unit/               # domaine + application, sans DB ni HTTP
│   │           ├── integration/        # repositories contre une vraie base de test
│   │           └── api/                # tests bout-en-bout via TestClient
│   │
│   └── main.py                          # factory FastAPI, montage des routers de chaque module
│
├── alembic/                             # migrations, une par module au fil de l'avancement
├── pyproject.toml
└── Dockerfile                           # ajouté à l'étape 7
```

**Pourquoi ce découpage** : chaque futur module (Restaurants, Catalogue, Commandes...) reproduira exactement cette structure sous `modules/<nom_module>/`. Le `domain` de `auth_tenants` (notamment `PermissionResolver` et les entités `User`/`Role`) est le seul élément que les autres modules pourront importer directement ; tout le reste communique via les *ports* définis dans `application/ports`, jamais en accédant à l'infrastructure d'un autre module.

## 3.3 Isolation multi-tenant

Défense en profondeur à deux niveaux indépendants, conformément à la règle absolue de l'AMD :

1. **Niveau applicatif** : chaque repository reçoit obligatoirement un `tenant_id` (porté par le contexte de requête, extrait du JWT) et l'injecte dans chaque requête SQL. Aucune méthode de repository ne peut être appelée sans tenant explicite (le Super Administrateur utilise un chemin de code distinct, jamais le même repository).
2. **Niveau base de données** : chaque table portant une donnée de tenant active PostgreSQL **Row-Level Security** avec une policy `USING (tenant_id = current_setting('app.tenant_id')::uuid)`. Le middleware `tenant_context` positionne ce paramètre de session au début de chaque requête HTTP. Ainsi, même un bug applicatif oubliant le filtre `tenant_id` ne peut pas exposer les données d'un autre tenant.

## 3.4 Authentification & jetons

- **Hachage mot de passe** : Argon2id (bibliothèque `argon2-cffi`), paramètres calibrés selon les recommandations OWASP.
- **JWT** : signé en HS256 dans un premier temps (clé secrète unique par environnement), migration possible vers RS256 si des services tiers doivent vérifier les tokens sans partager le secret.
- **Refresh tokens** : stockés hachés (jamais en clair) dans PostgreSQL (table `refresh_tokens`), avec rotation à chaque usage et détection de réutilisation (un refresh token déjà consommé qui est présenté à nouveau révoque toute la famille de tokens de la session — protection contre le vol de token).
- **2FA (TOTP)** : bibliothèque `pyotp`, secret chiffré au repos (via une clé applicative, pas en clair en base).
- **Rate limiting** : Redis (compteur glissant) sur les endpoints `/auth/login`, `/auth/refresh` et `/tenants` (inscription), en complément du verrouillage de compte (BR-12).

## 3.5 Ce que ce module expose aux autres modules

- Une dépendance FastAPI `get_current_user()` → objet `AuthenticatedUser { user_id, tenant_id, role_codes, permissions }`.
- Une dépendance `require_permission("domaine:action")` réutilisable par tous les routers futurs.
- Un service `audit_logger.record(...)` du `shared_kernel` pour que chaque module journalise ses propres événements sensibles.

## 3.6 Évolution vers le multi-succursale

Le Module 2 ajoutera une table `restaurants`/`succursales` rattachée à `tenant_id`. L'extension prévue (non implémentée ici) : une colonne optionnelle `succursale_id` sur `user_roles`, nullable — `null` signifiant « rôle valable sur tout le tenant ». Cette évolution ne nécessite ni migration destructive ni changement de l'API d'authentification.

## 3.7 Décisions à valider

Ces choix engagent la suite du projet ; ils sont documentés avec leur justification ci-dessus mais méritent une relecture explicite avant l'implémentation :

1. **Isolation multi-tenant par Row-Level Security PostgreSQL** en plus du filtrage applicatif (section 3.3) — coût de complexité additionnel (policies à maintenir, tests dédiés), pour un gain de sécurité en profondeur.
2. **2FA obligatoire pour 4 rôles** (Administrateur, Super Administrateur, PDG, Comptable) dès la v1 (BR-17) — impact direct sur l'onboarding de ces profils.
3. **Un compte utilisateur = un seul tenant** (BR-07) — un PDG possédant plusieurs tenants distincts devra utiliser plusieurs comptes en v1 ; le compte multi-tenant est une évolution possible mais non triviale (changement de modèle de session).
4. **Hébergement du backend hors Vercel** (Railway/Render/Fly.io à trancher à l'étape 7) — impact sur le budget d'infrastructure, à valider séparément de ce document.
