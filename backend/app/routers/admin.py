import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app import r2, security
from app.config import get_settings
from app.deps import require_admin
from app.models import SubmissionStatus
from app.rate_limit import limiter
from app.scoring import compute_resultados
from app.salesforce import (
    SalesforceSyncError,
    build_vote_candidate_fields,
    get_row_by_cedula_nino,
    list_jurados,
    list_rows,
    list_vote_candidate_rows,
    list_votos_publico,
    upsert_row,
)
from app.schemas import (
    AdminDecisionRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSubmissionDetail,
    AdminSubmissionListItem,
    AdminVotingCandidateRequest,
    JuradoResultadoItem,
    ResultadoVideo,
    ResultadosResponse,
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


def _is_vote_candidate(row: dict) -> bool:
    return str(row.get("candidato_votacion", "")).lower() == "true"


def _row_to_list_item(row: dict) -> AdminSubmissionListItem:
    return AdminSubmissionListItem(
        child_cedula=row.get("cedula_nino", ""),
        parent_first_name=row.get("nombre_adulto", ""),
        parent_last_name=row.get("apellido_adulto", ""),
        child_first_name=row.get("nombre_nino", ""),
        child_last_name=row.get("apellido_nino", ""),
        status=row.get("status") or SubmissionStatus.UPLOADED.value,
        is_vote_candidate=_is_vote_candidate(row),
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
        is_vote_candidate=_is_vote_candidate(row),
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


@router.post("/submissions/{child_cedula}/voting-candidate", response_model=AdminSubmissionDetail)
def set_voting_candidate(child_cedula: str, payload: AdminVotingCandidateRequest) -> AdminSubmissionDetail:
    row = get_row_by_cedula_nino(child_cedula)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "submission_not_found"})

    if payload.enabled:
        if row.get("status") != SubmissionStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "not_approved", "message": "Solo se pueden marcar videos aprobados."},
            )
        current_candidates = list_vote_candidate_rows()
        already_candidate = any(r.get("cedula_nino") == child_cedula for r in current_candidates)
        if not already_candidate and len(current_candidates) >= settings.VOTE_CANDIDATES_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "vote_candidates_full",
                    "message": f"Ya hay {settings.VOTE_CANDIDATES_LIMIT} videos elegidos para la votación pública.",
                },
            )

    try:
        upsert_row(build_vote_candidate_fields(child_cedula=child_cedula, enabled=payload.enabled))
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_write_failed", "message": str(e)}
        )

    updated = get_row_by_cedula_nino(child_cedula)
    return _row_to_detail(updated or row)


def _jurado_ha_votado(row: dict) -> bool:
    return str(row.get("havotado", "")).lower() == "true"


@router.get("/votacion/resultados", response_model=ResultadosResponse)
def get_resultados_votacion() -> ResultadosResponse:
    try:
        candidatos = list_vote_candidate_rows()
        votos_publico_rows = list_votos_publico()
        jurado_rows = list_jurados()
    except SalesforceSyncError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail={"error": "salesforce_read_failed", "message": str(e)}
        )

    candidatos_choices = [row.get("cedula_nino", "") for row in candidatos]
    votos_publico_choices = [row.get("videoelegido", "") for row in votos_publico_rows if row.get("videoelegido")]
    votos_jurado_choices = [
        row.get("videoelegido", "") for row in jurado_rows if _jurado_ha_votado(row) and row.get("videoelegido")
    ]

    resultados = compute_resultados(votos_publico_choices, votos_jurado_choices, candidatos_choices)

    videos = [
        ResultadoVideo(
            video_choice=row.get("cedula_nino", ""),
            child_first_name=row.get("nombre_nino", ""),
            child_last_name=row.get("apellido_nino", ""),
            **resultados[row.get("cedula_nino", "")],
        )
        for row in candidatos
    ]
    jurados = [
        JuradoResultadoItem(
            jurado_id=row.get("juradoid", ""),
            nombre=row.get("nombre", ""),
            ha_votado=_jurado_ha_votado(row),
        )
        for row in jurado_rows
    ]
    return ResultadosResponse(videos=videos, jurados=jurados)
