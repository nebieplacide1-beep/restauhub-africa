# 1. Analyse — Restaurants & succursales

## 1.1 Périmètre du Module 2

D'après l'AMD (section 6, domaine « Structure »), ce module couvre : **Restaurants, Succursales, Employés**. Avant de documenter les règles métier, une clarification terminologique s'impose — elle n'était pas tranchée dans l'AMD ni dans le Module 1.

### Décision structurante : pas d'entité « Restaurant » distincte du Tenant

Le Module 1 a défini `Tenant` comme « un établissement (ou un groupe d'établissements géré par un même PDG) inscrit sur la plateforme » (BR-01). Deux modélisations étaient possibles pour le Module 2 :

- **(A) Trois niveaux** : `Tenant` (compte SaaS / groupe) → `Restaurant` (marque/concept) → `Succursale` (lieu physique). Pertinent pour un holding possédant plusieurs enseignes différentes.
- **(B) Deux niveaux** *(retenu)* : `Tenant` **est** le restaurant (au sens large : restaurant, maquis, hôtel, boulangerie...) → `Succursale` (lieu physique où ce restaurant opère). Un PDG multi-établissements gère un tenant avec plusieurs succursales.

**Choix retenu et validé : (B)**, pour deux raisons : d'une part, l'AMD ne mentionne jamais explicitement un niveau « marque » distinct du tenant ailleurs que dans le nom du module ; d'autre part, la section 5 de l'AMD énonce l'isolation par tenant comme la frontière naturelle (« chaque restaurant dispose de ses propres utilisateurs, employés, menus... »), ce qui correspond exactement au périmètre déjà donné à `Tenant` en Module 1. Un PDG possédant plusieurs enseignes différentes utiliserait plusieurs tenants distincts (cohérent avec la décision déjà prise en Module 1 pour le même cas de figure, BR-07).

### Ce que couvre concrètement le module

- Gestion des succursales d'un tenant : création, modification, désactivation, informations (nom, adresse, coordonnées, horaires d'ouverture, devise/langue locale si différente du défaut du tenant).
- Rattachement des employés (les `User` du Module 1) à une ou plusieurs succursales, avec un rôle par rattachement — active enfin la colonne `user_roles.succursale_id`, réservée mais non utilisée depuis le Module 1.
- Vue consolidée multi-succursales pour le PDG (liste, statuts, indicateurs de premier niveau — pas encore les rapports détaillés, qui relèvent du module Intelligence).

### Explicitement hors périmètre

- Le contenu métier de chaque succursale (menus, produits, stocks, tables, QR codes) → modules Catalogue et Opérations.
- Les rapports et statistiques par succursale → module Intelligence.
- La facturation/abonnement par succursale → module Finance.

## 1.2 Impacts sur les autres modules

| Module impacté | Nature de la dépendance |
|---|---|
| Module 1 (Auth & Tenants) | `user_roles.succursale_id` devient actif : un rôle peut désormais être scopé à une succursale précise plutôt qu'à tout le tenant. Aucune migration destructive requise (colonne déjà nullable). |
| Catalogue, Opérations, Commandes (futurs modules) | Toute donnée opérationnelle (menu, commande, table) référencera une `succursale_id`, en plus du `tenant_id` déjà obligatoire. |
| Intelligence / BI (futur) | Les rapports « par établissement » vs « consolidés tenant » (rôle PDG, AMD section 7) reposent sur le découpage posé ici. |

## 1.3 Rôles concernés (rappel AMD section 7)

- **Gérant** : « Pilotage d'un établissement » → rattaché à une seule succursale en pratique, même si le RBAC du Module 1 n'empêche pas plusieurs rattachements.
- **PDG** : « Pilotage multi-établissements » → vue consolidée sur toutes les succursales du tenant, sans rattachement à une succursale unique (son rôle reste tenant-wide, `succursale_id = null` dans `user_roles`).
- Tous les autres rôles opérationnels (Serveur, Cuisine, Caissier, Livreur...) seront, en pratique, rattachés à une succursale précise une fois ce module livré — mais ce module se contente de rendre le rattachement *possible* ; l'application effective par chaque module opérationnel viendra plus tard.

## 1.4 Definition of Done du Module 2

- [ ] Un Administrateur ou PDG peut créer, modifier et désactiver une succursale de son tenant.
- [ ] Un Administrateur/Gérant peut rattacher un employé existant à une succursale avec un rôle donné.
- [ ] Un utilisateur rattaché à une succursale ne voit/n'agit que dans le périmètre de cette succursale pour les actions qui le requièrent (règle appliquée par les modules consommateurs, ce module expose l'information).
- [ ] Un PDG obtient la liste de toutes les succursales de son tenant avec leur statut.
- [ ] Aucune fuite de données entre tenants (héritage direct de la règle absolue du Module 1 — les succursales sont une table tenant-scopée de plus, RLS incluse).
