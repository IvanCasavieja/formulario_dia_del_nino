from dataclasses import dataclass

import boto3

from app.config import get_settings

settings = get_settings()

_client = None


def get_rekognition_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "rekognition",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _client


@dataclass
class ModerationLabel:
    name: str
    category: str
    confidence: float


def detect_moderation_labels(frame_bytes: bytes) -> list[ModerationLabel]:
    """Runs Rekognition's image moderation API directly on raw frame bytes.

    Deliberately uses Image={'Bytes': ...} rather than an S3Object reference: the video
    lives in R2, not AWS S3, and Rekognition's video API (StartContentModeration) requires
    an S3 bucket. Running the image API on extracted frames avoids ever copying videos
    into AWS just to moderate them.
    """
    client = get_rekognition_client()
    response = client.detect_moderation_labels(
        Image={"Bytes": frame_bytes},
        MinConfidence=settings.MODERATION_MIN_CONFIDENCE_FLOOR,
    )
    labels = []
    for label in response.get("ModerationLabels", []):
        name = label["Name"]
        confidence = label["Confidence"]
        parent_name = label.get("ParentName") or name
        labels.append(ModerationLabel(name=name, category=parent_name, confidence=confidence))
    return labels
