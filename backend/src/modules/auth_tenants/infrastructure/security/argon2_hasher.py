from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.modules.auth_tenants.application.ports import Hasher


class Argon2Hasher(Hasher):
    """BR-08 : Argon2id, paramètres par défaut d'`argon2-cffi` (déjà alignés
    sur les recommandations OWASP)."""

    def __init__(self) -> None:
        self._ph = PasswordHasher()

    def hash(self, plain: str) -> str:
        return self._ph.hash(plain)

    def verify(self, *, plain: str, hashed: str) -> bool:
        try:
            return self._ph.verify(hashed, plain)
        except VerifyMismatchError:
            return False
