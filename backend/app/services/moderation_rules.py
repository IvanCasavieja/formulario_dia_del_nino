"""Pure, unit-testable decision logic: turns aggregated Rekognition labels into a verdict.

Kept free of any I/O (no boto3, no DB, no file access) so it's trivial to test with
hand-built label lists - see tests/test_moderation_rules.py.
"""
from dataclasses import dataclass, field

from app.config import get_settings
from app.rekognition import ModerationLabel

settings = get_settings()


@dataclass
class Decision:
    status: str  # "approved" | "needs_review" | "rejected"
    reason: str
    triggered_labels: list[dict] = field(default_factory=list)


def aggregate_labels(frames: list[list[ModerationLabel]]) -> list[ModerationLabel]:
    """Dedupes labels by name across all frames, keeping the max confidence seen for each."""
    best: dict[str, ModerationLabel] = {}
    for frame_labels in frames:
        for label in frame_labels:
            existing = best.get(label.name)
            if existing is None or label.confidence > existing.confidence:
                best[label.name] = label
    return list(best.values())


def decide(labels: list[ModerationLabel]) -> Decision:
    reject_categories = set(settings.moderation_reject_categories_list)

    reject_hits = [
        label
        for label in labels
        if label.category in reject_categories and label.confidence >= settings.MODERATION_REJECT_CONFIDENCE
    ]
    if reject_hits:
        return Decision(
            status="rejected",
            reason="high_confidence_reject_category",
            triggered_labels=[_label_to_dict(l) for l in reject_hits],
        )

    review_hits = [label for label in labels if label.confidence >= settings.MODERATION_REVIEW_CONFIDENCE]
    if review_hits:
        return Decision(
            status="needs_review",
            reason="moderate_confidence_label",
            triggered_labels=[_label_to_dict(l) for l in review_hits],
        )

    return Decision(status="approved", reason="no_labels_above_threshold", triggered_labels=[])


def _label_to_dict(label: ModerationLabel) -> dict:
    return {"name": label.name, "category": label.category, "confidence": label.confidence}
