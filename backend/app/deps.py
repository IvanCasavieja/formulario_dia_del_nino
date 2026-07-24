from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import security

_bearer_scheme = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_admin_token")
    try:
        return security.decode_admin_token(credentials.credentials)
    except security.TokenExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin_token_expired")
    except security.TokenInvalid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_admin_token")


def require_jurado(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_jurado_token")
    try:
        return security.decode_jurado_token(credentials.credentials)
    except security.TokenExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="jurado_token_expired")
    except security.TokenInvalid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_jurado_token")
