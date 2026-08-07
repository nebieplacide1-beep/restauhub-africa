# Module 2 — Restaurants & succursales

Suivi du module selon la méthode en 11 étapes définie dans l'AMD (section 13).

| # | Étape | Statut | Livrable |
|---|---|---|---|
| 1 | Analyse | ✅ | [01-analyse.md](./01-analyse.md) |
| 2 | Documentation | ✅ | ce dossier |
| 3 | Business Rules | ✅ | [02-regles-metier.md](./02-regles-metier.md) |
| 4 | Architecture | ✅ | [03-architecture.md](./03-architecture.md), [04-diagrammes.md](./04-diagrammes.md) |
| 5 | Base de données | ✅ | [05-modele-donnees.md](./05-modele-donnees.md) |
| 6 | API | ✅ | [06-api-specification.md](./06-api-specification.md) |
| 7 | Backend | ✅ | [../../../backend/src/modules/succursales](../../../backend/src/modules/succursales) |
| 8 | Tests | ✅ 47/47 (suite complète du projet, unitaires + intégration + API, exécutés contre PostgreSQL réel) | [../../../backend/src/tests](../../../backend/src/tests) |
| 9 | Flutter (mobile/web) | ⏳ | — |
| 10 | Documentation finale | ⏳ | — |
| 11 | Validation | ⏳ | — |

**Décision structurante validée le 2026-08-07** : pas d'entité « Restaurant » distincte du `Tenant` du Module 1 — le tenant *est* le restaurant, et ce module ajoute la notion de succursale (lieu physique) en dessous. Voir [01-analyse.md](./01-analyse.md#décision-structurante--pas-dentité-restaurant-distincte-du-tenant).

**Le test bout-en-bout a trouvé un vrai bug fonctionnel** (BR2-15) : une invitation Module 1 accorde son rôle tenant-wide par défaut, donc rattacher ensuite ce rôle à une succursale doit **restreindre** l'accès plutôt que l'ajouter en plus — sans quoi BR2-09 ne s'appliquerait jamais à un utilisateur invité. Corrigé et couvert par un test dédié.

**Correctif de conception appliqué en implémentant** : la clé primaire composite `(user_id, role_id)` du Module 1 empêchait BR2-10 (même rôle à plusieurs succursales) — remplacée par une clé de substitution + deux index uniques partiels (migration `0003`, voir [backend/README.md](../../../backend/README.md)).
