"""Hachage à sens unique des tokens opaques (refresh tokens, tokens
d'invitation, tokens de réinitialisation) — jamais stockés en clair, jamais
réversibles, à la différence des secrets chiffrés (voir symmetric_encryption).
"""

from __future__ import annotations

import hashlib
import secrets


def generate_opaque_token(*, num_bytes: int = 32) -> str:
    return secrets.token_urlsafe(num_bytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
