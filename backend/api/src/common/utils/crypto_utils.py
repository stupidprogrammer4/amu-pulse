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
    """
    Desc: Pre-hash a password with the pepper into a bcrypt-safe input.
    Args:
        password (str): Plaintext password.
        pepper (str): Server-side secret mixed into the digest.
    Returns:
        return (bytes): Base64-encoded HMAC-SHA256 digest.
    """
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
    """
    Desc: Hash a password with bcrypt over its peppered digest.
    Args:
        password (str): Plaintext password.
        pepper (str): Server-side secret mixed into the digest.
        rounds (int): bcrypt cost factor.
    Returns:
        return (str): The bcrypt hash string.
    """
    hashed = bcrypt.hashpw(_peppered(password, pepper), bcrypt.gensalt(rounds))
    return hashed.decode()


def verify_password(
    password: str,
    hashed: str,
    *,
    pepper: str = "",
) -> bool:
    """
    Desc: Check a plaintext password against a stored bcrypt hash.
    Args:
        password (str): Plaintext password to check.
        hashed (str): Stored bcrypt hash.
        pepper (str): Server-side secret mixed into the digest.
    Returns:
        return (bool): True when the password matches.
    """
    try:
        return bcrypt.checkpw(_peppered(password, pepper), hashed.encode())
    except ValueError:
        # a malformed/legacy hash is a non-match, never an error
        return False


def _fernet(key: str) -> Fernet:
    """
    Desc: Derive a Fernet cipher from an arbitrary-length key string.
    Args:
        key (str): Raw secret key.
    Returns:
        return (Fernet): Cipher bound to the derived key.
    """
    derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
    return Fernet(derived)


def encrypt(
    plaintext: str,
    key: str,
) -> str:
    """
    Desc: Encrypt a string with authenticated Fernet encryption.
    Args:
        plaintext (str): Value to encrypt.
        key (str): Raw secret key.
    Returns:
        return (str): The ciphertext token.
    """
    return _fernet(key).encrypt(plaintext.encode()).decode()


def decrypt(
    token: str,
    key: str,
) -> str:
    """
    Desc: Decrypt an encrypt() token, raising ValueError when it is invalid.
    Args:
        token (str): Ciphertext token produced by encrypt().
        key (str): Raw secret key.
    Returns:
        return (str): The decrypted plaintext.
    """
    try:
        return _fernet(key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("could not decrypt payload") from exc


def hash_sha256(value: str) -> str:
    """
    Desc: Deterministic digest for opaque tokens — not for passwords.
    Args:
        value (str): Value to digest.
    Returns:
        return (str): Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(value.encode()).hexdigest()


def secure_compare(
    a: str,
    b: str,
) -> bool:
    """
    Desc: Constant-time comparison — use when checking secrets or tokens.
    Args:
        a (str): First value.
        b (str): Second value.
    Returns:
        return (bool): True when both values are equal.
    """
    return hmac.compare_digest(a, b)
