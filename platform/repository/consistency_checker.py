"""
Repository data consistency checker.

Phase 1-P1.7:
Compare legacy JSONL storage and new repository storage.
"""

from dataclasses import dataclass


@dataclass
class ConsistencyResult:
    entity_type: str
    total_checked: int
    matched: int
    mismatched: int

    @property
    def success(self) -> bool:
        return self.mismatched == 0


class RepositoryConsistencyChecker:
    """Validate dual-write migration data consistency."""

    def compare(self, entity_type: str, legacy_items, new_items):
        legacy_map = {item.get("id"): item for item in legacy_items}
        new_map = {item.get("id"): item for item in new_items}

        matched = 0
        mismatched = 0

        for key, value in legacy_map.items():
            if new_map.get(key) == value:
                matched += 1
            else:
                mismatched += 1

        return ConsistencyResult(
            entity_type=entity_type,
            total_checked=len(legacy_map),
            matched=matched,
            mismatched=mismatched,
        )
