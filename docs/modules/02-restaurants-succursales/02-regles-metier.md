# 2. Règles métier — Restaurants & succursales

> Numérotation `BR2-*` pour ce module (distincte de `BR-*` du Module 1), afin qu'une référence croisée future ne soit jamais ambiguë entre modules.

## 2.1 Succursales

- **BR2-01** : Une succursale appartient à un seul tenant, jamais partagée (héritage direct de la règle absolue du Module 1, BR-05).
- **BR2-02** : Une succursale possède : un nom, une adresse complète (rue, ville, pays), un pays, une devise et une langue par défaut (indépendants de ceux du tenant — un même tenant peut opérer des succursales dans plusieurs pays, ex. une enseigne présente en Côte d'Ivoire et au Sénégal), un statut, des horaires d'ouverture, des coordonnées de contact.
- **BR2-03** : Un tenant peut exister sans aucune succursale (ex. juste après inscription, en cours de configuration) — ce module n'ajoute aucune contrainte sur les transitions de statut du tenant définies au Module 1.
- **BR2-04** : Statut d'une succursale : `active`, `inactive`, `fermeture_temporaire`. Une succursale `inactive` ou en `fermeture_temporaire` n'apparaît plus dans les futures interfaces client (module Croissance) mais conserve tout son historique.
- **BR2-05** : La désactivation d'une succursale est une suppression logique : l'historique (commandes, employés y ayant été rattachés) est conservé pour la traçabilité comptable (cohérent avec BR-11 du Module 1).
- **BR2-06** : Les horaires d'ouverture sont définis par jour de la semaine (créneaux ouverture/fermeture, plusieurs créneaux possibles par jour pour gérer les coupures). Le calcul « ouvert maintenant » est dérivé à la volée, jamais stocké.

## 2.2 Employés et rattachement aux succursales

- **BR2-07** : Un employé est un `User` du Module 1 auquel s'ajoute un rattachement à une ou plusieurs succursales via `user_roles.succursale_id` (colonne réservée par le Module 1, activée ici).
- **BR2-08** : `succursale_id = null` sur un rattachement de rôle signifie que ce rôle s'applique à **tout le tenant** (tous les établissements) — c'est le cas normal du rôle PDG (AMD section 7 : « pilotage multi-établissements ») et de l'Administrateur.
- **BR2-09** : `succursale_id` renseigné restreint l'application opérationnelle de ce rôle à cette succursale précise — c'est le cas normal des rôles Gérant, Serveur, Cuisine, Caissier, Livreur (AMD section 7 : le Gérant pilote « un établissement »).
- **BR2-10** : Un même utilisateur peut être rattaché à plusieurs succursales du même tenant, avec le même rôle ou des rôles différents selon la succursale (ex. Gérant de la succursale A, simple Serveur en renfort à la succursale B).
- **BR2-11** : Le rattachement à une succursale ne modifie pas les permissions accordées par le rôle (celles-ci restent résolues au niveau tenant, BR-21/BR-23 du Module 1) — il ne fait que délimiter le **périmètre opérationnel** dans lequel ce rôle s'exerce. Ce sont les modules opérationnels futurs (Catalogue, Commandes...) qui appliqueront ce périmètre lors de leurs propres vérifications.
- **BR2-12** : Retirer le dernier rattachement d'un utilisateur à une succursale ne désactive pas son compte (BR-11 du Module 1 reste le seul mécanisme de désactivation) ; l'utilisateur reste actif mais n'a plus de périmètre opérationnel tant qu'aucun nouveau rattachement n'est créé.

## 2.3 Consultation multi-succursales

- **BR2-13** : Un PDG (rattachement tenant-wide, BR2-08) obtient la liste de toutes les succursales actives et inactives de son tenant, avec leur statut — sans avoir besoin d'un rattachement explicite à chacune.
- **BR2-14** : Un Gérant ne voit que les succursales auxquelles il est explicitement rattaché.

## 2.4 Dépendances futures (hors périmètre, pour information)

- Le nombre maximal de succursales par tenant pourra être limité par le plan d'abonnement (module Finance) — contrôle applicatif à ajouter lors de la livraison du module Finance, pas dans ce module.
- Les rapports consolidés par succursale ou par tenant (module Intelligence) consommeront le découpage posé ici sans le modifier.
