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
| 7 | Backend | ⏳ | — |
| 8 | Tests | ⏳ | — |
| 9 | Flutter (mobile/web) | ⏳ | — |
| 10 | Documentation finale | ⏳ | — |
| 11 | Validation | ⏳ | — |

**Décision structurante validée le 2026-08-07** : pas d'entité « Restaurant » distincte du `Tenant` du Module 1 — le tenant *est* le restaurant, et ce module ajoute la notion de succursale (lieu physique) en dessous. Voir [01-analyse.md](./01-analyse.md#décision-structurante--pas-dentité-restaurant-distincte-du-tenant).

**Conformément à la section 12 de l'AMD**, les étapes 1 à 6 sont soumises à validation avant le démarrage de l'étape 7 (Backend).
