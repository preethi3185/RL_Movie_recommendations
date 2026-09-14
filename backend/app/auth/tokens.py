from datetime import datetime, timedelta, timezone
import os

import jwt

# HS256 (HMAC with SHA-256) is a symmetric algorithm, meaning the same secret
# is used for both signing and verifying the token. It is efficient and
# suitable for internal application tokens.
JWT_ALGORITHM = "HS256"

# The secret key is the foundation of JWT security. If compromised, anyone
# can forge tokens and impersonate users. In production, this MUST be a
# complex random string stored in an environment variable.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "movieverse-development-secret-change-me")

# Token expiration prevents "forever tokens". If a token is stolen, it
# only grants access for a limited window (e.g., 60 minutes).
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(user_id: str) -> str:
    """
    Generates a signed JWT access token for a user.

    JWT Claims:
    - 'sub' (Subject): The unique identifier for the user.
    - 'iat' (Issued At): When the token was created.
    - 'exp' (Expiration): When the token becomes invalid.
    - 'type': Distinguishes between access and refresh tokens.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Validates a JWT and extracts the user identity.

    The decode process verifies the signature using the JWT_SECRET_KEY.
    If the token was modified or has expired, PyJWT raises a PyJWTError.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        # Invalid signature, expired token, or malformed JWT.
        return None

    # Safety check: ensure the token is an 'access' token and has a subject.
    if payload.get("type") != "access" or not payload.get("sub"):
        return None

    return str(payload["sub"])
