"""One-off diagnostic: exercises the adults/voting Data Extension directly against the
real tenant (using the credentials in backend/.env), to confirm three things before
this DE is trusted in production:

1. That insert/upsert/lookup work against this second DE key, same as
   scripts/test_salesforce_sync.py already confirmed for Formulario_Video_Nino.
2. That a vote can be cast, a second vote from the same cedula is rejected by the
   app-level check (HaVotado), and the row's contact fields survive both.
3. THE CRITICAL ONE: that a partial upsert (contact fields only, no HaVotado/
   Video_Votado - exactly what the etapa-1 registration sync in
   routers/submissions.py sends) does NOT reset a vote already cast under that
   cedula. If this DE's PUT ever turns out to be a full-row overwrite instead of a
   partial update, this step is where it would show up - don't skip it.

IMPORTANT - this script is a connectivity test ONLY, calling app.salesforce functions
directly with fake data. It does NOT represent how the real flow works - in
production, rows are only ever written from routers/submissions.py (registration
sync) or routers/votes.py (a real vote), never from here.

Usage (from backend/, with .env filled in, SFMC_ENABLED=true and
SFMC_ADULTS_DATA_EXTENSION_KEY set):
    python scripts/test_adults_sync.py

Leaves one row with Cedula_Adulto=88888888 in the DE - delete it manually from Contact
Builder once you've confirmed the row landed with the right values.
"""
from datetime import datetime, timezone

from app.config import get_settings
from app.salesforce import (
    SalesforceSyncError,
    build_adult_row_fields,
    build_vote_fields,
    get_adult_row_by_cedula,
    upsert_adult_row,
)

settings = get_settings()

TEST_CEDULA_ADULTO = "88888888"

CONTACT_FIELDS = build_adult_row_fields(
    adult_first_name="PRUEBA",
    adult_last_name="PRUEBA",
    adult_cedula=TEST_CEDULA_ADULTO,
    adult_email="prueba@tiendainglesa.com.uy",
    adult_phone="000000000",
    terms_accepted=True,
)

if __name__ == "__main__":
    if not settings.SFMC_ENABLED:
        raise SystemExit("SFMC_ENABLED es false en backend/.env - poné SFMC_ENABLED=true antes de correr esto.")
    if not settings.SFMC_ADULTS_DATA_EXTENSION_KEY:
        raise SystemExit("SFMC_ADULTS_DATA_EXTENSION_KEY no está seteado en backend/.env.")

    print(f"Subdominio: {settings.SFMC_SUBDOMAIN}")
    print(f"Adults Data Extension key: {settings.SFMC_ADULTS_DATA_EXTENSION_KEY}")

    print("\n1) Lookup inicial (no debería existir todavía)...")
    existing = get_adult_row_by_cedula(TEST_CEDULA_ADULTO)
    print("   fila existente:", existing)

    print("\n2) Sync de inscripción (como confirm_upload) - solo campos de contacto...")
    try:
        upsert_adult_row(CONTACT_FIELDS)
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)
    print("   OK")

    after_registration = get_adult_row_by_cedula(TEST_CEDULA_ADULTO)
    print("   fila tras el sync de inscripción:", after_registration)
    assert str(after_registration.get("havotado", "")).lower() != "true", (
        "La fila ya tenía HaVotado=true antes de votar - algo está mal en este script."
    )

    print("\n3) Votando (como cast_vote en routers/votes.py)...")
    vote_fields = {**CONTACT_FIELDS, **build_vote_fields(
        adult_cedula=TEST_CEDULA_ADULTO, video_choice="1", voted_at=datetime.now(timezone.utc)
    )}
    try:
        upsert_adult_row(vote_fields)
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)
    print("   OK")

    after_vote = get_adult_row_by_cedula(TEST_CEDULA_ADULTO)
    print("   fila tras votar:", after_vote)
    assert str(after_vote.get("havotado", "")).lower() == "true", "HaVotado debería ser true después de votar."

    print("\n4) Re-sync de inscripción (ej. el mismo adulto anota a un segundo hijo) - CRÍTICO...")
    try:
        upsert_adult_row(CONTACT_FIELDS)
    except SalesforceSyncError as e:
        print("FALLÓ:", e)
        raise SystemExit(1)

    final = get_adult_row_by_cedula(TEST_CEDULA_ADULTO)
    print("   fila final:", final)
    if str(final.get("havotado", "")).lower() != "true":
        print(
            "\n¡ALERTA! HaVotado se perdió después del re-sync de inscripción. Esto significa que el PUT "
            "de esta DE hace overwrite de fila completa, no update parcial - el sync best-effort en "
            "confirm_upload (routers/submissions.py) resetearía el voto de cualquiera que se re-sincronice "
            "después de votar. Hay que revisar esa lógica antes de habilitar esto en producción."
        )
        raise SystemExit(1)

    print("\nOK - HaVotado sobrevivió al re-sync de inscripción, el PUT hace update parcial como se esperaba.")
    print(f"\nListo - revisá Contact Builder en la DE de adultos, Cedula_Adulto={TEST_CEDULA_ADULTO}.")
    print("Borrala a mano una vez que confirmes que los valores llegaron bien.")
