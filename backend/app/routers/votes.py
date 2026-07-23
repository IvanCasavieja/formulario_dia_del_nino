from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.rate_limit import limiter
from app.salesforce import (
    SalesforceSyncError,
    build_adult_row_fields,
    build_vote_fields,
    get_adult_row_by_cedula,
    upsert_adult_row,
)
from app.schemas import VoteRequest, VoteResponse

settings = get_settings()
router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.post("", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_VOTE)
def cast_vote(request: Request, payload: VoteRequest) -> VoteResponse:
    try:
        # No row for this cedula just means "first contact" - anyone can vote,
        # registered parent or not. The lookup exists purely to block a second vote,
        # not to gate who is allowed to vote in the first place.
        existing = get_adult_row_by_cedula(payload.adult_cedula)
        if existing is not None and str(existing.get("havotado", "")).lower() == "true":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "already_voted", "message": "Esta cédula ya emitió un voto."},
            )

        fields = build_adult_row_fields(
            adult_first_name=payload.adult_first_name,
            adult_last_name=payload.adult_last_name,
            adult_cedula=payload.adult_cedula,
            adult_email=payload.adult_email,
            adult_phone=payload.adult_phone,
            terms_accepted=payload.terms_accepted,
        )
        fields.update(
            build_vote_fields(
                adult_cedula=payload.adult_cedula,
                video_choice=payload.video_choice,
                voted_at=datetime.now(timezone.utc),
            )
        )
        upsert_adult_row(fields)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    return VoteResponse(video_choice=payload.video_choice)
