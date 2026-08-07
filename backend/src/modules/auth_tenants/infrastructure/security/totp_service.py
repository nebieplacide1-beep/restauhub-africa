import secrets

import pyotp

from src.modules.auth_tenants.application.ports import TwoFactorService
from src.shared_kernel.security.symmetric_encryption import SymmetricEncryptor
from src.shared_kernel.security.token_hashing import hash_token


class TOTPService(TwoFactorService):
    """BR-17/BR-18 : TOTP (RFC 6238) via `pyotp`. Le secret est chiffré au
    repos (jamais stocké en clair) via `SymmetricEncryptor`."""

    def __init__(self, encryptor: SymmetricEncryptor) -> None:
        self._encryptor = encryptor

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def encrypt_secret(self, plain_secret: str) -> str:
        return self._encryptor.encrypt(plain_secret)

    def provisioning_uri(
        self, *, secret: str, account_name: str, issuer: str = "RestauHub Africa"
    ) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)

    def verify_code(self, *, encrypted_secret: str, code: str) -> bool:
        plain_secret = self._encryptor.decrypt(encrypted_secret)
        return pyotp.totp.TOTP(plain_secret).verify(code, valid_window=1)

    def generate_recovery_codes(self, *, count: int = 10) -> list[str]:
        return [secrets.token_hex(5) for _ in range(count)]

    def hash_recovery_code(self, code: str) -> str:
        return hash_token(code)
