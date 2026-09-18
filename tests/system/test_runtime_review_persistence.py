import sys
from pathlib import Path


SYSTEM = Path(__file__).resolve().parents[2] / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_review_persistence


def test_parse_current_and_attempt_request_paths(tmp_path):
    ep = tmp_path / "episodes" / "demo"
    current = ep / "meta/runtime/reviews/story-semantic-request.json"
    attempt = ep / "meta/runtime/reviews/story-semantic-attempt-2-request.json"
    c = runtime_review_persistence.parse_request_path(current)
    a = runtime_review_persistence.parse_request_path(attempt)
    assert c["review_kind"] == "story-semantic"
    assert c["record_key"] == "CURRENT"
    assert a["record_key"] == "ATTEMPT:2"
    assert a["attempt"] == 2
