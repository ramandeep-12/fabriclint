from pathlib import Path

from .models import Finding
from .rules.notebook_rules import RULES
from fabriclint.config import load_config
from fabriclint.items import discover_fabric_items
from fabriclint.pipeline import validate_pipeline
from fabriclint.platform import validate_item_system_metadata
from fabriclint.config import (
    apply_rule_overrides,
)
NOTEBOOK_FILE_NAME = "notebook-content.py"


def discover_notebooks(target: Path) -> list[Path]:
    """Find Fabric notebook source files under the target path."""

    if target.is_file():
        if target.name == NOTEBOOK_FILE_NAME:
            return [target]

        return []

    return sorted(target.rglob(NOTEBOOK_FILE_NAME))


def scan_file(file_path: Path) -> list[Finding]:
    """Run all FabricLint rules against one notebook file."""

    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Unable to read {file_path} as UTF-8 text."
        ) from exc

    findings: list[Finding] = []

    for rule in RULES:
        findings.extend(rule.scan(source, file_path))

    return findings

def scan_path(
    target: str | Path,
) -> tuple[list[Finding], list[Path]]:
    """Scan a Fabric project for supported issues."""

    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {target_path}"
        )

    config = load_config(target_path)

    all_findings: list[Finding] = []

    # --------------------------------------------------
    # 1. Scan notebook source files
    # --------------------------------------------------

    discovered_files = discover_notebooks(target_path)

    notebook_files = [
        file_path
        for file_path in discovered_files
        if not config.is_excluded(file_path)
    ]

    for file_path in notebook_files:
        file_findings = scan_file(file_path)

        ignored_rules = config.ignored_rules_for_file(
            file_path
        )

        all_findings.extend(
            finding
            for finding in file_findings
            if finding.rule_id.upper()
            not in ignored_rules
        )

    # --------------------------------------------------
    # 2. Discover Fabric items
    # --------------------------------------------------

    fabric_items = discover_fabric_items(target_path)

    fabric_items = [
        item
        for item in fabric_items
        if not config.is_excluded(item.path)
    ]

    # --------------------------------------------------
    # 3. Validate item metadata
    # --------------------------------------------------

    for item in fabric_items:
        metadata_findings = (
            validate_item_system_metadata(item)
        )

        for finding in metadata_findings:
            ignored_rules = (
                config.ignored_rules_for_file(
                    finding.file_path
                )
            )

            if (
                finding.rule_id.upper()
                not in ignored_rules
            ):
                all_findings.append(finding)

    # --------------------------------------------------
    # 4. Validate Data Pipelines
    # --------------------------------------------------

    for item in fabric_items:
        if item.item_type != "DataPipeline":
            continue

        pipeline_findings = validate_pipeline(item)

        for finding in pipeline_findings:
            ignored_rules = (
                config.ignored_rules_for_file(
                    finding.file_path
                )
            )

            if (
                finding.rule_id.upper()
                not in ignored_rules
            ):
                all_findings.append(finding)

    scanned_targets: list[Path] = []

# Count every discovered Fabric item
    scanned_targets.extend(
        item.path
        for item in fabric_items
    )

# If scanning a standalone notebook file that wasn't discovered
# as an item folder, include it too.
    for notebook_file in notebook_files:
        if not any(
            notebook_file.is_relative_to(item.path)
            for item in fabric_items
        ):
            scanned_targets.append(notebook_file)
    all_findings = apply_rule_overrides(
    all_findings,
    config,
    )

    return all_findings, scanned_targets
    
