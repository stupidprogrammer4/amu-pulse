from __future__ import annotations

import base64
import hashlib
import hmac

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_BCRYPT_ROUNDS = 12


def _peppered(
    password: str,
    pepper: str,
) -> bytes:
    digest = hmac.new(
        pepper.encode(), password.encode(), hashlib.sha256
    ).digest()
    return base64.b64encode(digest)


def hash_password(
    password: str,
    *,
    pepper: str = "",
    rounds: int = DEFAULT_BCRYPT_ROUNDS,
) -> str:
    hashed = bcrypt.hashpw(_peppered(password, pepper), bcrypt.gensalt(rounds))
    return hashed.decode()


def verify_password(
    password: str,
    hashed: str,
    *,
    pepper: str = "",
) -> bool:
    try:
        return bcrypt.checkpw(_peppered(password, pepper), hashed.encode())
    except ValueError:
        return False


def _fernet(key: str) -> Fernet:
    derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
    return Fernet(derived)


def encrypt(
    plaintext: str,
    key: str,
) -> str:
    return _fernet(key).encrypt(plaintext.encode()).decode()


def decrypt(
    token: str,
    key: str,
) -> str:
    try:
        return _fernet(key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("could not decrypt payload") from exc


def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def secure_compare(
    a: str,
    b: str,
) -> bool:
    return hmac.compare_digest(a, b)
