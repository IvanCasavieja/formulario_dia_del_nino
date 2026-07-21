import uuid
from pathlib import Path

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app import shared_constants as sc
from app.config import get_settings

settings = get_settings()

_client = None


def get_r2_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=BotoConfig(signature_version="s3v4", region_name="auto"),
        )
    return _client


def build_video_key(submission_id: uuid.UUID, content_type: str) -> str:
    extension = sc.MIME_TYPE_TO_EXTENSION.get(content_type, ".bin")
    return f"submissions/{submission_id}/{uuid.uuid4()}{extension}"


def create_presigned_put_url(key: str, content_type: str) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key, "ContentType": content_type},
        ExpiresIn=settings.PRESIGNED_PUT_TTL_SECONDS,
    )


def create_presigned_get_url(key: str) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.PRESIGNED_GET_TTL_SECONDS,
    )


def head_object(key: str) -> dict | None:
    """Returns the object metadata, or None if it doesn't exist (or isn't accessible yet)."""
    client = get_r2_client()
    try:
        return client.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def download_to_temp_file(key: str, destination: Path) -> None:
    client = get_r2_client()
    client.download_file(settings.R2_BUCKET_NAME, key, str(destination))
