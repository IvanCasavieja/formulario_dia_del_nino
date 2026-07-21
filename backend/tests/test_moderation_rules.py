from app.rekognition import ModerationLabel
from app.services import moderation_rules


def _label(name: str, category: str, confidence: float) -> ModerationLabel:
    return ModerationLabel(name=name, category=category, confidence=confidence)


def test_no_labels_approved():
    assert moderation_rules.decide([]).status == "approved"


def test_low_confidence_label_approved():
    labels = [_label("Female Swimwear Or Underwear", "Suggestive", 20.0)]
    assert moderation_rules.decide(labels).status == "approved"


def test_medium_confidence_needs_review():
    labels = [_label("Female Swimwear Or Underwear", "Suggestive", 60.0)]
    assert moderation_rules.decide(labels).status == "needs_review"


def test_high_confidence_reject_category_rejected():
    labels = [_label("Graphic Violence Or Gore", "Violence", 95.0)]
    assert moderation_rules.decide(labels).status == "rejected"


def test_reject_category_below_reject_threshold_falls_to_review():
    # A reject-category label present but below the (higher) reject threshold should
    # still trip the review threshold rather than being silently ignored.
    labels = [_label("Graphic Violence Or Gore", "Violence", 60.0)]
    assert moderation_rules.decide(labels).status == "needs_review"


def test_most_severe_wins_across_multiple_labels():
    labels = [
        _label("Female Swimwear Or Underwear", "Suggestive", 55.0),
        _label("Graphic Violence Or Gore", "Violence", 95.0),
    ]
    decision = moderation_rules.decide(labels)
    assert decision.status == "rejected"


def test_aggregate_labels_keeps_max_confidence_per_name():
    frames = [
        [_label("Violence", "Violence", 40.0)],
        [_label("Violence", "Violence", 92.0)],
        [_label("Violence", "Violence", 70.0)],
    ]
    aggregated = moderation_rules.aggregate_labels(frames)
    assert len(aggregated) == 1
    assert aggregated[0].confidence == 92.0


def test_aggregate_labels_across_different_names():
    frames = [
        [_label("Violence", "Violence", 40.0)],
        [_label("Drugs", "Drugs", 55.0)],
    ]
    aggregated = moderation_rules.aggregate_labels(frames)
    assert {l.name for l in aggregated} == {"Violence", "Drugs"}
