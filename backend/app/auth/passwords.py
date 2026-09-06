from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a non-empty password with Argon2id."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must not be empty.")
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Safely verify a password against an Argon2id hash."""
    if not isinstance(password, str) or not password:
        return False
    if not isinstance(password_hash, str) or not password_hash:
        return False
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False
