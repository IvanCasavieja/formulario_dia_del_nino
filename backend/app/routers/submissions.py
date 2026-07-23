import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from app import r2, security
from app.config import get_settings
from app.models import SubmissionStatus
from app.rate_limit import limiter
from app.salesforce import (
    SalesforceSyncError,
    build_adult_row_fields,
    build_row_fields,
    get_row_by_cedula_nino,
    upsert_adult_row,
    upsert_row,
)
from app.schemas import SubmissionCreateRequest, SubmissionCreateResponse
from app.worker.tasks import process_submission_video

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/submissions", tags=["submissions"])

# A row with one of these statuses (or none yet) doesn't block a fresh attempt for the
# same child - anything else (uploaded/processing/needs_review/approved/rejected)
# means there's already a real entry for that child.
_RESUBMITTABLE_STATUSES = {"", SubmissionStatus.PENDING_UPLOAD.value, SubmissionStatus.EXPIRED.value}


@router.post("", response_model=SubmissionCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_SUBMIT)
def create_submission(request: Request, payload: SubmissionCreateRequest) -> SubmissionCreateResponse:
    # Dedup check against Salesforce directly - there's no database of our own to ask.
    # No row in Salesforce means no submission has ever been confirmed for this child.
    existing = get_row_by_cedula_nino(payload.child_cedula)
    if existing is not None and existing.get("status") not in _RESUBMITTABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "duplicate_child_cedula", "message": "Ya existe una inscripción para este niño/a."},
        )

    # This id only lives for the duration of the upload window (inside the signed
    # token below) - it's never written anywhere, just used to build a private R2 key.
    submission_id = uuid.uuid4()
    video_key = r2.build_video_key(submission_id, payload.video_content_type)

    fields = {
        "parent_first_name": payload.parent_first_name,
        "parent_last_name": payload.parent_last_name,
        "parent_cedula": payload.parent_cedula,
        "parent_email": payload.parent_email,
        "parent_phone": payload.parent_phone,
        "child_first_name": payload.child_first_name,
        "child_last_name": payload.child_last_name,
        "child_cedula": payload.child_cedula,
        "terms_accepted": payload.terms_accepted,
    }
    upload_token = security.create_upload_token(str(submission_id), video_key, fields)
    upload_url = r2.create_presigned_put_url(video_key, payload.video_content_type)

    return SubmissionCreateResponse(
        submission_id=submission_id,
        upload_url=upload_url,
        upload_token=upload_token,
        video_key=video_key,
        expires_in=settings.UPLOAD_TOKEN_TTL_SECONDS,
    )


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "missing_upload_token"}
        )
    return authorization.split(" ", 1)[1].strip()


@router.post("/{submission_id}/confirm-upload", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.RATE_LIMIT_CONFIRM_UPLOAD)
def confirm_upload(
    request: Request,
    submission_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)

    try:
        claims = security.decode_upload_token(token, str(submission_id))
    except security.TokenExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "upload_token_expired"})
    except security.TokenSubmissionMismatch:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "token_submission_mismatch"})
    except security.TokenInvalid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_upload_token"})

    video_key = claims["video_key"]
    fields = claims["fields"]

    # TEMP (R2 sin contratar - revertir cuando exista): sin bucket real no hay nada que
    # head_object pueda encontrar, así que este chequeo queda pausado. Es la única
    # verificación de que el video realmente existe antes de escribir en Salesforce -
    # reactivarlo es condición para ir a producción.
    #
    # head = r2.head_object(video_key)
    # if head is None or head.get("ContentLength", 0) <= 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "video_not_found_in_storage"}
    #     )

    # This is the one and only place any of this data gets written anywhere - right
    # here, right after the video upload is confirmed. If this fails, the submission
    # genuinely doesn't exist and the client needs to know (and can retry) rather than
    # silently losing the entry.
    row_fields = build_row_fields(**fields)
    row_fields["Status"] = SubmissionStatus.UPLOADED.value
    row_fields["VideoKey"] = video_key
    try:
        upsert_row(row_fields)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    # Best-effort sync into the sendable adults/voting DE, keyed by the parent's own
    # cedula - upsert-by-primary-key is what keeps that DE deduplicated (a parent
    # registering a second child just updates the same row instead of creating one).
    # Never fails the request: the registration itself already succeeded above in the
    # DE that actually prevents double registration, so a hiccup here shouldn't make
    # the client think their submission was lost. Deliberately only sends contact
    # fields (build_adult_row_fields excludes HaVotado/Video_Votado) so this can never
    # reset a vote already cast under this cedula.
    try:
        upsert_adult_row(
            build_adult_row_fields(
                adult_first_name=fields["parent_first_name"],
                adult_last_name=fields["parent_last_name"],
                adult_cedula=fields["parent_cedula"],
                adult_email=fields["parent_email"],
                adult_phone=fields["parent_phone"],
                terms_accepted=fields["terms_accepted"],
            )
        )
    except SalesforceSyncError:
        logger.exception(
            "confirm_upload: failed to sync parent_cedula=%s into the adults/voting DE", fields["parent_cedula"]
        )

    background_tasks.add_task(process_submission_video, video_key, fields["child_cedula"])

    return {"status": "processing"}
