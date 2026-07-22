from app.salesforce import build_row_fields


def test_build_row_fields_uses_real_data_extension_column_names():
    fields = build_row_fields(
        parent_first_name="Juana",
        parent_last_name="Pérez",
        parent_cedula="1234567",
        parent_email="juana@example.com",
        parent_phone="099123456",
        child_first_name="Sofía",
        child_last_name="Pérez",
        child_cedula="7654321",
        terms_accepted=True,
    )

    assert fields == {
        "Nombre_Adulto": "Juana",
        "Apellido_Adulto": "Pérez",
        "Cedula": "1234567",
        "EmailAddress": "juana@example.com",
        "Celular": "099123456",
        "Nombre_nino": "Sofía",
        "Apellido_nino": "Pérez",
        "Cedula_Nino": "7654321",
        "Term_Cond": True,
    }


def test_build_row_fields_excludes_video_and_internal_fields():
    fields = build_row_fields(
        parent_first_name="Juana",
        parent_last_name="Pérez",
        parent_cedula="1234567",
        parent_email="juana@example.com",
        parent_phone="099123456",
        child_first_name="Sofía",
        child_last_name="Pérez",
        child_cedula="7654321",
        terms_accepted=True,
    )

    assert "video_key" not in fields
    assert "Status" not in fields
    assert "VideoKey" not in fields
    assert "Link_Video" not in fields
