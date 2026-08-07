"""Exceptions métier communes, indépendantes de FastAPI.

Chaque exception porte un `code` stable (utilisé dans `error.code` des
réponses API, voir docs/modules/01-auth-tenants/06-api-specification.md)
et le code HTTP à lui associer. Le mapping vers la réponse HTTP se fait
dans un exception handler global (voir `main.py`), jamais dans les use
cases eux-mêmes.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base de toutes les erreurs métier du domaine `auth_tenants`."""

    code: str = "domain_error"
    http_status: int = 400

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404


class ConflictError(DomainError):
    code = "conflict"
    http_status = 409


class ValidationError(DomainError):
    code = "validation_error"
    http_status = 422


class UnauthenticatedError(DomainError):
    code = "unauthenticated"
    http_status = 401


class ForbiddenError(DomainError):
    code = "forbidden"
    http_status = 403


class AccountLockedError(DomainError):
    code = "account_locked"
    http_status = 423


class RateLimitedError(DomainError):
    code = "rate_limited"
    http_status = 429
