import pytest
from pydantic import ValidationError

from app.schemas import SubmissionCreateRequest


def _valid_payload(**overrides):
    payload = dict(
        parent_first_name="Juana",
        parent_last_name="Pérez",
        parent_cedula="1234567-8",
        parent_email="juana@example.com",
        parent_phone="099123456",
        child_first_name="Sofía",
        child_last_name="Pérez",
        child_cedula="7654321",
        video_content_type="video/mp4",
        video_declared_size_bytes=50_000_000,
        video_declared_duration_seconds=45.0,
        terms_accepted=True,
        terms_version="placeholder-v1",
    )
    payload.update(overrides)
    return payload


def test_valid_payload_passes():
    req = SubmissionCreateRequest(**_valid_payload())
    assert req.child_cedula == "7654321"
    assert req.parent_phone == "099123456"


def test_missing_terms_acceptance_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(terms_accepted=False))


def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(parent_email="not-an-email"))


def test_bad_cedula_length_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(child_cedula="123"))


def test_disallowed_video_type_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(video_content_type="video/avi"))


def test_oversized_video_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(video_declared_size_bytes=300_000_000))


def test_over_duration_video_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(video_declared_duration_seconds=90.0))


def test_empty_name_rejected():
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(**_valid_payload(parent_first_name="   "))
