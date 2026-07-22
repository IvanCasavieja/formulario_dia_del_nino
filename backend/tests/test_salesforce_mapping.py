import uuid
from datetime import datetime, timezone

from app.models import Submission, SubmissionStatus
from app.worker.salesforce_tasks import _submission_to_de_fields


def _build_submission(**overrides) -> Submission:
    defaults = dict(
        id=uuid.uuid4(),
        parent_first_name="Juana",
        parent_last_name="Pérez",
        parent_cedula="12345678",
        parent_email="juana@example.com",
        parent_phone="099123456",
        child_first_name="Sofía",
        child_last_name="Pérez",
        child_cedula="87654321",
        video_key="submissions/x/y.mp4",
        video_content_type="video/mp4",
        status=SubmissionStatus.UPLOADED,
        terms_accepted=True,
        terms_version="placeholder-v1",
        ip_address="127.0.0.1",
        created_at=datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return Submission(**defaults)


def test_field_mapping_uses_real_data_extension_column_names():
    submission = _build_submission()
    fields = _submission_to_de_fields(submission)

    assert fields == {
        "Nombre_Adulto": "Juana",
        "Apellido_Adulto": "Pérez",
        "EmailAddress": "juana@example.com",
        "Celular": "099123456",
        "Cedula": "12345678",
        "Nombre_nino": "Sofía",
        "Apellido_nino": "Pérez",
        "Cedula_Nino": "87654321",
        "Term_Cond": True,
    }


def test_field_mapping_excludes_internal_and_video_fields():
    submission = _build_submission()
    fields = _submission_to_de_fields(submission)

    assert "video_key" not in fields
    assert "SubmissionId" not in fields
    assert "Status" not in fields
    assert "SubmittedAt" not in fields
    assert "Link_Video" not in fields
