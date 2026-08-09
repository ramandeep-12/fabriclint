import json
from pathlib import Path


def write_valid_platform(
    item_directory: Path,
    item_type: str,
    display_name: str,
) -> None:
    """Create a valid synthetic Fabric .platform file for tests."""

    platform_data = {
        "version": "2.0",
        "$schema": "test-schema",
        "config": {
            "logicalId": (
                "11111111-1111-4111-8111-111111111111"
            )
        },
        "metadata": {
            "type": item_type,
            "displayName": display_name,
        },
    }

    platform_file = item_directory / ".platform"

    platform_file.write_text(
        json.dumps(platform_data),
        encoding="utf-8",
    )