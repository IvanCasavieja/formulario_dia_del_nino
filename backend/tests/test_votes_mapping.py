from app.salesforce import build_jurado_vote_fields, build_vote_candidate_fields, build_voto_publico_fields


def test_build_voto_publico_fields_uses_real_data_extension_column_names():
    fields = build_voto_publico_fields(
        adult_first_name="Juana",
        adult_last_name="Pérez",
        adult_email="juana@example.com",
        video_choice="7654321",
        terms_accepted=True,
    )

    assert fields["EmailAddress"] == "juana@example.com"
    assert fields["Nombre"] == "Juana Pérez"
    assert fields["VideoElegido"] == "7654321"
    assert fields["Term_Cond_Voto"] is True
    assert "FechaVoto" in fields


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


def test_build_jurado_vote_fields_uses_real_data_extension_column_names():
    fields = build_jurado_vote_fields(jurado_id="jurado_1", video_choice="2")

    assert fields["JuradoId"] == "jurado_1"
    assert fields["VideoElegido"] == "2"
    assert fields["HaVotado"] is True
    assert "FechaVoto" in fields


def test_build_jurado_vote_fields_never_touches_password_hash():
    fields = build_jurado_vote_fields(jurado_id="jurado_1", video_choice="2")

    assert "PasswordHash" not in fields
