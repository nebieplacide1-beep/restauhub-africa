"""Chiffrement symétrique générique (Fernet), utilisé pour tout secret devant
rester déchiffrable (ex. secret TOTP) — à distinguer du hachage à sens unique
(mots de passe, refresh tokens), qui ne doit jamais être réversible.
"""

from __future__ import annotations

from cryptography.fernet import Fernet


class SymmetricEncryptor:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()
