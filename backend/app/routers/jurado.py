import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app import security
from app.config import get_settings
from app.deps import require_jurado
from app.rate_limit import limiter
from app.salesforce import SalesforceSyncError, build_jurado_vote_fields, get_jurado_row, upsert_jurado_row
from app.schemas import JuradoLoginRequest, JuradoLoginResponse, JuradoStatusResponse, JuradoVoteRequest

settings = get_settings()

# Login lives on its own router (no require_jurado dependency - that would be
# circular), same split as admin.py's login_router/router.
login_router = APIRouter(prefix="/api/jurado", tags=["jurado"])
router = APIRouter(prefix="/api/jurado", tags=["jurado"], dependencies=[Depends(require_jurado)])


def _ha_votado(row: dict) -> bool:
    return str(row.get("havotado", "")).lower() == "true"


@login_router.post("/login", response_model=JuradoLoginResponse)
@limiter.limit(settings.RATE_LIMIT_JURADO_LOGIN)
def jurado_login(request: Request, payload: JuradoLoginRequest) -> JuradoLoginResponse:
    try:
        row = get_jurado_row(payload.jurado_id)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_read_failed", "message": str(e)}
        )

    password_hash = (row or {}).get("passwordhash", "")
    # Same shape regardless of "no such jurado_id" vs "wrong password" - don't leak
    # which one it was.
    valid = bool(password_hash) and bcrypt.checkpw(payload.password.encode("utf-8"), password_hash.encode("utf-8"))
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_credentials"})

    token = security.create_jurado_token(payload.jurado_id)
    return JuradoLoginResponse(
        access_token=token,
        expires_in=settings.ADMIN_SESSION_TTL_SECONDS,
        nombre=row.get("nombre", ""),
    )


@router.get("/status", response_model=JuradoStatusResponse)
def jurado_status(claims: dict = Depends(require_jurado)) -> JuradoStatusResponse:
    jurado_id = claims["sub"]
    try:
        row = get_jurado_row(jurado_id)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_read_failed", "message": str(e)}
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "jurado_not_found"})

    return JuradoStatusResponse(
        nombre=row.get("nombre", ""),
        ha_votado=_ha_votado(row),
        video_elegido=row.get("videoelegido") or None,
    )


@router.post("/vote", response_model=JuradoStatusResponse, status_code=status.HTTP_201_CREATED)
def jurado_vote(payload: JuradoVoteRequest, claims: dict = Depends(require_jurado)) -> JuradoStatusResponse:
    jurado_id = claims["sub"]
    try:
        row = get_jurado_row(jurado_id)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_read_failed", "message": str(e)}
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "jurado_not_found"})
    if _ha_votado(row):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "already_voted", "message": "Ya emitiste tu voto."},
        )

    try:
        upsert_jurado_row(build_jurado_vote_fields(jurado_id=jurado_id, video_choice=payload.video_choice))
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    return JuradoStatusResponse(nombre=row.get("nombre", ""), ha_votado=True, video_elegido=payload.video_choice)
