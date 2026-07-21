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
        child_full_name="Sofía Pérez",
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


def test_field_mapping_uses_de_column_names():
    submission = _build_submission()
    fields = _submission_to_de_fields(submission)

    assert fields["SubmissionId"] == str(submission.id)
    assert fields["ParentFirstName"] == "Juana"
    assert fields["ChildCedula"] == "87654321"
    assert fields["Status"] == "uploaded"
    assert fields["SubmittedAt"] == "2026-07-21T12:00:00+00:00"


def test_field_mapping_has_no_video_bytes_or_binary_fields():
    submission = _build_submission()
    fields = _submission_to_de_fields(submission)

    assert "video_key" not in fields
    assert all(isinstance(v, str) or v is None for v in fields.values())
