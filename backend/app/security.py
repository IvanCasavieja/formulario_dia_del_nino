import time
import uuid

import jwt

from app.config import get_settings

settings = get_settings()

UPLOAD_TOKEN_PURPOSE = "upload_confirm"
ADMIN_TOKEN_ROLE = "admin"
JURADO_TOKEN_ROLE = "jurado"


class TokenError(Exception):
    """Base class for all upload/admin token verification failures."""


class TokenExpired(TokenError):
    pass


class TokenInvalid(TokenError):
    pass


class TokenSubmissionMismatch(TokenInvalid):
    pass


def create_upload_token(submission_id: str, video_key: str, fields: dict) -> str:
    """`fields` carries the submitted form data (parent/child names, cedulas, email,
    phone, terms_accepted) across the create -> confirm-upload round trip. There's no
    database to persist it in between - Salesforce is the only store, and it isn't
    written to until confirm-upload, so the token itself is where this lives for the
    ~30 minute upload window. Signed and short-lived, same as the rest of this token."""
    now = int(time.time())
    payload = {
        "sub": submission_id,
        "purpose": UPLOAD_TOKEN_PURPOSE,
        "video_key": video_key,
        "fields": fields,
        "iat": now,
        "exp": now + settings.UPLOAD_TOKEN_TTL_SECONDS,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.UPLOAD_TOKEN_SECRET, algorithm="HS256")


def decode_upload_token(token: str, expected_submission_id: str) -> dict:
    try:
        claims = jwt.decode(token, settings.UPLOAD_TOKEN_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise TokenExpired("upload_token_expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalid("invalid_upload_token") from e

    if claims.get("purpose") != UPLOAD_TOKEN_PURPOSE:
        raise TokenInvalid("invalid_upload_token")
    if claims.get("sub") != expected_submission_id:
        raise TokenSubmissionMismatch("token_submission_mismatch")
    return claims


def create_admin_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "admin",
        "role": ADMIN_TOKEN_ROLE,
        "iat": now,
        "exp": now + settings.ADMIN_SESSION_TTL_SECONDS,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.ADMIN_JWT_SECRET, algorithm="HS256")


def decode_admin_token(token: str) -> dict:
    try:
        claims = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise TokenExpired("admin_token_expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalid("invalid_admin_token") from e

    if claims.get("role") != ADMIN_TOKEN_ROLE:
        raise TokenInvalid("invalid_admin_token")
    return claims


def create_jurado_token(jurado_id: str) -> str:
    """Same shape/secret as create_admin_token (both are internal-panel sessions, not
    exposed to end users the way the upload token is) - the role claim, not a separate
    secret, is what keeps a jurado token from being accepted as an admin token or vice
    versa (see require_jurado/require_admin in app/deps.py)."""
    now = int(time.time())
    payload = {
        "sub": jurado_id,
        "role": JURADO_TOKEN_ROLE,
        "iat": now,
        "exp": now + settings.ADMIN_SESSION_TTL_SECONDS,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.ADMIN_JWT_SECRET, algorithm="HS256")


def decode_jurado_token(token: str) -> dict:
    try:
        claims = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise TokenExpired("jurado_token_expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalid("invalid_jurado_token") from e

    if claims.get("role") != JURADO_TOKEN_ROLE:
        raise TokenInvalid("invalid_jurado_token")
    return claims
