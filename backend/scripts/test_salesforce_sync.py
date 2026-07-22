"""One-off diagnostic: sends a single obviously-fake row to the real
"Formulario_Video_Nino" Data Extension using the credentials in backend/.env, to
confirm the SFMC REST API call actually works before trusting it in the automatic
sync flow (app/worker/salesforce_tasks.py).

Usage (from backend/, with .env filled in and SFMC_ENABLED=true):
    python scripts/test_salesforce_sync.py

Leaves one row with Cedula=00000000 in the DE - delete it manually from Contact
Builder once you've confirmed the row landed with the right values.
"""
from app.config import get_settings
from app.salesforce import SalesforceSyncError, insert_data_extension_row

settings = get_settings()

TEST_FIELDS = {
    "Nombre_Adulto": "PRUEBA",
    "Apellido_Adulto": "PRUEBA",
    "EmailAddress": "prueba@tiendainglesa.com.uy",
    "Celular": "000000000",
    "Cedula": "00000000",
    "Nombre_nino": "PRUEBA",
    "Apellido_nino": "PRUEBA",
    "Cedula_Nino": "00000001",
    "Term_Cond": True,
}

if __name__ == "__main__":
    if not settings.SFMC_ENABLED:
        raise SystemExit("SFMC_ENABLED es false en backend/.env - poné SFMC_ENABLED=true antes de correr esto.")

    print(f"Subdominio: {settings.SFMC_SUBDOMAIN}")
    print(f"Data Extension key: {settings.SFMC_DATA_EXTENSION_KEY}")
    print("Insertando fila de prueba...")

    try:
        insert_data_extension_row(TEST_FIELDS)
    except SalesforceSyncError as e:
        print("\nFALLÓ:")
        print(e)
        raise SystemExit(1)

    print("\nOK - revisá Contact Builder > Formulario_Video_Nino, debería haber una")
    print("fila nueva con Cedula=00000000. Borrala a mano una vez que confirmes que")
    print("los valores llegaron bien.")
