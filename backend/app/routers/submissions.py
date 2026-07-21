import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import r2, security
from app.config import get_settings
from app.db import get_db
from app.models import Submission, SubmissionStatus
from app.rate_limit import limiter
from app.schemas import SubmissionCreateRequest, SubmissionCreateResponse, SubmissionStatusResponse
from app.worker.queue import enqueue_salesforce_sync, enqueue_submission_processing

settings = get_settings()
router = APIRouter(prefix="/api/submissions", tags=["submissions"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _apply_fields(submission: Submission, payload: SubmissionCreateRequest, client_ip: str, video_key: str) -> None:
    submission.parent_first_name = payload.parent_first_name
    submission.parent_last_name = payload.parent_last_name
    submission.parent_cedula = payload.parent_cedula
    submission.parent_email = payload.parent_email
    submission.parent_phone = payload.parent_phone
    submission.child_full_name = payload.child_full_name
    submission.child_cedula = payload.child_cedula
    submission.video_key = video_key
    submission.video_content_type = payload.video_content_type
    submission.video_declared_size_bytes = payload.video_declared_size_bytes
    submission.video_declared_duration_seconds = payload.video_declared_duration_seconds
    submission.terms_accepted = payload.terms_accepted
    submission.terms_version = payload.terms_version
    submission.ip_address = client_ip


@router.post("", response_model=SubmissionCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_SUBMIT)
def create_submission(
    request: Request, payload: SubmissionCreateRequest, db: Session = Depends(get_db)
) -> SubmissionCreateResponse:
    client_ip = _client_ip(request)

    existing = db.scalar(select(Submission).where(Submission.child_cedula == payload.child_cedula))

    if existing is not None and existing.status != SubmissionStatus.PENDING_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "duplicate_child_cedula", "message": "Ya existe una inscripción para este niño/a."},
        )

    submission_id = existing.id if existing is not None else uuid.uuid4()
    video_key = r2.build_video_key(submission_id, payload.video_content_type)

    if existing is not None:
        submission = existing
        _apply_fields(submission, payload, client_ip, video_key)
    else:
        submission = Submission(id=submission_id, status=SubmissionStatus.PENDING_UPLOAD)
        _apply_fields(submission, payload, client_ip, video_key)
        db.add(submission)

    try:
        db.commit()
    except IntegrityError:
        # Race backstop: two concurrent requests for the same child_cedula could both
        # pass the pre-check above. The DB unique constraint is the real guarantee.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "duplicate_child_cedula", "message": "Ya existe una inscripción para este niño/a."},
        )

    upload_token = security.create_upload_token(str(submission.id), video_key)
    upload_url = r2.create_presigned_put_url(video_key, payload.video_content_type)

    return SubmissionCreateResponse(
        submission_id=submission.id,
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
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    token = _extract_bearer_token(authorization)

    try:
        security.decode_upload_token(token, str(submission_id))
    except security.TokenExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "upload_token_expired"})
    except security.TokenSubmissionMismatch:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "token_submission_mismatch"})
    except security.TokenInvalid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_upload_token"})

    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    if submission.status != SubmissionStatus.PENDING_UPLOAD:
        # Idempotency/replay guard: a replayed or double-fired confirm-upload call lands
        # here as a clean no-op instead of re-enqueueing a duplicate moderation job.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail={"error": "already_confirmed", "status": submission.status}
        )

    head = r2.head_object(submission.video_key)
    if head is None or head.get("ContentLength", 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "video_not_found_in_storage"}
        )

    submission.status = SubmissionStatus.UPLOADED
    submission.uploaded_at = datetime.now(timezone.utc)
    submission.video_actual_size_bytes = head.get("ContentLength")
    db.commit()

    enqueue_submission_processing(str(submission.id))

    if settings.SFMC_ENABLED:
        # Fires right here per spec: Salesforce gets the raw submission data as soon as
        # the video upload is confirmed, not after moderation runs. Best-effort/never
        # blocks - failures only show up as salesforce_sync_error in the admin panel.
        enqueue_salesforce_sync(str(submission.id))

    return {"status": "processing"}


@router.get("/{submission_id}/status", response_model=SubmissionStatusResponse)
def get_submission_status(submission_id: uuid.UUID, db: Session = Depends(get_db)) -> SubmissionStatusResponse:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})
    return SubmissionStatusResponse(submission_id=submission.id, status=submission.status)
