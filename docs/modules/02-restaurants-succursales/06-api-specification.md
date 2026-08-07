# 6. Spécification API — Restaurants & succursales

Convention identique au Module 1 : base `/api/v1`, JSON, erreurs `{ "error": { "code": "...", "message": "..." } }`, `Authorization: Bearer <access_token>` requis sur toutes les routes (ce module n'a aucune route publique, à la différence du Module 1).

**Nouvelle permission** `succursales:manage`, à ajouter au catalogue du Module 1 lors de l'implémentation (BR2-\*) et accordée par défaut à Administrateur, PDG et Gérant — pour ce dernier, une vérification de portée opérationnelle s'ajoute (voir ci-dessous), la permission seule ne suffit pas.

## 6.1 Succursales

| Méthode | Route | Permission | Description |
|---|---|---|---|
| GET | `/succursales` | `succursales:manage` | Liste les succursales visibles par l'appelant — toutes celles du tenant si rattachement tenant-wide (PDG/Administrateur, BR2-13), seulement celles assignées sinon (Gérant, BR2-14). |
| POST | `/succursales` | `succursales:manage`, rattachement tenant-wide requis | Crée une succursale. |
| GET | `/succursales/{id}` | `succursales:manage` | Détail d'une succursale (dans le périmètre de l'appelant). |
| PATCH | `/succursales/{id}` | `succursales:manage`, dans le périmètre de l'appelant | Modifie les informations d'une succursale. |
| POST | `/succursales/{id}/deactivate` | `succursales:manage`, rattachement tenant-wide requis | BR2-04/BR2-05. |
| POST | `/succursales/{id}/reactivate` | `succursales:manage`, rattachement tenant-wide requis | — |

## 6.2 Détail des endpoints clés

### `POST /succursales`
**Requête**
```json
{
  "name": "Chez Awa - Plateau",
  "address_line": "12 Avenue Chardy",
  "city": "Abidjan",
  "country": "CI",
  "default_currency": "XOF",
  "default_locale": "fr",
  "phone_number": "+2250700000001",
  "opening_hours": {
    "lundi": [{"ouverture": "08:00", "fermeture": "22:00"}],
    "dimanche": []
  }
}
```
**Réponse `201`** : la succursale créée, `status = "active"`.
**Erreurs** : `403 forbidden` (rattachement non tenant-wide), `422 validation_error`.

---

### `GET /succursales`
**Réponse `200`** : liste filtrée selon le périmètre de l'appelant (BR2-13/BR2-14) — jamais une erreur `403`, une liste vide au pire (ex. un Gérant sans aucun rattachement actif).

---

### `PATCH /succursales/{id}`
**Requête** : sous-ensemble des champs de création (`name`, `address_line`, `opening_hours`, `phone_number`, ...).
**Réponse `200`**.
**Erreurs** : `403 forbidden` si l'appelant n'est ni tenant-wide ni rattaché à cette succursale précise ; `404 not_found` si la succursale n'existe pas **ou** appartient à un autre tenant (même politique de non-divulgation que le Module 1).

## 6.3 Personnel d'une succursale

| Méthode | Route | Permission | Description |
|---|---|---|---|
| GET | `/succursales/{id}/staff` | `succursales:manage`, dans le périmètre de l'appelant | Liste les employés rattachés à cette succursale, avec leur(s) rôle(s). |
| POST | `/succursales/{id}/staff` | `succursales:manage`, dans le périmètre de l'appelant | Rattache un employé existant (`user_id`) à cette succursale avec un rôle (`role_code`, BR2-07). |
| POST | `/succursales/{id}/staff/remove` | `succursales:manage`, dans le périmètre de l'appelant | Retire un rattachement précis (`user_id`, `role_code`) — BR2-12 : ne désactive jamais le compte utilisateur lui-même. |

### `POST /succursales/{id}/staff`
**Requête** : `{ "user_id": "...", "role_code": "serveur" }`
**Réponse `204`**.
**Erreurs** : `404 user_not_found` (l'utilisateur doit appartenir au même tenant, sinon traité comme introuvable — même politique de non-divulgation), `422 validation_error` (rôle inconnu), `409 conflict` (rattachement déjà existant pour ce couple utilisateur/rôle/succursale).

## 6.4 Codes d'erreur additionnels

Aucun nouveau code par rapport à la liste du Module 1 (06-api-specification.md#66) — ce module réutilise `not_found`, `forbidden`, `validation_error`, `conflict`.
