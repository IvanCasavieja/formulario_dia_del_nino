"""Sets fake-but-valid env vars before any `app.*` module is imported by a test file.

app.config.Settings requires every non-defaulted field to be present at import time -
these are throwaway values good enough for unit tests that never actually call R2 or
Salesforce for real. conftest.py is collected before sibling test modules, so this
module-level code runs first.
"""
import os

os.environ.setdefault("R2_ACCESS_KEY_ID", "test")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("R2_ENDPOINT_URL", "https://test.r2.cloudflarestorage.com")
os.environ.setdefault("R2_BUCKET_NAME", "test-bucket")
os.environ.setdefault("UPLOAD_TOKEN_SECRET", "test-upload-secret-at-least-32-bytes-long")
os.environ.setdefault("ADMIN_JWT_SECRET", "test-admin-secret-at-least-32-bytes-long")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "$2b$12$KIXQ2N3xX0f7c1234567uEabcdefghijklmnopqrstuvwxyzABCDE")
