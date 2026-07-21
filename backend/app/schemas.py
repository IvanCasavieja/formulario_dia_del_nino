import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app import shared_constants as sc
from app.models import SubmissionStatus

_DIGITS_RE = re.compile(r"\D+")


def _normalize_digits(value: str) -> str:
    return _DIGITS_RE.sub("", value or "")


def _validate_cedula(value: str, min_digits: int, max_digits: int, field_name: str) -> str:
    digits = _normalize_digits(value)
    if not (min_digits <= len(digits) <= max_digits):
        raise ValueError(
            f"{field_name} debe tener entre {min_digits} y {max_digits} dígitos"
        )
    return digits


class SubmissionCreateRequest(BaseModel):
    parent_first_name: str = Field(min_length=1, max_length=200)
    parent_last_name: str = Field(min_length=1, max_length=200)
    parent_cedula: str
    parent_email: EmailStr
    parent_phone: str
    child_full_name: str = Field(min_length=1, max_length=200)
    child_cedula: str

    video_content_type: str
    video_declared_size_bytes: int = Field(gt=0)
    video_declared_duration_seconds: float = Field(gt=0)

    terms_accepted: bool
    terms_version: str = Field(min_length=1, max_length=50)

    @field_validator("parent_first_name", "parent_last_name", "child_full_name")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("no puede estar vacío")
        return v

    @field_validator("parent_cedula")
    @classmethod
    def _validate_parent_cedula(cls, v: str) -> str:
        return _validate_cedula(v, sc.PARENT_CEDULA_MIN_DIGITS, sc.PARENT_CEDULA_MAX_DIGITS, "La cédula del padre/madre")

    @field_validator("child_cedula")
    @classmethod
    def _validate_child_cedula(cls, v: str) -> str:
        return _validate_cedula(v, sc.CHILD_CEDULA_MIN_DIGITS, sc.CHILD_CEDULA_MAX_DIGITS, "La cédula del niño/a")

    @field_validator("parent_phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        digits = _normalize_digits(v)
        if not (sc.PHONE_MIN_DIGITS <= len(digits) <= sc.PHONE_MAX_DIGITS):
            raise ValueError("Teléfono inválido")
        return digits

    @field_validator("video_content_type")
    @classmethod
    def _validate_content_type(cls, v: str) -> str:
        if v not in sc.ALLOWED_VIDEO_MIME_TYPES:
            raise ValueError(f"Formato de video no soportado: {v}")
        return v

    @field_validator("video_declared_size_bytes")
    @classmethod
    def _validate_size(cls, v: int) -> int:
        if v > sc.MAX_VIDEO_SIZE_BYTES:
            raise ValueError(f"El video supera el tamaño máximo de {sc.MAX_VIDEO_SIZE_BYTES} bytes")
        return v

    @field_validator("video_declared_duration_seconds")
    @classmethod
    def _validate_duration(cls, v: float) -> float:
        if v > sc.MAX_VIDEO_DURATION_SECONDS + sc.MAX_VIDEO_DURATION_TOLERANCE_SECONDS:
            raise ValueError(f"El video supera los {sc.MAX_VIDEO_DURATION_SECONDS} segundos máximos")
        return v

    @model_validator(mode="after")
    def _validate_terms(self) -> "SubmissionCreateRequest":
        if not self.terms_accepted:
            raise ValueError("Debe aceptar los términos y condiciones")
        return self


class SubmissionCreateResponse(BaseModel):
    submission_id: UUID
    upload_url: str
    upload_token: str
    video_key: str
    expires_in: int


class SubmissionStatusResponse(BaseModel):
    submission_id: UUID
    status: SubmissionStatus


class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class AdminSubmissionListItem(BaseModel):
    id: UUID
    parent_first_name: str
    parent_last_name: str
    child_full_name: str
    status: SubmissionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSubmissionDetail(BaseModel):
    id: UUID
    parent_first_name: str
    parent_last_name: str
    parent_cedula: str
    parent_email: str
    parent_phone: str
    child_full_name: str
    child_cedula: str
    video_content_type: str
    video_actual_size_bytes: int | None
    video_duration_seconds: float | None
    status: SubmissionStatus
    moderation_result: dict | None
    admin_notes: str | None
    admin_reviewed_by: str | None
    admin_decided_at: datetime | None
    terms_accepted: bool
    terms_version: str
    created_at: datetime
    video_view_url: str | None = None
    salesforce_synced_at: datetime | None
    salesforce_sync_error: str | None

    model_config = {"from_attributes": True}


class AdminDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=2000)
    reviewed_by: str | None = Field(default=None, max_length=200)
