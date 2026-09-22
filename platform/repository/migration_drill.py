"""Phase 1-P1.8 migration drill helpers.

Only simulates migration verification.
It does not modify production runtime state.
"""

from dataclasses import dataclass


@dataclass
class MigrationDrillResult:
    entity_type: str
    checked_count: int
    success: bool
    message: str


class MigrationDrill:
    """Read-only migration rehearsal."""

    def verify(self, entity_type: str, legacy_data: list, target_data: list):
        success = legacy_data == target_data
        return MigrationDrillResult(
            entity_type=entity_type,
            checked_count=len(legacy_data),
            success=success,
            message="MATCH" if success else "MISMATCH",
        )
