from datetime import datetime, timezone

from app.salesforce import build_adult_row_fields, build_vote_candidate_fields, build_vote_fields


def test_build_adult_row_fields_uses_real_data_extension_column_names():
    fields = build_adult_row_fields(
        adult_first_name="Juana",
        adult_last_name="Pérez",
        adult_cedula="1234567",
        adult_email="juana@example.com",
        adult_phone="099123456",
        terms_accepted=True,
    )

    assert fields == {
        "Nombre_Adulto": "Juana",
        "Apellido_Adulto": "Pérez",
        "Cedula_Adulto": "1234567",
        "EmailAddress": "juana@example.com",
        "Celular": "099123456",
        "Term_Cond_Voto": True,
    }


def test_build_adult_row_fields_excludes_vote_state_fields():
    fields = build_adult_row_fields(
        adult_first_name="Juana",
        adult_last_name="Pérez",
        adult_cedula="1234567",
        adult_email="juana@example.com",
        adult_phone="099123456",
        terms_accepted=True,
    )

    assert "HaVotado" not in fields
    assert "Video_Votado" not in fields
    assert "Fecha_Voto" not in fields


def test_build_vote_fields_uses_real_data_extension_column_names():
    voted_at = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)

    fields = build_vote_fields(adult_cedula="1234567", video_choice="2", voted_at=voted_at)

    assert fields == {
        "Cedula_Adulto": "1234567",
        "HaVotado": True,
        "Video_Votado": "2",
        "Fecha_Voto": voted_at.isoformat(),
    }


def test_build_vote_candidate_fields_uses_real_data_extension_column_names():
    fields = build_vote_candidate_fields(child_cedula="7654321", enabled=True)

    assert fields == {
        "Cedula_Nino": "7654321",
        "Candidato_Votacion": True,
    }


def test_build_vote_candidate_fields_can_disable():
    fields = build_vote_candidate_fields(child_cedula="7654321", enabled=False)

    assert fields == {
        "Cedula_Nino": "7654321",
        "Candidato_Votacion": False,
    }
