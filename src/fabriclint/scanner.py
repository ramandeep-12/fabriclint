from pathlib import Path

from .models import Finding
from .rules.notebook_rules import RULES


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


def scan_path(target: str | Path) -> tuple[list[Finding], list[Path]]:
    """Discover and scan all supported files under a path."""

    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    files = discover_notebooks(target_path)
    findings: list[Finding] = []

    for file_path in files:
        findings.extend(scan_file(file_path))

    return findings, files
