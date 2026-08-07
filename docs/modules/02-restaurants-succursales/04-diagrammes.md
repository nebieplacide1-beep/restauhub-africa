# 4. Diagrammes — Restaurants & succursales

## 4.1 C4 — Contexte et conteneurs

Inchangés par rapport au Module 1 (voir [../01-auth-tenants/04-diagrammes.md](../01-auth-tenants/04-diagrammes.md#41-c4--niveau-contexte)) : ce module n'introduit ni nouvel acteur, ni nouveau conteneur, ni système externe. Il ajoute uniquement des tables et des routes au conteneur API déjà existant.

## 4.2 UML — Diagramme de classes du domaine

```mermaid
classDiagram
    class Succursale {
        +UUID id
        +UUID tenant_id
        +str name
        +str address_line
        +str city
        +str country
        +str default_currency
        +str default_locale
        +SuccursaleStatus status
        +OpeningHours opening_hours
        +str~nullable~ phone_number
        +datetime created_at
    }

    class SuccursaleStatus {
        <<enumeration>>
        ACTIVE
        INACTIVE
        FERMETURE_TEMPORAIRE
    }

    class OpeningHours {
        +dict~Weekday, list~TimeRange~~ schedule
        +is_open_at(datetime) bool
    }

    class UserRole {
        +UUID user_id
        +UUID role_id
        +UUID~nullable~ succursale_id
    }

    class User {
        +UUID id
        +UUID tenant_id
    }

    class Tenant {
        +UUID id
    }

    Tenant "1" --> "*" Succursale : possede
    Succursale "0..1" <-- "*" UserRole : delimite le perimetre de
    User "1" --> "*" UserRole : a
    Succursale ..> OpeningHours : compose
    Succursale ..> SuccursaleStatus : a un
```

## 4.3 Séquence — Rattachement d'un employé à une succursale

```mermaid
sequenceDiagram
    participant G as Gérant/Administrateur
    participant A as API (succursales_router)
    participant UC as AssignEmployeeToSuccursale
    participant SR as SuccursaleRepository
    participant UR as UserRoleRepository (Module 1, étendu)

    G->>A: PATCH /succursales/{id}/staff (user_id, role_code)
    A->>UC: execute(actor, succursale_id, user_id, role_code)
    UC->>SR: get_by_id(succursale_id)
    SR-->>UC: Succursale (vérifie tenant_id == actor.tenant_id)
    UC->>UR: assign_role(user_id, role_id, succursale_id)
    UR-->>UC: OK
    UC-->>A: 204
    A-->>G: 204
```

## 4.4 Séquence — Vue PDG multi-succursales

```mermaid
sequenceDiagram
    participant P as PDG
    participant A as API (succursales_router)
    participant UC as ListSuccursales
    participant SR as SuccursaleRepository

    Note over P,A: user_roles.succursale_id = null pour le PDG (BR2-08) → accès tenant-wide, pas de filtre supplémentaire nécessaire.
    P->>A: GET /succursales
    A->>UC: execute(tenant_id)
    UC->>SR: list_by_tenant(tenant_id)
    SR-->>UC: [Succursale, ...] (RLS garantit déjà le scope tenant)
    UC-->>A: liste complète
    A-->>P: 200
```
