"""Run locally once per jurado member. Pega el resultado (no la contraseña) en la
columna PasswordHash de su fila en la Data Extension Jurados (JuradoId como Primary
Key). Nunca guardes la contraseña en texto plano en ningún lado (Salesforce, logs,
chats) - solo este hash bcrypt."""
import getpass

import bcrypt

if __name__ == "__main__":
    jurado_id = input("JuradoId (ej. jurado_1): ").strip()
    password = getpass.getpass("Contraseña del jurado: ")
    confirm = getpass.getpass("Confirmar: ")
    if password != confirm:
        raise SystemExit("Las contraseñas no coinciden")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print(f"\nJuradoId: {jurado_id}")
    print(f"PasswordHash: {password_hash}")
