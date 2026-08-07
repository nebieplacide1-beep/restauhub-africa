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
        uuid tenant_id FK
        text email UK "nullable, unique par tenant"
        text phone_number UK "nullable, unique par tenant"
        text password_hash
        boolean is_active
        boolean two_factor_enabled
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
```

## 5.2 Notes de conception par table

**`tenants`** — Racine de l'isolation multi-tenant. `slug` unique globalement (index unique). `status` : `en_essai | actif | suspendu | résilié` (enum PostgreSQL).

**`users`** — `email` et `phone_number` sont uniques **par tenant** (index unique composite `(tenant_id, email)` et `(tenant_id, phone_number)`, partiels `WHERE ... IS NOT NULL`), pas uniques globalement : rien n'empêche deux tenants différents d'avoir un utilisateur avec le même email (BR-07, un compte par tenant). Contrainte `CHECK` : au moins un de `email`/`phone_number` non nul (BR-06).

**`roles`** — Les 12 rôles de l'AMD sont insérés en seed avec `is_system_role = true` (non supprimables). Un Administrateur pourra créer des rôles additionnels par tenant dans une évolution future (`tenant_id` nullable non présent en v1 — hors périmètre, voir décisions à valider dans [03-architecture.md](./03-architecture.md#décisions-à-valider)).

**`permissions`** — Référence globale, format `domaine:action` (ex. `menu:write`). Le champ `code` est la valeur réellement vérifiée par `require_permission(...)` ; `domain`/`action` ne servent qu'à l'affichage et au filtrage en back-office.

**`user_roles`** — Table d'association ; `succursale_id` est ajoutée dès maintenant en `nullable` pour éviter une migration destructive au Module 2, mais n'est ni lue ni écrite par le Module 1 (toujours `null`).

**`role_permissions`** — `tenant_id` nullable : une ligne avec `tenant_id = null` définit le jeu de permissions **par défaut** d'un rôle (le seed de la matrice en section 2.5) ; une ligne avec `tenant_id` renseigné **surcharge** ce défaut pour ce tenant (BR-23). La résolution effective des permissions d'un utilisateur consulte d'abord les lignes propres à son tenant, puis retombe sur les lignes par défaut.

**`refresh_tokens`** — `token_hash` (SHA-256 du token, jamais le token en clair) unique. `replaced_by` chaîne les rotations successives et permet de détecter une réutilisation (BR-15/3.4) : si un token déjà `revoked_at` non nul est présenté, toute la chaîne est révoquée.

**`two_factor_secrets`** — Relation 1-1 avec `users` (clé primaire = clé étrangère). `encrypted_secret` chiffré avec la clé applicative (jamais en clair, distinct du hachage — le secret TOTP doit être déchiffrable pour vérifier les codes).

**`audit_logs`** — Append-only (BR-26) : aucun `UPDATE`/`DELETE` autorisé au niveau applicatif ; `metadata` (JSONB) porte les détails spécifiques à chaque type d'action sans multiplier les colonnes.

## 5.3 Row-Level Security (référence croisée)

Chaque table portant `tenant_id` (`users`, `role_permissions`, `audit_logs`) active une policy RLS équivalente à :

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

Le détail d'implémentation (migration Alembic, positionnement de `app.tenant_id` par le middleware) est traité à l'étape 7 (Backend), pas dans ce document de conception.
