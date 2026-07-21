import uuid
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import r2, security
from app.config import get_settings
from app.db import get_db
from app.deps import require_admin
from app.models import Submission, SubmissionStatus
from app.rate_limit import limiter
from app.schemas import (
    AdminDecisionRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSubmissionDetail,
    AdminSubmissionListItem,
)

settings = get_settings()

# Login lives on its own router (no require_admin dependency - that would be circular).
login_router = APIRouter(prefix="/api/admin", tags=["admin"])

# Every other admin route is protected structurally via the router-level dependency,
# so protection can't be forgotten on an individual endpoint.
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@login_router.post("/login", response_model=AdminLoginResponse)
@limiter.limit(settings.RATE_LIMIT_ADMIN_LOGIN)
def admin_login(request: Request, payload: AdminLoginRequest) -> AdminLoginResponse:
    valid = bcrypt.checkpw(payload.password.encode("utf-8"), settings.ADMIN_PASSWORD_HASH.encode("utf-8"))
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_password"})
    token = security.create_admin_token()
    return AdminLoginResponse(access_token=token, expires_in=settings.ADMIN_SESSION_TTL_SECONDS)


@router.get("/submissions", response_model=list[AdminSubmissionListItem])
def list_submissions(
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Submission]:
    query = select(Submission).order_by(Submission.created_at.desc())
    # Default view is the review queue - the whole point of this dashboard.
    query = query.where(Submission.status == (status_filter or SubmissionStatus.NEEDS_REVIEW))
    query = query.limit(limit).offset(offset)
    return list(db.scalars(query))


@router.get("/submissions/{submission_id}", response_model=AdminSubmissionDetail)
def get_submission_detail(submission_id: uuid.UUID, db: Session = Depends(get_db)) -> AdminSubmissionDetail:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    detail = AdminSubmissionDetail.model_validate(submission)
    if submission.status != SubmissionStatus.PENDING_UPLOAD:
        head = r2.head_object(submission.video_key)
        if head is not None:
            detail.video_view_url = r2.create_presigned_get_url(submission.video_key)
    return detail


@router.post("/submissions/{submission_id}/decision", response_model=AdminSubmissionDetail)
def decide_submission(
    submission_id: uuid.UUID, payload: AdminDecisionRequest, db: Session = Depends(get_db)
) -> AdminSubmissionDetail:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    submission.status = SubmissionStatus.APPROVED if payload.decision == "approved" else SubmissionStatus.REJECTED
    submission.admin_notes = payload.note
    submission.admin_reviewed_by = payload.reviewed_by
    submission.admin_decided_at = datetime.now(timezone.utc)
    db.commit()

    return AdminSubmissionDetail.model_validate(submission)
