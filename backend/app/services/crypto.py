"""Symmetric encryption for storing secrets (e.g. LinkedIn cookie) in DB."""
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet

from app.config import settings


def _get_key() -> bytes:
    """Derive a 32-byte Fernet key from the app secret."""
    h = hashlib.sha256(settings.app_secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(h)


def encrypt(plaintext: Optional[str]) -> str:
    if not plaintext:
        return ""
    f = Fernet(_get_key())
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: Optional[str]) -> str:
    if not ciphertext:
        return ""
    f = Fernet(_get_key())
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
