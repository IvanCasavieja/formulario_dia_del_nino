"""One-off diagnostic: simulates a full submission (create -> confirm-upload ->
moderation) against the real "Formulario_Video_Nino" Data Extension, using the
credentials in backend/.env, to confirm the whole no-database flow actually works.

IMPORTANT - this script is a connectivity test ONLY. It calls the Salesforce
functions directly with fake data, with no form, no video, no real HTTP request
involved. It does NOT represent how the real flow works and must never be wired into
the app that way. In production, a row is only ever written from
app/routers/submissions.py's confirm_upload, and only after the video upload is
verified - i.e. after the upload itself is validated, never before. Don't "simplify"
that gating to look more like this script.

Usage (from backend/, with .env filled in and SFMC_ENABLED=true):
    python scripts/test_salesforce_sync.py

Leaves one row with Cedula_Nino=99999999 in the DE - delete it manually from Contact
Builder once you've confirmed the row landed with the right values.
"""
from app.config import get_settings
from app.salesforce import SalesforceSyncError, build_row_fields, get_row_by_cedula_nino, upsert_row

settings = get_settings()

TEST_CEDULA_NINO = "99999999"

FIELDS = build_row_fields(
    parent_first_name="PRUEBA",
    parent_last_name="PRUEBA",
    parent_cedula="12345678",
    parent_email="prueba@tiendainglesa.com.uy",
    parent_phone="000000000",
    child_first_name="PRUEBA",
    child_last_name="PRUEBA",
    child_cedula=TEST_CEDULA_NINO,
    terms_accepted=True,
)

if __name__ == "__main__":
    if not settings.SFMC_ENABLED:
        raise SystemExit("SFMC_ENABLED es false en backend/.env - poné SFMC_ENABLED=true antes de correr esto.")

    print(f"Subdominio: {settings.SFMC_SUBDOMAIN}")
    print(f"Data Extension key: {settings.SFMC_DATA_EXTENSION_KEY}")

    print("\n1) Dedup check (como create_submission)...")
    existing = get_row_by_cedula_nino(TEST_CEDULA_NINO)
    print("   fila existente:", existing)

    print("\n2) Insertando con Status=uploaded (como confirm_upload)...")
    row_fields = {**FIELDS, "Status": "uploaded", "VideoKey": "submissions/probe/test.mp4"}
    try:
        upsert_row(row_fields)
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)
    print("   OK")

    print("\n3) Actualizando a needs_review (como process_submission_video)...")
    try:
        upsert_row({"Cedula_Nino": TEST_CEDULA_NINO, "Status": "needs_review", "ModerationResult": "passed_server_side_validation"})
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)
    print("   OK")

    print("\n4) Aprobando (como decide_submission)...")
    try:
        upsert_row({"Cedula_Nino": TEST_CEDULA_NINO, "Status": "approved", "AdminNotes": "prueba ok", "AdminReviewedBy": "script"})
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)
    print("   OK")

    final = get_row_by_cedula_nino(TEST_CEDULA_NINO)
    print("\nFila final en Salesforce:")
    print(final)

    print(f"\nListo - revisá Contact Builder > Formulario_Video_Nino, Cedula_Nino={TEST_CEDULA_NINO}.")
    print("Borrala a mano una vez que confirmes que los valores llegaron bien.")
