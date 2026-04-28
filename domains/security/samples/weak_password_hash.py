# Vulnerable example: Weak password hashing (MD5/SHA1)
# WARNING: This is intentionally vulnerable code for educational purposes only.

import hashlib


def hash_password(password: str) -> str:
    """Hash a password using MD5 — insecure for password storage."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against an MD5 hash."""
    return hashlib.md5(password.encode()).hexdigest() == hashed


def hash_password_sha1(password: str) -> str:
    """Hash a password using SHA1 — also insecure for password storage."""
    return hashlib.sha1(password.encode()).hexdigest()
