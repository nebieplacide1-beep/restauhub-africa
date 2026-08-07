# RestauHub Africa — Architecture Master Document (AMD)

> Document de référence unique pour le projet **RestauHub Africa**.
> À utiliser comme contexte de priming pour toute session de développement (Claude Code, revues techniques, onboarding).

---

## 1. Vision du projet

**RestauHub Africa** est une plateforme SaaS multi-tenant de gestion de la restauration, pensée pour le marché africain (multi-pays, multi-langues, multi-devises), et destinée à durer **10+ ans sans refonte majeure**.

**Segments cibles** : restaurants, maquis, bars, hôtels, boulangeries, pâtisseries, cafés, fast-foods, food trucks.

**Positionnement concurrentiel** : équivalent africain de Toast POS, Lightspeed, Odoo, Square, Shopify, Uber Eats et Glovo — combinant gestion de point de vente, back-office, livraison, marketplace et publicité en une seule plateforme.

---

## 2. Rôle attendu de l'assistant IA

Sur ce projet, l'IA doit se comporter comme un collectif d'expertise senior :
Architecte Logiciel, CTO, Product Manager, Software Engineer Principal, DevOps Engineer, Database Architect, Security Engineer, UI/UX Architect.

**Principe directeur** : ne jamais sacrifier l'architecture à la vitesse d'exécution. Chaque décision technique doit être justifiée et évaluée selon : évolutivité, sécurité, simplicité, maintenabilité, performance, qualité du code.

### Protocole de traitement d'une demande de fonctionnalité
1. Analyser le besoin.
2. Vérifier la cohérence avec l'architecture existante.
3. Identifier les impacts sur les autres modules.
4. Proposer des améliorations possibles.
5. Générer un plan de développement.
6. Attendre validation si une décision structurante est en jeu.
7. Implémenter uniquement après validation.

---

## 3. Philosophie & principes d'ingénierie

| Principe | Application |
|---|---|
| Clean Architecture | Séparation stricte des couches (domaine / application / infrastructure) |
| Domain-Driven Design | Modules organisés autour des domaines métier |
| Architecture Hexagonale | Ports & adaptateurs pour isoler le cœur métier |
| SOLID / DRY / KISS / YAGNI | Qualité et sobriété du code |
| Repository Pattern & Service Layer | Accès aux données et logique métier découplés |
| Dependency Injection | Testabilité et inversion de contrôle |
| API First | Contrat d'API défini avant l'implémentation |
| Offline First | Fonctionnement mobile dégradé sans réseau |
| Security First | Sécurité intégrée dès la conception |
| Cloud Native | Conteneurisation, observabilité, scalabilité horizontale |
| Documentation First | Spécification avant code |

---

## 4. Stack technique

### Backend
- **Langage** : Python 3.13
- **Framework** : FastAPI
- **ORM** : SQLAlchemy 2 + Alembic (migrations)
- **Base de données** : PostgreSQL
- **Cache / broker** : Redis
- **Tâches asynchrones** : Celery
- **Temps réel** : WebSocket
- **Validation** : Pydantic
- **Auth** : JWT + OAuth2
- **Qualité** : Pytest, Ruff, Black, MyPy

### Mobile
- Flutter
- Riverpod (state management)
- GoRouter (navigation)
- Dio (HTTP client)
- Hive (stockage local)
- Freezed (immutabilité / modèles)
- Flutter Secure Storage (secrets)

### Web
> Décision révisée le 2026-08-07 : Next.js remplace Flutter Web, pour bénéficier nativement de l'écosystème Vercel (SSR/ISR, edge functions, SEO, déploiement continu via GitHub). Flutter reste la stack mobile (iOS/Android) exclusivement.
- Next.js (App Router) + React + TypeScript
- Tailwind CSS v4 + shadcn/ui (Radix)
- Déploiement : Vercel, connecté au dépôt GitHub (CI/CD automatique)

### Infrastructure
- Docker / Docker Compose
- Nginx (reverse proxy)
- GitHub Actions (CI/CD) — pour le backend ; le frontend web est déployé en continu via Vercel
- Observabilité : Prometheus, Grafana, Loki, Sentry
- Stockage objet : MinIO

---

## 5. Architecture globale

- **Style** : Modular Monolith, conçu pour une évolution ultérieure vers des microservices sans réécriture.
- **Approches combinées** : DDD, Hexagonale, API First, Offline First.
- **Dimensions transverses** : Multi-tenant, Multi-pays, Multi-langues, Multi-devises.

### Isolation multi-tenant
Chaque restaurant dispose de ses propres : utilisateurs, employés, menus, produits, commandes, clients, paiements, rapports, paramètres.

**Règle absolue** : aucune donnée n'est visible entre tenants. Toute requête (API, base de données, cache, tâches asynchrones) doit être filtrée/isolée par `tenant_id`.

---

## 6. Modules fonctionnels

| Domaine | Modules |
|---|---|
| Identité | Authentification, Utilisateurs, Rôles, Permissions |
| Structure | Restaurants, Succursales, Employés |
| Catalogue | Produits, Catégories, Menus, Recettes |
| Opérations | Stocks, Achats, Fournisseurs, Commandes, Cuisine, Tables, QR Codes, Réservations |
| Finance | Paiements, Factures, Wallet, Commissions, Abonnements SaaS |
| Croissance | Livraison, Fidélité, Coupons, Publicités, Marketplace |
| Intelligence | Analytics, Business Intelligence, Intelligence Artificielle, Rapports |
| Gouvernance | Audit, Logs, Support, Paramètres, API Publique |

---

## 7. Rôles utilisateurs

| Rôle | Portée |
|---|---|
| Client | Application consommateur final |
| Serveur | Prise de commande en salle |
| Cuisine | Suivi de production |
| Caissier | Encaissement / caisse |
| Gérant | Pilotage d'un établissement |
| PDG | Pilotage multi-établissements |
| Comptable | Suivi financier |
| Livreur | Logistique de livraison |
| Annonceur | Achat d'espaces publicitaires |
| Fournisseur | Vente sur le marketplace |
| Administrateur | Gestion d'un tenant |
| Super Administrateur | Gestion globale du SaaS |

Chaque rôle doit disposer de : permissions dédiées, dashboard, API, services, tests, documentation.

### Fonctionnalités clés par rôle

**Client** : créer un compte, commander (sur place / à emporter / livraison), réserver, payer, suivre une commande, recevoir des notifications, cumuler des points de fidélité, laisser un avis, consulter les promotions, choisir un restaurant.

**Serveur** : connexion personnelle, prise de commande, gestion des tables, historique des ventes, statistiques personnelles.

**Caissier** : encaissement, paiement, facturation, ouverture/clôture de caisse, rapport journalier.

**Cuisine** : visualisation des commandes, changement de statuts, temps de préparation, signalement de rupture.

**Gérant** : gestion du personnel, des stocks, des produits, des promotions, rapports d'établissement.

**PDG** : tableau de bord global, vue multi-établissements, rapports consolidés, analyse financière, statistiques.

**Super Administrateur** : gestion du SaaS, des restaurants, des abonnements, des commissions, des publicités, monitoring, support.

---

## 8. Modèle économique

### Commission
- Prélevée automatiquement par la plateforme.
- Taux par défaut : **1 %**, configurable.
- Appliquée uniquement **après confirmation définitive du paiement**.
- Chaque calcul de commission doit être historisé (traçabilité comptable).

### Publicité
- Les restaurants publient promotions, nouveaux menus, événements.
- Les entreprises achètent des espaces publicitaires.
- Les institutions diffusent des campagnes.

### Marketplace
- Les fournisseurs vendent : viandes, boissons, gaz, légumes, équipements, emballages.
- Les restaurants commandent directement via la plateforme.

---

## 9. Intelligence artificielle

L'IA a un rôle **assistif, jamais décisionnel** sur les actions critiques. Ses capacités :
- Prévision des ventes
- Prévision des ruptures de stock
- Détection d'anomalies
- Génération de rapports
- Recommandation de produits
- Analyse de performance

---

## 10. Sécurité

- Authentification JWT
- Contrôle d'accès basé sur les rôles (RBAC)
- Authentification à deux facteurs (2FA)
- Conformité OWASP
- Journalisation d'audit (Audit Logs)
- Limitation de débit (Rate Limiting)
- Permissions granulaires
- Validation stricte des entrées
- Chiffrement des données sensibles
- Sauvegardes automatiques

---

## 11. Qualité & tests

Le code doit toujours être : typé, testé, documenté, modulaire, lisible, maintenable, réutilisable.

Chaque module doit inclure :
- Tests unitaires
- Tests d'intégration
- Tests API

**Règle** : aucune fonctionnalité n'est considérée terminée sans couverture de tests.

---

## 12. Processus de documentation

Avant tout développement d'un module, produire dans l'ordre :
1. Règles métier (Business Rules)
2. Architecture du module
3. Diagrammes UML
4. Diagrammes C4
5. Modèle de données (ERD)
6. Spécification API

Le développement ne commence qu'une fois ces livrables validés.

---

## 13. Méthode de travail

Traiter **un seul module à la fois**, jamais en parallèle, selon la séquence suivante :

1. Analyse
2. Documentation
3. Business Rules
4. Architecture
5. Base de données
6. API
7. Backend
8. Tests
9. Flutter (mobile/web)
10. Documentation finale
11. Validation

---

## 14. Statut du projet

- [x] Design system + page d'accueil vitrine (Next.js, charte graphique dérivée du logo) — 2026-08-07
- [ ] Module 1 : Authentification & gestion des tenants — *à démarrer*
- [ ] Module 2 : Restaurants & succursales
- [ ] Module 3 : Catalogue (produits, menus, catégories)
- [ ] Module 4 : Commandes & cuisine
- [ ] Module 5 : Paiements & facturation
- [ ] ...

*(à mettre à jour au fil de l'avancement — un module = une case cochée une fois les 11 étapes de la section 13 validées)*
