import json
from pathlib import Path

from fabriclint.items import FabricItem
from fabriclint.models import Finding


PIPELINE_FILE = "pipeline-content.json"


def create_pipeline_finding(
    rule_id: str,
    severity: str,
    message: str,
    suggestion: str,
    file_path: Path,
    line_number: int = 1,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        suggestion=suggestion,
        file_path=file_path,
        line_number=line_number,
    )


def validate_pipeline(
    item: FabricItem,
) -> list[Finding]:
    """Validate a DataPipeline item."""

    if item.item_type != "DataPipeline":
        return []

    pipeline_path = item.path / PIPELINE_FILE

    # FL200
    if not pipeline_path.is_file():
        return [
            create_pipeline_finding(
                rule_id="FL200",
                severity="HIGH",
                message="Missing pipeline-content.json.",
                suggestion=(
                    "Restore the Fabric Data Pipeline definition file."
                ),
                file_path=pipeline_path,
            )
        ]

    try:
        data = json.loads(
            pipeline_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        return [
            create_pipeline_finding(
                rule_id="FL201",
                severity="HIGH",
                message="Invalid JSON in pipeline-content.json.",
                suggestion=(
                    "Fix the pipeline JSON syntax before deployment."
                ),
                file_path=pipeline_path,
                line_number=exc.lineno,
            )
        ]

    findings: list[Finding] = []

    activities = data.get("properties", {}).get(
        "activities",
        [],
    )

    # FL202
    if not activities:
        findings.append(
            create_pipeline_finding(
                rule_id="FL202",
                severity="MEDIUM",
                message="Data Pipeline contains no activities.",
                suggestion=(
                    "Verify that the pipeline is intentionally empty."
                ),
                file_path=pipeline_path,
            )
        )

    return findings