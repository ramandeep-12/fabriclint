import json
from pathlib import Path

from fabriclint.items import FabricItem
from fabriclint.pipeline import validate_pipeline


def make_pipeline(tmp_path: Path) -> FabricItem:
    pipeline_path = tmp_path / "CustomerLoad.DataPipeline"
    pipeline_path.mkdir()

    return FabricItem(
        name="CustomerLoad",
        item_type="DataPipeline",
        path=pipeline_path,
    )


def test_missing_pipeline_content_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL200"
        for finding in findings
    )


def test_invalid_pipeline_json_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    (
        item.path / "pipeline-content.json"
    ).write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL201"
        for finding in findings
    )


def test_empty_pipeline_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": []
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL202"
        for finding in findings
    )


def test_pipeline_with_activity_passes(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy"
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert findings == []