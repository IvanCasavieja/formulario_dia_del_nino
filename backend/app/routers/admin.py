import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app import r2, security
from app.config import get_settings
from app.deps import require_admin
from app.models import SubmissionStatus
from app.rate_limit import limiter
from app.salesforce import SalesforceSyncError, get_row_by_cedula_nino, list_rows, upsert_row
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


def _row_to_list_item(row: dict) -> AdminSubmissionListItem:
    return AdminSubmissionListItem(
        child_cedula=row.get("cedula_nino", ""),
        parent_first_name=row.get("nombre_adulto", ""),
        parent_last_name=row.get("apellido_adulto", ""),
        child_first_name=row.get("nombre_nino", ""),
        child_last_name=row.get("apellido_nino", ""),
        status=row.get("status") or SubmissionStatus.UPLOADED.value,
    )


def _row_to_detail(row: dict) -> AdminSubmissionDetail:
    return AdminSubmissionDetail(
        child_cedula=row.get("cedula_nino", ""),
        parent_first_name=row.get("nombre_adulto", ""),
        parent_last_name=row.get("apellido_adulto", ""),
        parent_cedula=row.get("cedula", ""),
        parent_email=row.get("emailaddress", ""),
        parent_phone=row.get("celular", ""),
        child_first_name=row.get("nombre_nino", ""),
        child_last_name=row.get("apellido_nino", ""),
        status=row.get("status") or SubmissionStatus.UPLOADED.value,
        moderation_result=row.get("moderationresult") or None,
        admin_notes=row.get("adminnotes") or None,
        admin_reviewed_by=row.get("adminreviewedby") or None,
        terms_accepted=str(row.get("term_cond", "")).lower() == "true",
        video_key=row.get("videokey") or None,
    )


@router.get("/submissions", response_model=list[AdminSubmissionListItem])
def list_submissions(
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
) -> list[AdminSubmissionListItem]:
    # Default view is the review queue - the whole point of this dashboard. There's no
    # database here anymore, this Data Extension is queried directly.
    rows = list_rows(status=(status_filter or SubmissionStatus.NEEDS_REVIEW).value)
    return [_row_to_list_item(row) for row in rows]


@router.get("/submissions/{child_cedula}", response_model=AdminSubmissionDetail)
def get_submission_detail(child_cedula: str) -> AdminSubmissionDetail:
    row = get_row_by_cedula_nino(child_cedula)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    detail = _row_to_detail(row)
    video_key = row.get("videokey")
    if video_key:
        head = r2.head_object(video_key)
        if head is not None:
            detail.video_view_url = r2.create_presigned_get_url(video_key)
    return detail


@router.post("/submissions/{child_cedula}/decision", response_model=AdminSubmissionDetail)
def decide_submission(child_cedula: str, payload: AdminDecisionRequest) -> AdminSubmissionDetail:
    if get_row_by_cedula_nino(child_cedula) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    new_status = SubmissionStatus.APPROVED if payload.decision == "approved" else SubmissionStatus.REJECTED
    update_fields: dict = {"Cedula_Nino": child_cedula, "Status": new_status.value}
    if payload.note is not None:
        update_fields["AdminNotes"] = payload.note
    if payload.reviewed_by is not None:
        update_fields["AdminReviewedBy"] = payload.reviewed_by

    try:
        upsert_row(update_fields)
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    updated = get_row_by_cedula_nino(child_cedula)
    return _row_to_detail(updated or update_fields)
