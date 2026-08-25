import json
from pathlib import Path

from fabriclint.items import FabricItem
from fabriclint.platform import validate_item_system_metadata


def make_item(tmp_path: Path) -> FabricItem:
    item_path = tmp_path / "Sales.Notebook"
    item_path.mkdir()

    return FabricItem(
        name="Sales",
        item_type="Notebook",
        path=item_path,
    )


def test_valid_platform_has_no_findings(
    tmp_path: Path,
) -> None:
    item = make_item(tmp_path)

    platform_data = {
        "version": "2.0",
        "$schema": (
            "https://developer.microsoft.com/json-schemas/"
            "fabric/platform/platformProperties.json"
        ),
        "config": {
            "logicalId": (
                "11111111-1111-4111-8111-111111111111"
            )
        },
        "metadata": {
            "type": "Notebook",
            "displayName": "Sales",
        },
    }

    (item.path / ".platform").write_text(
        json.dumps(platform_data),
        encoding="utf-8",
    )

    findings = validate_item_system_metadata(item)

    assert findings == []


def test_missing_platform_is_reported(
    tmp_path: Path,
) -> None:
    item = make_item(tmp_path)

    findings = validate_item_system_metadata(item)

    assert any(
        finding.rule_id == "FL100"
        for finding in findings
    )


def test_invalid_platform_json_is_reported(
    tmp_path: Path,
) -> None:
    item = make_item(tmp_path)

    (item.path / ".platform").write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    findings = validate_item_system_metadata(item)

    assert any(
        finding.rule_id == "FL103"
        for finding in findings
    )


def test_complete_v1_metadata_is_allowed(
    tmp_path: Path,
) -> None:
    item = make_item(tmp_path)

    (item.path / "item.metadata.json").write_text(
        "{}",
        encoding="utf-8",
    )

    (item.path / "item.config.json").write_text(
        "{}",
        encoding="utf-8",
    )

    findings = validate_item_system_metadata(item)

    assert findings == []
