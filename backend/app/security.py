import time
import uuid

import jwt

from app.config import get_settings

settings = get_settings()

UPLOAD_TOKEN_PURPOSE = "upload_confirm"
ADMIN_TOKEN_ROLE = "admin"


class TokenError(Exception):
    """Base class for all upload/admin token verification failures."""


class TokenExpired(TokenError):
    pass


class TokenInvalid(TokenError):
    pass


class TokenSubmissionMismatch(TokenInvalid):
    pass


def create_upload_token(submission_id: str, video_key: str) -> str:
    now = int(time.time())
    payload = {
        "sub": submission_id,
        "purpose": UPLOAD_TOKEN_PURPOSE,
        "video_key": video_key,
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
