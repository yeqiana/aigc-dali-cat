from platform.gateway.phase8_final_release_package import (
    Phase8FinalReleasePackageBuilder,
)


def test_phase8_release_package_ready():
    package = Phase8FinalReleasePackageBuilder().build(
        migration_completed=True,
        primary_runtime="V3_RUNTIME",
    )

    assert package.status == "READY"
    assert package.migration_state == "COMPLETED"


def test_phase8_release_package_blocked_when_v3_not_primary():
    package = Phase8FinalReleasePackageBuilder().build(
        migration_completed=True,
        primary_runtime="V2_RUNTIME",
    )

    assert package.status == "BLOCKED"
    assert "v3_not_primary_runtime" in package.reasons
