import hashlib
import secrets

from pwdlib import PasswordHash
from werkzeug.security import check_password_hash

_hasher = PasswordHash.recommended()  # argon2id
# Verified against when the user doesn't exist, so response time doesn't reveal valid names.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(24))
# Hashes created by the original Flask version (werkzeug scrypt/pbkdf2).
_LEGACY_PREFIXES = ('scrypt:', 'pbkdf2:')


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored: str | None) -> tuple[bool, str | None]:
    """Return (valid, new_hash). new_hash is set when the stored hash should be upgraded."""
    if stored is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False, None
    if stored.startswith(_LEGACY_PREFIXES):
        valid = check_password_hash(stored, password)
        return valid, hash_password(password) if valid else None
    return _hasher.verify_and_update(password, stored)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def same_token(given: str, expected: str) -> bool:
    return secrets.compare_digest(given.encode(), expected.encode())
