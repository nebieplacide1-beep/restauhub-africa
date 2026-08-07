# 2. Règles métier — Authentification & gestion des tenants

## 2.1 Tenants

- **BR-01** : Un tenant représente un établissement (ou un groupe d'établissements géré par un même PDG) inscrit sur la plateforme. Il possède : un nom, un identifiant unique (`slug`), un pays, une devise par défaut, une langue par défaut, un statut (`en_essai`, `actif`, `suspendu`, `résilié`), une date de création.
- **BR-02** : La création d'un tenant crée automatiquement son premier utilisateur avec le rôle **Administrateur**. Il n'existe pas de tenant sans au moins un Administrateur actif.
- **BR-03** : Un tenant suspendu conserve ses données mais bloque toute authentification de ses utilisateurs (sauf Super Administrateur) et toute écriture via l'API.
- **BR-04** : Un `slug` de tenant est unique globalement, généré à partir du nom, en minuscules, sans accents ni espaces, avec suffixe numérique en cas de collision.
- **BR-05** *(règle absolue, héritée de l'AMD section 5)* : Aucune donnée n'est visible entre tenants. Toute requête (API, base de données, cache, tâches asynchrones) est filtrée par `tenant_id`. Cette isolation est appliquée à deux niveaux indépendants : filtrage applicatif systématique **et** Row-Level Security PostgreSQL (défense en profondeur — voir [03-architecture.md](./03-architecture.md#isolation-multi-tenant)).

## 2.2 Comptes utilisateurs

- **BR-06** : Un utilisateur s'identifie par un email **ou** un numéro de téléphone (l'un des deux est obligatoire, les deux peuvent être renseignés). Le marché africain visé justifie de ne pas imposer l'email comme identifiant unique.
- **BR-07** : Un utilisateur appartient à un seul tenant. Une même personne physique gérant plusieurs établissements (PDG multi-tenant) possède un compte distinct par tenant — le rattachement multi-tenant d'un même compte est explicitement hors périmètre v1 (voir décisions à valider).
- **BR-08** : Mot de passe : 10 caractères minimum, au moins une majuscule, un chiffre, un symbole. Haché avec Argon2id (jamais stocké en clair, jamais journalisé).
- **BR-09** : Un compte est créé soit par inscription d'un nouveau tenant (l'utilisateur devient Administrateur), soit par invitation d'un Administrateur/Gérant existant (l'utilisateur reçoit un lien d'activation à durée de vie limitée — 72h).
- **BR-10** : Un compte non activé sous 72h après invitation voit son lien expirer ; l'invitation peut être renvoyée par un Administrateur.
- **BR-11** : Un Administrateur peut désactiver un utilisateur de son tenant. Un utilisateur désactivé ne peut plus s'authentifier ; ses données historiques (commandes prises, ventes réalisées) sont conservées pour la traçabilité comptable.
- **BR-12** : Après 5 échecs de connexion consécutifs sur un même compte en moins de 15 minutes, le compte est verrouillé temporairement 15 minutes (protection brute-force, indépendante du rate limiting réseau).

## 2.3 Authentification

- **BR-13** : L'authentification retourne un token d'accès JWT (durée de vie 15 minutes) et un refresh token (durée de vie 30 jours, rotation à chaque utilisation, révocable individuellement).
- **BR-14** : Le token d'accès contient : `user_id`, `tenant_id`, `role`, liste des permissions effectives, date d'expiration. Il ne contient aucune donnée personnelle sensible (email, téléphone).
- **BR-15** : La révocation d'un refresh token (déconnexion explicite, changement de mot de passe, désactivation du compte) invalide immédiatement toute nouvelle tentative de rafraîchissement ; le token d'accès déjà émis reste valide au maximum 15 minutes (fenêtre de risque acceptée et documentée).
- **BR-16** : Le changement de mot de passe révoque tous les refresh tokens actifs de l'utilisateur, sur tous ses appareils.

## 2.4 Authentification à deux facteurs (2FA)

- **BR-17** : Le 2FA (TOTP, applications type Google Authenticator/Authy) est **obligatoire** pour les rôles Administrateur, Super Administrateur, PDG et Comptable (accès à des données sensibles ou à des actions financières). Il est **optionnel mais recommandé** pour les autres rôles.
- **BR-18** : L'activation du 2FA génère 10 codes de récupération à usage unique, affichés une seule fois, pour couvrir la perte de l'appareil d'authentification.
- **BR-19** : La désactivation du 2FA nécessite une réauthentification (mot de passe + code 2FA valide), pour éviter qu'un accès compromis ne désactive lui-même la protection.

## 2.5 Rôles et permissions (RBAC)

- **BR-20** : Un rôle est un ensemble nommé de permissions. Les 12 rôles de l'AMD sont créés en données de référence à l'installation de la plateforme et ne peuvent pas être supprimés (seules leurs permissions par défaut peuvent être ajustées par tenant).
- **BR-21** : Une permission s'exprime sous la forme `domaine:action` (ex. `menu:write`, `commandes:read`, `rapports:export`). Le détail du modèle est dans [05-modele-donnees.md](./05-modele-donnees.md).
- **BR-22** : Un utilisateur peut cumuler plusieurs rôles au sein d'un même tenant (ex. Serveur + Caissier dans un petit établissement). Ses permissions effectives sont l'union des permissions de tous ses rôles.
- **BR-23** : Un Administrateur peut personnaliser, pour son tenant uniquement, l'ensemble de permissions attaché à un rôle (permissions granulaires, AMD section 10) — sans jamais dépasser les permissions maximales autorisées par son plan d'abonnement (contrôle appliqué au niveau application, indépendant du RBAC lui-même).
- **BR-24** : Le rôle Super Administrateur n'est jamais rattaché à un tenant : il opère au niveau plateforme et n'est pas soumis au filtrage `tenant_id`.

### Matrice des permissions par défaut

| Rôle | Domaines de permission par défaut (lecture/écriture selon le domaine) |
|---|---|
| Client | commandes (propres), réservations (propres), fidélité (propre), avis |
| Serveur | commandes (établissement), tables |
| Cuisine | commandes (statuts de préparation) |
| Caissier | commandes, paiements, caisse |
| Gérant | personnel, stocks, produits, promotions, rapports (établissement) |
| PDG | rapports (tous établissements du tenant), finance (lecture) |
| Comptable | finance, factures, rapports financiers |
| Livreur | livraisons (assignées) |
| Annonceur | publicités (propres) |
| Fournisseur | marketplace (catalogue propre, commandes reçues) |
| Administrateur | gestion complète du tenant : utilisateurs, rôles, paramètres, abonnement |
| Super Administrateur | gestion globale : tenants, commissions, monitoring, support |

Cette matrice est le jeu de données seed ; elle n'est pas figée dans le code (BR-21/BR-23).

## 2.6 Audit

- **BR-25** : Sont journalisés au minimum : connexion réussie, échec de connexion, activation/désactivation 2FA, création/désactivation d'utilisateur, changement de rôle ou de permission, suspension/réactivation de tenant. Chaque entrée conserve `tenant_id`, `user_id` (ou `null` si anonyme), action, horodatage, adresse IP, résultat.
- **BR-26** : Les journaux d'audit sont immuables (pas de mise à jour ni suppression applicative) et conservés au minimum 12 mois.

## 2.7 Rôle de l'IA sur ce module

Conformément à l'AMD (section 9), aucune automatisation IA n'intervient sur ce module : la création de comptes, l'attribution de rôles et la suspension de tenants restent des actions humaines exclusivement.
