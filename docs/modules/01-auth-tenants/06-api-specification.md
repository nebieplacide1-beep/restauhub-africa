# 6. Spécification API — Authentification & gestion des tenants

Convention : base `/api/v1`, JSON uniquement, erreurs au format `{ "error": { "code": "...", "message": "..." } }`. L'en-tête `Authorization: Bearer <access_token>` est requis sur tous les endpoints sauf ceux listés en section 6.1.

## 6.1 Endpoints publics (sans authentification)

| Méthode | Route | Description |
|---|---|---|
| POST | `/tenants` | Inscription d'un nouvel établissement (crée le tenant + son Administrateur). |
| POST | `/auth/login` | Connexion (email ou téléphone + mot de passe). |
| POST | `/auth/2fa/verify` | Deuxième étape de connexion si le compte a le 2FA activé. |
| POST | `/auth/refresh` | Échange un refresh token contre un nouveau couple access/refresh. |
| POST | `/auth/password/forgot` | Démarre une réinitialisation de mot de passe. |
| POST | `/auth/password/reset` | Termine la réinitialisation avec le token reçu par email/SMS. |
| GET | `/invitations/{token}` | Consulte une invitation en attente (pour afficher le formulaire d'activation). |
| POST | `/invitations/{token}/accept` | Active le compte invité (définit le mot de passe). |

## 6.2 Détail des endpoints clés

### `POST /tenants`
Inscription libre-service.

**Requête**
```json
{
  "tenant_name": "Le Bon Maquis",
  "country": "CI",
  "default_currency": "XOF",
  "default_locale": "fr",
  "admin_email": "owner@lebonmaquis.ci",
  "admin_phone_number": "+225070000000",
  "admin_password": "Str0ng!Passw0rd"
}
```
`admin_email` ou `admin_phone_number` requis (au moins un), règle BR-06.

**Réponse `201`**
```json
{ "tenant": { "id": "...", "slug": "le-bon-maquis", "status": "en_essai" },
  "user": { "id": "...", "role": "administrateur" } }
```

**Erreurs** : `409 slug_conflict` (nom déjà très proche d'un tenant existant, rare), `422 validation_error`.

---

### `POST /auth/login`

**Requête**
```json
{ "identifier": "owner@lebonmaquis.ci", "password": "Str0ng!Passw0rd" }
```

**Réponse `200`** (2FA désactivé)
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900 }
```

**Réponse `202`** (2FA activé, BR-17)
```json
{ "challenge_token": "...", "requires_two_factor": true }
```

**Erreurs** : `401 invalid_credentials`, `423 account_locked` (BR-12), `403 tenant_suspended` (BR-03).

---

### `POST /auth/2fa/verify`
**Requête** : `{ "challenge_token": "...", "code": "123456" }`
**Réponse `200`** : identique à la réponse de connexion sans 2FA.
**Erreurs** : `401 invalid_code`, `410 challenge_expired`.

---

### `POST /auth/refresh`
**Requête** : `{ "refresh_token": "..." }`
**Réponse `200`** : nouveau couple `access_token`/`refresh_token` (rotation, BR-13).
**Erreurs** : `401 invalid_or_revoked_token` — si le token présenté a déjà été consommé, **toute la chaîne de tokens de la session est révoquée** (détection de réutilisation, section 3.4).

---

### `POST /auth/logout`
*Authentifié.* Révoque le refresh token courant. **Réponse `204`**.

---

### `GET /auth/me`
*Authentifié.* Retourne l'utilisateur courant, son tenant, son rôle et ses permissions effectives.

---

### `POST /auth/2fa/enable`
*Authentifié.* Démarre l'activation du 2FA : retourne un secret TOTP + QR code (à confirmer via `POST /auth/2fa/confirm` avec un premier code valide, qui déclenche la génération des 10 codes de récupération, BR-18).

### `POST /auth/2fa/disable`
*Authentifié, nécessite mot de passe + code 2FA courant dans le corps de la requête* (BR-19).

## 6.3 Gestion des utilisateurs du tenant

*Toutes les routes de cette section nécessitent la permission `users:manage`, typiquement Administrateur.*

| Méthode | Route | Description |
|---|---|---|
| GET | `/users` | Liste les utilisateurs du tenant courant (pagination, filtre par rôle/statut). |
| POST | `/users/invitations` | Invite un nouvel utilisateur (email/téléphone + rôle initial). Déclenche un email/SMS avec lien d'activation (BR-09). |
| POST | `/users/invitations/{id}/resend` | Renvoie une invitation expirée (BR-10). |
| PATCH | `/users/{id}/roles` | Modifie les rôles d'un utilisateur (ajout/retrait, BR-22). |
| POST | `/users/{id}/deactivate` | Désactive un utilisateur (BR-11). |
| POST | `/users/{id}/reactivate` | Réactive un utilisateur désactivé. |

## 6.4 Rôles & permissions

| Méthode | Route | Description |
|---|---|---|
| GET | `/roles` | Liste les 12 rôles système avec leurs permissions effectives pour le tenant courant. |
| PATCH | `/roles/{code}/permissions` | Surcharge les permissions d'un rôle pour le tenant courant (BR-23, crée des lignes `role_permissions` avec `tenant_id`). |
| GET | `/permissions` | Liste toutes les permissions disponibles dans le système (catalogue, pour construire l'UI de gestion des rôles). |

## 6.5 Super Administrateur

*Permission `platform:admin`, jamais rattachée à un tenant (BR-24).*

| Méthode | Route | Description |
|---|---|---|
| GET | `/admin/tenants` | Liste tous les tenants de la plateforme (recherche, filtre par statut). |
| GET | `/admin/tenants/{id}` | Détail d'un tenant. |
| POST | `/admin/tenants/{id}/suspend` | Suspend un tenant (BR-03). |
| POST | `/admin/tenants/{id}/reactivate` | Réactive un tenant suspendu. |

## 6.6 Codes d'erreur communs

| Code HTTP | `error.code` | Signification |
|---|---|---|
| 400 | `bad_request` | Corps de requête malformé. |
| 401 | `unauthenticated` | Token absent, invalide ou expiré. |
| 403 | `forbidden` | Authentifié mais permission manquante, ou tenant suspendu. |
| 404 | `not_found` | Ressource inexistante **ou appartenant à un autre tenant** (jamais de distinction — évite de révéler l'existence de données d'un autre tenant). |
| 409 | `conflict` | Ex. email déjà utilisé dans ce tenant. |
| 422 | `validation_error` | Échec de validation Pydantic. |
| 423 | `account_locked` | Verrouillage brute-force (BR-12). |
| 429 | `rate_limited` | Rate limiting Redis dépassé (section 3.4). |
