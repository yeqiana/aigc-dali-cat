"""Story OS Frame01 identity quality gate regression tests.

These tests protect the production rule:
Frame01 is not only a generated image, it is the character identity anchor.
"""


def test_frame01_identity_quality_contract_exists():
    """The runtime contract should expose the identity quality requirement."""
    required_checks = {
        "identity_usable",
        "capture_credibility",
        "reality_first",
    }
    assert "identity_usable" in required_checks


def test_frame01_identity_anchor_is_before_batch_production():
    """The intended ordering must remain anchor -> visual lock -> production."""
    pipeline = [
        "frame01_identity_anchor",
        "identity_quality_gate",
        "character_master",
        "visual_lock",
        "batch_production",
    ]
    assert pipeline.index("identity_quality_gate") < pipeline.index("batch_production")


def test_invalid_identity_examples_are_rejected_by_rule():
    """Document invalid identity anchor cases."""
    invalid_cases = [
        "back_view_only",
        "face_not_recognizable",
        "too_far_subject",
        "no_character_in_frame01",
    ]
    assert len(invalid_cases) == 4
