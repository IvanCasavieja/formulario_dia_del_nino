import time

import jwt
import pytest

from app import security

_FIELDS = {
    "parent_first_name": "Juana",
    "parent_last_name": "Pérez",
    "parent_cedula": "1234567",
    "parent_email": "juana@example.com",
    "parent_phone": "099123456",
    "child_first_name": "Sofía",
    "child_last_name": "Pérez",
    "child_cedula": "7654321",
    "terms_accepted": True,
}


def test_valid_upload_token_accepted():
    token = security.create_upload_token("sub-1", "video-key-1", _FIELDS)
    claims = security.decode_upload_token(token, "sub-1")
    assert claims["sub"] == "sub-1"
    assert claims["video_key"] == "video-key-1"
    assert claims["fields"] == _FIELDS


def test_expired_upload_token_rejected(monkeypatch):
    monkeypatch.setattr(security.settings, "UPLOAD_TOKEN_TTL_SECONDS", -10)
    token = security.create_upload_token("sub-1", "video-key-1", _FIELDS)
    with pytest.raises(security.TokenExpired):
        security.decode_upload_token(token, "sub-1")


def test_wrong_purpose_rejected():
    now = int(time.time())
    payload = {"sub": "sub-1", "purpose": "not_upload_confirm", "video_key": "k", "fields": {}, "iat": now, "exp": now + 100}
    token = jwt.encode(payload, security.settings.UPLOAD_TOKEN_SECRET, algorithm="HS256")
    with pytest.raises(security.TokenInvalid):
        security.decode_upload_token(token, "sub-1")


def test_submission_id_mismatch_rejected():
    token = security.create_upload_token("sub-1", "video-key-1", _FIELDS)
    with pytest.raises(security.TokenSubmissionMismatch):
        security.decode_upload_token(token, "sub-2")


def test_tampered_signature_rejected():
    token = security.create_upload_token("sub-1", "video-key-1", _FIELDS)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(security.TokenInvalid):
        security.decode_upload_token(tampered, "sub-1")


def test_upload_token_cannot_be_replayed_as_admin_token():
    # Different secrets for the two token kinds - an upload token must never verify as
    # an admin session token even if somehow presented as one.
    upload_token = security.create_upload_token("sub-1", "video-key-1", _FIELDS)
    with pytest.raises(security.TokenInvalid):
        security.decode_admin_token(upload_token)


def test_admin_token_missing_role_rejected():
    now = int(time.time())
    payload = {"sub": "admin", "iat": now, "exp": now + 100}  # no "role" claim
    token = jwt.encode(payload, security.settings.ADMIN_JWT_SECRET, algorithm="HS256")
    with pytest.raises(security.TokenInvalid):
        security.decode_admin_token(token)


def test_valid_admin_token_accepted():
    token = security.create_admin_token()
    claims = security.decode_admin_token(token)
    assert claims["role"] == "admin"
