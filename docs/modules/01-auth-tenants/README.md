# Module 1 — Authentification & gestion des tenants

Suivi du module selon la méthode en 11 étapes définie dans l'AMD (section 13).

| # | Étape | Statut | Livrable |
|---|---|---|---|
| 1 | Analyse | ✅ | [01-analyse.md](./01-analyse.md) |
| 2 | Documentation | ✅ | ce dossier |
| 3 | Business Rules | ✅ | [02-regles-metier.md](./02-regles-metier.md) |
| 4 | Architecture | ✅ | [03-architecture.md](./03-architecture.md), [04-diagrammes.md](./04-diagrammes.md) |
| 5 | Base de données | ✅ | [05-modele-donnees.md](./05-modele-donnees.md) |
| 6 | API | ✅ | [06-api-specification.md](./06-api-specification.md) |
| 7 | Backend | ✅ | [../../../backend](../../../backend) |
| 8 | Tests | ✅ 28/28 (unitaires + intégration + API, exécutés contre PostgreSQL réel) | [../../../backend/src/tests](../../../backend/src/tests) |
| 9 | Flutter (mobile/web) | ⏳ non démarré | — |
| 10 | Documentation finale | ⏳ | — |
| 11 | Validation | ⏳ | — |

**Conformément à la section 12 de l'AMD** ("le développement ne commence qu'une fois ces livrables validés"), les étapes 1 à 6 ont été validées avant le démarrage de l'étape 7 (Backend), le 2026-08-07. L'implémentation a corrigé quelques lacunes de conception révélées en cours de route — voir [backend/README.md](../../../backend/README.md#corrections-apportées-à-la-conception-pendant-limplémentation) et l'amendement en tête de [05-modele-donnees.md](./05-modele-donnees.md#52-amendement-post-validation-implémentation-2026-08-07).

**L'exécution des tests d'intégration a trouvé deux bugs de sécurité réels** (RLS non appliquée faute de `FORCE ROW LEVEL SECURITY`, puis rôle applicatif superutilisateur systématiquement exempté de la RLS) — corrigés, voir backend/README.md. C'est la preuve concrète que ces tests avaient une valeur autre que documentaire.

La spécification API validée est désormais couverte intégralement, y compris `POST /auth/password/forgot`/`reset` (ajouté après coup, migration `0002`).
