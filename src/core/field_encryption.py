"""
Encrypt/decrypt short strings at rest (e.g. connector credential JSON).

Production: set INFRA_ENCRYPTION_KEY to a Fernet key (see `fernet.Fernet.generate_key()`).
Fallback: derive a Fernet-compatible key from SECRET_KEY (adequate for dev only).
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from src.core.config import settings


def _fernet_from_secret(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def _get_fernet() -> Fernet:
    raw = settings.infra_encryption_key or os.environ.get("INFRA_ENCRYPTION_KEY")
    if raw and isinstance(raw, str) and raw.strip():
        return Fernet(raw.strip().encode("ascii"))
    return _fernet_from_secret(settings.secret_key)


def encrypt_string(plaintext: str) -> str:
    """Return url-safe base64 ciphertext (ascii str)."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_string(ciphertext: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt credential blob") from exc
