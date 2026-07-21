"""Generates a random secret for UPLOAD_TOKEN_SECRET / ADMIN_JWT_SECRET. Use a
different one for each - a token of one kind must never be valid as the other."""
import secrets

if __name__ == "__main__":
    print(secrets.token_urlsafe(48))
