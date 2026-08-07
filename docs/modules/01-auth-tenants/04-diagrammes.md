# 4. Diagrammes — Authentification & gestion des tenants

## 4.1 C4 — Niveau Contexte

```mermaid
C4Context
    title RestauHub Africa — Contexte (périmètre Module 1)

    Person(client, "Client", "Consommateur final")
    Person(staff, "Personnel d'établissement", "Serveur, Cuisine, Caissier, Gérant, PDG, Comptable, Livreur")
    Person(superadmin, "Super Administrateur", "Opère la plateforme SaaS")

    System(platform, "RestauHub Africa", "Plateforme SaaS multi-tenant de gestion de la restauration")

    System_Ext(email, "Fournisseur d'email", "Envoi des invitations et réinitialisations de mot de passe")
    System_Ext(authenticator, "Application TOTP", "Google Authenticator / Authy (2FA)")

    Rel(client, platform, "S'authentifie, commande", "HTTPS")
    Rel(staff, platform, "S'authentifie, opère selon son rôle", "HTTPS")
    Rel(superadmin, platform, "Administre les tenants", "HTTPS")
    Rel(platform, email, "Envoie invitations / resets", "SMTP/API")
    Rel(staff, authenticator, "Génère un code 2FA", "TOTP")
```

## 4.2 C4 — Niveau Conteneurs

```mermaid
C4Container
    title RestauHub Africa — Conteneurs (périmètre Module 1)

    Person(user, "Utilisateur", "Client ou personnel d'établissement")

    Container(web, "Application Web", "Next.js / React", "Site vitrine + futur espace applicatif web")
    Container(mobile, "Application Mobile", "Flutter", "iOS / Android, offline-first")
    Container(api, "API RestauHub", "FastAPI / Python 3.13", "Expose les modules métier, dont Authentification & Tenants")
    ContainerDb(db, "Base de données", "PostgreSQL", "Données relationnelles, isolées par tenant (RLS)")
    ContainerDb(cache, "Cache / compteurs", "Redis", "Rate limiting, listes de révocation")
    Container(worker, "Tâches asynchrones", "Celery", "Envoi d'emails, tâches différées (hors périmètre v1 du Module 1)")

    Rel(user, web, "Utilise", "HTTPS")
    Rel(user, mobile, "Utilise", "HTTPS")
    Rel(web, api, "Appelle", "REST/JSON + JWT")
    Rel(mobile, api, "Appelle", "REST/JSON + JWT")
    Rel(api, db, "Lit/écrit (RLS par tenant_id)", "SQL (SQLAlchemy async)")
    Rel(api, cache, "Rate limiting, tokens révoqués", "Redis protocol")
    Rel(api, worker, "Déclenche", "Celery/Redis broker")
```

## 4.3 UML — Diagramme de classes du domaine

```mermaid
classDiagram
    class Tenant {
        +UUID id
        +str name
        +str slug
        +str country
        +str default_currency
        +str default_locale
        +TenantStatus status
        +datetime created_at
    }

    class User {
        +UUID id
        +UUID tenant_id
        +str~nullable~ email
        +str~nullable~ phone_number
        +str password_hash
        +bool is_active
        +bool two_factor_enabled
        +datetime created_at
    }

    class Role {
        +UUID id
        +str code
        +str label
        +bool is_system_role
    }

    class Permission {
        +UUID id
        +str code
        +str domain
        +str action
    }

    class UserRole {
        +UUID user_id
        +UUID role_id
        +UUID~nullable~ succursale_id
    }

    class RolePermission {
        +UUID role_id
        +UUID permission_id
    }

    class RefreshToken {
        +UUID id
        +UUID user_id
        +str token_hash
        +datetime expires_at
        +datetime~nullable~ revoked_at
        +UUID~nullable~ replaced_by
    }

    class TwoFactorSecret {
        +UUID user_id
        +str encrypted_secret
        +List~str~ recovery_codes_hashed
    }

    class AuditLog {
        +UUID id
        +UUID~nullable~ tenant_id
        +UUID~nullable~ user_id
        +str action
        +str result
        +str ip_address
        +datetime created_at
    }

    Tenant "1" --> "*" User : possède
    User "*" --> "*" Role : UserRole
    Role "*" --> "*" Permission : RolePermission
    User "1" --> "*" RefreshToken : émet
    User "1" --> "0..1" TwoFactorSecret : configure
    Tenant "1" --> "*" AuditLog : génère
```

## 4.4 Séquence — Connexion avec 2FA

```mermaid
sequenceDiagram
    participant C as Client (Web/Mobile)
    participant A as API Auth
    participant R as Redis (rate limit)
    participant D as PostgreSQL

    C->>A: POST /auth/login (identifiant, mot de passe)
    A->>R: vérifie le taux de tentatives
    R-->>A: OK
    A->>D: récupère l'utilisateur (email ou téléphone)
    D-->>A: utilisateur + hash + two_factor_enabled
    A->>A: vérifie le mot de passe (Argon2id)
    alt two_factor_enabled = true
        A-->>C: 202 Challenge 2FA requis (challenge_token temporaire)
        C->>A: POST /auth/2fa/verify (challenge_token, code TOTP)
        A->>A: vérifie le code TOTP
    end
    A->>D: crée le refresh token (haché)
    A-->>C: 200 { access_token, refresh_token }
```
