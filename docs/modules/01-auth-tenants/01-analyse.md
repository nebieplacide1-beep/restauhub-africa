# 1. Analyse — Authentification & gestion des tenants

## 1.1 Pourquoi ce module en premier

Tous les autres modules (Restaurants, Catalogue, Commandes, Paiements, etc.) dépendent de deux notions qui n'existent nulle part ailleurs dans la plateforme :

- **Qui parle** : un utilisateur authentifié, avec un rôle et des permissions.
- **Pour le compte de qui** : un tenant (l'établissement / l'organisation), qui isole ses données de tous les autres.

Sans ce socle, aucune requête métier ne peut être écrite correctement : chaque module futur consommera `current_user` et `current_tenant` fournis par ce module.

## 1.2 Périmètre du Module 1

**Inclus :**
- Création d'un tenant (inscription d'un établissement sur la plateforme)
- Authentification (email ou téléphone + mot de passe), JWT + refresh token
- Authentification à deux facteurs (2FA, TOTP)
- Gestion des utilisateurs d'un tenant (invitation, activation, désactivation)
- Rôles et permissions (RBAC) pour les 12 rôles définis dans l'AMD (section 7)
- Journalisation d'audit des événements d'authentification et de gestion des accès
- Espace Super Administrateur pour la gestion globale des tenants (suspension, réactivation)

**Explicitement hors périmètre (renvoyé aux modules suivants) :**
- Notion de « succursale » et rattachement d'un rôle à une succursale précise → Module 2 (Restaurants & succursales). Le Module 1 attribue les rôles au niveau du tenant ; l'extension au niveau succursale est prévue comme point d'ouverture (voir [03-architecture.md](./03-architecture.md#évolution-vers-le-multi-succursale)).
- Détails métier des rôles (ex. gestion des stocks pour le Gérant, tableau de bord PDG) → modules métier correspondants. Le Module 1 fournit uniquement l'identité, le rôle et les permissions ; il n'implémente pas les écrans/fonctionnalités propres à chaque rôle.
- Paiement des abonnements SaaS par tenant → Module Finance (section 6 de l'AMD).

## 1.3 Impacts sur les autres modules

| Module impacté | Nature de la dépendance |
|---|---|
| Tous les modules métier | Toute requête API doit recevoir un utilisateur authentifié + un `tenant_id` ; toute requête base de données doit être filtrée par `tenant_id` (règle absolue, AMD section 5). |
| Restaurants & succursales (Module 2) | Consommera `tenant_id` comme clé étrangère racine et étendra le modèle de rôle avec un rattachement optionnel à une succursale. |
| Gouvernance / Audit | Le modèle d'audit log posé ici (table `audit_logs`) sera réutilisé par tous les modules pour tracer leurs propres événements métier. |
| API Publique | Le mécanisme d'API keys par tenant (hors périmètre v1, voir décisions à valider) conditionnera l'accès externe futur. |

## 1.4 Rôles couverts (rappel AMD section 7)

Client, Serveur, Cuisine, Caissier, Gérant, PDG, Comptable, Livreur, Annonceur, Fournisseur, Administrateur, Super Administrateur.

Le Module 1 crée ces 12 rôles comme données de référence (seed) avec un jeu de permissions par défaut dérivé des « Fonctionnalités clés par rôle » de l'AMD. Le détail des permissions est dans [02-regles-metier.md](./02-regles-metier.md#matrice-des-permissions-par-défaut).

## 1.5 Definition of Done du Module 1

- [ ] Un établissement peut s'inscrire et obtenir un compte Administrateur pour son tenant.
- [ ] Un utilisateur peut se connecter (email/téléphone + mot de passe), avec ou sans 2FA, et obtenir un token exploitable par les autres modules.
- [ ] Un Administrateur peut inviter des utilisateurs à son tenant et leur attribuer un rôle.
- [ ] Aucune requête ne peut retourner des données d'un autre tenant (vérifié par des tests d'isolation dédiés, voir Tests).
- [ ] Le Super Administrateur peut lister, suspendre et réactiver un tenant.
- [ ] Chaque connexion, échec de connexion, changement de rôle et changement de permission est audité.
