from pathlib import Path

from .models import Finding
from .rules.notebook_rules import RULES
from fabriclint.config import load_config

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
    """Discover and scan all supported files under a path."""

    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {target_path}"
        )

    project_root = (
        target_path
        if target_path.is_dir()
        else target_path.parent
    )

    config = load_config(project_root)

    discovered_files = discover_notebooks(target_path)

    files = [
        file_path
        for file_path in discovered_files
        if not config.is_excluded(
            file_path
        )
    ]

    findings: list[Finding] = []

    for file_path in files:
        file_findings = scan_file(file_path)

        ignored_rules = config.ignored_rules_for_file(
            file_path
        )

        findings.extend(
            finding
            for finding in file_findings
            if finding.rule_id.upper() not in ignored_rules
        )

    return findings, files

