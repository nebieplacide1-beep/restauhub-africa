# 5. Modèle de données — Authentification & gestion des tenants

## 5.1 Diagramme entité-relation

```mermaid
erDiagram
    TENANTS ||--o{ USERS : possede
    TENANTS ||--o{ AUDIT_LOGS : genere
    USERS ||--o{ USER_ROLES : a
    ROLES ||--o{ USER_ROLES : attribue
    ROLES ||--o{ ROLE_PERMISSIONS : compose
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : compose
    USERS ||--o{ REFRESH_TOKENS : emet
    USERS ||--o| TWO_FACTOR_SECRETS : configure
    USERS ||--o{ AUDIT_LOGS : declenche
    TENANTS ||--o{ INVITATIONS : emet
    ROLES ||--o{ INVITATIONS : "role initial"
    USERS ||--o{ INVITATIONS : invite

    TENANTS {
        uuid id PK
        text name
        text slug UK
        text country
        text default_currency
        text default_locale
        text status
        timestamptz created_at
        timestamptz updated_at
    }

    USERS {
        uuid id PK
        uuid tenant_id FK "nullable, cf amendement 5.2 (Super Administrateur)"
        text email UK "nullable, unique globalement"
        text phone_number UK "nullable, unique globalement"
        text password_hash
        boolean is_active
        boolean two_factor_enabled
        int failed_login_attempts "BR-12"
        timestamptz locked_until "BR-12, nullable"
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    ROLES {
        uuid id PK
        text code UK
        text label
        boolean is_system_role
    }

    PERMISSIONS {
        uuid id PK
        text code UK
        text domain
        text action
    }

    USER_ROLES {
        uuid user_id FK
        uuid role_id FK
        uuid succursale_id "nullable, reserve Module 2"
        timestamptz assigned_at
    }

    ROLE_PERMISSIONS {
        uuid tenant_id FK "nullable = jeu par defaut global"
        uuid role_id FK
        uuid permission_id FK
    }

    REFRESH_TOKENS {
        uuid id PK
        uuid tenant_id FK "denormalise, pour la RLS"
        uuid user_id FK
        text token_hash UK
        timestamptz expires_at
        timestamptz revoked_at
        uuid replaced_by "nullable"
        text device_label
        timestamptz created_at
    }

    TWO_FACTOR_SECRETS {
        uuid user_id PK_FK
        uuid tenant_id FK "denormalise, pour la RLS"
        text encrypted_secret
        text[] recovery_codes_hashed
        timestamptz created_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid tenant_id FK "nullable si action Super Admin"
        uuid user_id FK "nullable si echec anonyme"
        text action
        text result
        text ip_address
        jsonb metadata
        timestamptz created_at
    }

    INVITATIONS {
        uuid id PK
        uuid tenant_id FK
        text email "nullable"
        text phone_number "nullable"
        uuid role_id FK
        uuid invited_by FK
        text token_hash UK
        text status "pending | accepted | expired | revoked"
        timestamptz expires_at
        timestamptz accepted_at "nullable"
        timestamptz created_at
    }
```

## 5.2 Amendement post-validation (implémentation, 2026-08-07)

En implémentant le cas d'usage de connexion, une incohérence est apparue dans la version initialement validée de ce document : l'unicité d'`email`/`phone_number` **par tenant** rend la connexion ambiguë, puisque l'identifiant seul (sans connaître le tenant au préalable) ne permet pas de savoir dans quel tenant chercher l'utilisateur — et la Row-Level Security interdit par construction toute lecture cross-tenant implicite.

**Correctif appliqué** : `email` et `phone_number` sont désormais uniques **globalement** sur la plateforme (cohérent avec la décision déjà validée BR-07 : un compte = un tenant, donc une personne gérant plusieurs tenants utilise déjà plusieurs comptes/emails distincts). La recherche d'un utilisateur par identifiant au moment du login s'effectue via un contexte de session dédié et restreint (`app.auth_lookup`, voir [03-architecture.md](./03-architecture.md#isolation-multi-tenant)), jamais via une désactivation générale de la RLS. Par conséquent, `refresh_tokens` et `two_factor_secrets` portent désormais aussi `tenant_id` (dénormalisé) pour rester filtrables par RLS au même titre que les autres tables sensibles.

Ajout mineur du même passage : `users` gagne `failed_login_attempts` et `locked_until`, nécessaires pour implémenter le verrouillage de compte (BR-12), omis du modèle initial. La table `invitations` (BR-09/BR-10), décrite en toutes lettres dans les règles métier mais absente du schéma d'origine, est ajoutée pour porter l'état d'une invitation en attente (email/téléphone cible, rôle initial, expiration 72h).

Enfin, `users.tenant_id` devient **nullable** : BR-24 exige que le Super Administrateur ne soit jamais rattaché à un tenant, ce qui était incompatible avec une clé étrangère obligatoire. Un compte Super Administrateur n'est jamais créé via `POST /tenants` ni via une invitation (ces deux chemins sont exclusivement tenant-scopés) — il est provisionné une fois via un script d'amorçage (`backend/scripts/create_super_admin.py`), en dehors de l'API publique.

## 5.3 Notes de conception par table

**`tenants`** — Racine de l'isolation multi-tenant. `slug` unique globalement (index unique). `status` : `en_essai | actif | suspendu | résilié` (enum PostgreSQL).

**`users`** — `email` et `phone_number` sont uniques **globalement** (voir 5.2), chacun avec un index unique partiel `WHERE ... IS NOT NULL`. Contrainte `CHECK` : au moins un de `email`/`phone_number` non nul (BR-06).

**`roles`** — Les 12 rôles de l'AMD sont insérés en seed avec `is_system_role = true` (non supprimables). Un Administrateur pourra créer des rôles additionnels par tenant dans une évolution future (`tenant_id` nullable non présent en v1 — hors périmètre, voir décisions à valider dans [03-architecture.md](./03-architecture.md#décisions-à-valider)).

**`permissions`** — Référence globale, format `domaine:action` (ex. `menu:write`). Le champ `code` est la valeur réellement vérifiée par `require_permission(...)` ; `domain`/`action` ne servent qu'à l'affichage et au filtrage en back-office.

**`user_roles`** — Table d'association ; `succursale_id` est ajoutée dès maintenant en `nullable` pour éviter une migration destructive au Module 2, mais n'est ni lue ni écrite par le Module 1 (toujours `null`).

**`role_permissions`** — `tenant_id` nullable : une ligne avec `tenant_id = null` définit le jeu de permissions **par défaut** d'un rôle (le seed de la matrice en section 2.5) ; une ligne avec `tenant_id` renseigné **surcharge** ce défaut pour ce tenant (BR-23). La résolution effective des permissions d'un utilisateur consulte d'abord les lignes propres à son tenant, puis retombe sur les lignes par défaut.

**`refresh_tokens`** — `token_hash` (SHA-256 du token, jamais le token en clair) unique. `replaced_by` chaîne les rotations successives et permet de détecter une réutilisation (BR-15/3.4) : si un token déjà `revoked_at` non nul est présenté, toute la chaîne est révoquée.

**`two_factor_secrets`** — Relation 1-1 avec `users` (clé primaire = clé étrangère). `encrypted_secret` chiffré avec la clé applicative (jamais en clair, distinct du hachage — le secret TOTP doit être déchiffrable pour vérifier les codes).

**`audit_logs`** — Append-only (BR-26) : aucun `UPDATE`/`DELETE` autorisé au niveau applicatif ; `metadata` (JSONB) porte les détails spécifiques à chaque type d'action sans multiplier les colonnes.

**`invitations`** — `token_hash` suit la même politique que `refresh_tokens` (jamais le token en clair). `status` passe à `expired` par lecture paresseuse (comparaison à `expires_at`) plutôt que par une tâche planifiée, pour rester simple en v1.

## 5.4 Row-Level Security (référence croisée)

Chaque table portant `tenant_id` (`users`, `refresh_tokens`, `two_factor_secrets`, `invitations`, `role_permissions`, `audit_logs`) active une policy RLS de la forme :

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR current_setting('app.is_super_admin', true) = 'true'
        OR current_setting('app.auth_lookup', true) = 'true'
    );
```

(`NULLIF(..., '')` évite qu'un cast `''::uuid` échoue lorsqu'aucun tenant n'est connu — un cast direct de la chaîne vide est une erreur PostgreSQL, pas juste une valeur fausse.)

Le contexte `app.auth_lookup` s'applique aux **six** tables tenant-scopées, pas seulement à `users` : les cas d'usage qui s'exécutent avant que le tenant ne soit connu (`RegisterTenant`, `LoginUser`, `VerifyTwoFactorChallenge`, `RefreshAccessToken`, `AcceptInvitation`, `GetInvitationPreview`) lisent et écrivent potentiellement dans chacune d'elles au cours d'une même transaction (ex. `LoginUser` peut écrire une ligne `audit_logs` avec le `tenant_id` de l'utilisateur trouvé, alors que le GUC `app.tenant_id` de la session est encore vide — sans le bypass, PostgreSQL rejetterait l'écriture via la clause `WITH CHECK` implicite de la policy). En dehors de ce petit ensemble fixe et audité de cas d'usage du module `auth_tenants`, `app.auth_lookup` n'est jamais positionné à `true` — pour tout le reste de l'application, présente et future, la RLS reste pleinement contraignante. `role_permissions` ajoute `tenant_id IS NULL` (défauts globaux, visibles de tous). `roles` et `permissions` sont des tables de référence globales, sans `tenant_id` ni RLS.

Le détail d'implémentation (migration Alembic, positionnement des GUC par `tenant_scoped_session`/`auth_lookup_session`) est traité à l'étape 7 (Backend, voir `backend/src/shared_kernel/db/session.py` et `backend/alembic/versions/0001_initial_auth_tenants.py`).
