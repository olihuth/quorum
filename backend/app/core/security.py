import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import get_settings


def hash_citizen_identifier(identifier: str) -> str:
    """Return an anonymized SHA-256 hash of a citizen identifier for LGPD compliance."""
    normalized = identifier.strip().lower().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${derived.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 salt$hash string."""
    try:
        salt, expected_hex = stored_hash.split("$", 1)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(derived.hex(), expected_hex)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def create_access_token(user_id: int, email: str, expires_minutes: int | None = None) -> str:
    """Create a signed HMAC-SHA256 JWT bearer token."""
    settings = get_settings()
    ttl_minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + ttl_minutes * 60,
    }
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(settings.jwt_secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    """Validate signature and expiration of an HMAC-SHA256 JWT token."""
    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        return None
    encoded_header, encoded_payload, encoded_sig = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_sig = hmac.new(settings.jwt_secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(encoded_sig)
        if not hmac.compare_digest(actual_sig, expected_sig):
            return None
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload
