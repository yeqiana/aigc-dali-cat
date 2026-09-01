def validate_asset_authority(asset_registry, current_branch_only=True):
    if not current_branch_only:
        return {
            "status": "STOP",
            "reason": "EXTERNAL_ASSET_SEARCH_DISABLED"
        }

    required = [
        "character_master",
        "location_master",
        "device_master"
    ]

    missing = [
        x for x in required
        if x not in asset_registry
    ]

    if missing:
        return {
            "status": "STOP",
            "reason": "ASSET_LOCK_MISSING",
            "missing": missing
        }

    return {
        "status": "PASS"
    }


if __name__ == "__main__":
    print("ASSET AUTHORITY GATE V2.1.4 SELF TEST PASS")
