"""Sets fake-but-valid env vars before any `app.*` module is imported by a test file.

app.db builds a SQLAlchemy engine at import time from Settings(), which requires every
non-defaulted field in app.config.Settings to be present - these are throwaway values
good enough for unit tests that never actually open a DB connection or call R2.
conftest.py is collected before sibling test modules, so this module-level code runs
first.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("R2_ENDPOINT_URL", "https://test.r2.cloudflarestorage.com")
os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
os.environ.setdefault("UPLOAD_TOKEN_SECRET", "test-upload-secret-at-least-32-bytes-long")
os.environ.setdefault("ADMIN_JWT_SECRET", "test-admin-secret-at-least-32-bytes-long")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "$2b$12$KIXQ2N3xX0f7c1234567uEabcdefghijklmnopqrstuvwxyzABCDE")
