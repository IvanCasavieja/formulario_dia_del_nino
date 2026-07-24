from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.rate_limit import limiter
from app.salesforce import (
    SalesforceSyncError,
    build_voto_publico_fields,
    get_voto_publico,
    insert_voto_publico,
    list_vote_candidate_rows,
)
from app.schemas import VoteCandidate, VoteCandidatesResponse, VoteRequest, VoteResponse

settings = get_settings()
router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.get("/candidates", response_model=VoteCandidatesResponse)
def get_vote_candidates() -> VoteCandidatesResponse:
    """Public, unauthenticated - the videos the admin panel picked as this campaign's
    (up to VOTE_CANDIDATES_LIMIT) featured/votable submissions. No rate limit: it's a
    read-only lookup with no side effects, same as GET /api/health."""
    try:
        rows = list_vote_candidate_rows()
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_read_failed", "message": str(e)}
        )
    return VoteCandidatesResponse(
        candidates=[
            VoteCandidate(
                video_choice=row.get("cedula_nino", ""),
                child_first_name=row.get("nombre_nino", ""),
                child_last_name=row.get("apellido_nino", ""),
            )
            for row in rows
        ]
    )


@router.post("", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_VOTE)
def cast_vote(request: Request, payload: VoteRequest) -> VoteResponse:
    # No row for this email just means "first contact" - anyone can vote, registered
    # parent or not. The lookup exists purely to block a second vote, not to gate who
    # is allowed to vote in the first place.
    existing = get_voto_publico(payload.adult_email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "already_voted", "message": "Este email ya emitió un voto."},
        )

    fields = build_voto_publico_fields(
        adult_first_name=payload.adult_first_name,
        adult_last_name=payload.adult_last_name,
        adult_email=payload.adult_email,
        video_choice=payload.video_choice,
        terms_accepted=payload.terms_accepted,
    )
    try:
        insert_voto_publico(fields)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    return VoteResponse(video_choice=payload.video_choice)
