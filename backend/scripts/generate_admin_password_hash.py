"""Run locally, paste the output into ADMIN_PASSWORD_HASH. Never store the plaintext
admin password anywhere (env vars, logs, dashboards) - only this bcrypt hash."""
import getpass

import bcrypt

if __name__ == "__main__":
    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm: ")
    if password != confirm:
        raise SystemExit("Passwords don't match")
    print(bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"))
