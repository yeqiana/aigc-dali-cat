from pathlib import Path

from character_appearance_anchor import verify_frame01_identity_anchor


def test_frame01_identity_anchor_missing_contract(tmp_path: Path):
    result = verify_frame01_identity_anchor(tmp_path)
    assert "FRAME01_IDENTITY_ANCHOR_CHARACTER_CONTRACT_MISSING" in result


def test_frame01_identity_anchor_missing_anchor(tmp_path: Path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta" / "character-contract.json").write_text(
        '{"cast":{"members":[{"id":"P01"}]}}',
        encoding="utf-8",
    )
    assert "FRAME01_IDENTITY_ANCHOR_MISSING" in verify_frame01_identity_anchor(tmp_path)
