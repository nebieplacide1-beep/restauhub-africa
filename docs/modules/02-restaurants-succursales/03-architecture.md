# 3. Architecture — Restaurants & succursales

## 3.1 Position dans le monorepo

Nouveau module au sein du même backend FastAPI, à côté de `auth_tenants` :

```
backend/src/modules/
├── auth_tenants/        (Module 1, existant)
└── succursales/         (Module 2, ce document)
```

Le nom de dossier retenu est `succursales` et non `restaurants` : conformément à la décision de conception (section 1.1 de l'analyse), il n'y a pas d'entité « Restaurant » — le concept central introduit par ce module est la succursale. Ce choix de nommage technique n'a pas besoin de correspondre mot pour mot au titre AMD du module.

## 3.2 Style architectural

Même structure hexagonale/DDD que le Module 1 (voir [../01-auth-tenants/03-architecture.md](../01-auth-tenants/03-architecture.md#32-style-architectural)), reproduite à l'identique :

```
succursales/
├── domain/
│   ├── entities.py          # Succursale, OpeningHours (value object), SuccursaleStatus
│   ├── repositories.py      # SuccursaleRepository (port)
│   └── exceptions.py
├── application/
│   ├── dto.py
│   ├── ports.py             # AuditRecorder, Clock réutilisés depuis auth_tenants ? voir 3.5
│   └── use_cases/
│       ├── succursale_use_cases.py   # Create/Update/Deactivate/Reactivate/List
│       └── staffing_use_cases.py     # AssignEmployeeToSuccursale/RemoveAssignment/ListStaff
├── infrastructure/
│   └── db/
│       ├── models.py        # SuccursaleModel
│       └── repositories.py
├── api/
│   └── v1/
│       ├── succursales_router.py
│       └── staffing_router.py
└── tests/
```

## 3.3 Réutilisation du Module 1 (pas de duplication)

Ce module **ne redéfinit rien** de ce que le Module 1 possède déjà :

- **Authentification/autorisation** : les routers de ce module utilisent exactement les mêmes dépendances FastAPI (`get_current_user`, `require_permission`, `get_repositories`) définies dans `modules/auth_tenants/api/deps.py`. Aucune dépendance dupliquée.
- **Audit** : réutilise `shared_kernel.audit.service.record_audit_event` directement (le port `AuditRecorder` du Module 1 est assez générique pour être réimporté tel quel, pas besoin d'un second port identique).
- **Rattachement employé/succursale** : la table `user_roles` (propriété du Module 1) est **modifiée** par ce module uniquement pour activer sa colonne `succursale_id` déjà existante — ce module n'en devient pas propriétaire pour autant ; `UserRoleRepository.assign_role`/`remove_role` du Module 1 sont étendus avec un paramètre `succursale_id` optionnel plutôt que dupliqués.

Cette réutilisation directe (plutôt qu'un « anti-corruption layer » complet entre modules) est jugée proportionnée : les deux modules sont dans le même backend, la même équipe, le même cycle de vie — la séparation en bounded contexts distincts reste utile pour la lisibilité du code, pas pour s'isoler d'une équipe tierce.

## 3.4 Isolation multi-tenant

Identique au Module 1 (section 3.3 de son architecture) : `succursales` porte `tenant_id`, RLS activée avec `FORCE ROW LEVEL SECURITY`, policy `tenant_id = ... OR is_super_admin`. **Pas de contexte `app.auth_lookup`** ici : contrairement à l'authentification, aucun cas d'usage de ce module ne s'exécute avant que le tenant ne soit connu — toutes les routes sont authentifiées.

## 3.5 Ce que ce module expose aux autres modules

- `SuccursaleRepository` (port du domaine), consommable par les futurs modules Catalogue/Opérations pour valider qu'une `succursale_id` référencée existe bien et appartient au tenant courant.
- Une fonction utilitaire `get_operational_scope(user) -> list[UUID] | None` (`None` signifiant « toutes les succursales du tenant », cohérent avec BR2-08) — que les modules opérationnels futurs pourront appeler pour filtrer leurs propres requêtes par succursale, sans avoir à relire eux-mêmes `user_roles`.

## 3.6 Décisions à valider

1. **Pas d'entité Restaurant distincte du Tenant** — déjà validée le 2026-08-07 (voir analyse), rappelée ici car elle conditionne toute l'architecture de ce module.
2. **Réutilisation directe des dépendances/ports du Module 1** plutôt qu'une duplication par souci d'isolation stricte entre bounded contexts (section 3.3) — pragmatique tant que les deux modules restent dans le même service ; à revisiter si une extraction en microservice séparé était un jour envisagée (AMD section 5 : « conçu pour une évolution ultérieure vers des microservices sans réécriture » — cette réutilisation directe est le principal point qui devrait changer dans ce scénario).
3. **`get_operational_scope` renvoie `None` pour signifier « tout le tenant »** plutôt qu'une liste explicite de toutes les succursales — plus efficace (évite une requête supplémentaire) mais impose à chaque module consommateur de gérer ce cas particulier correctement (`None` ≠ liste vide, qui elle signifierait « aucun accès »).
