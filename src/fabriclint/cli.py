import argparse
import json
import sys
from pathlib import Path

from fabriclint.config import load_config
from fabriclint.items import (
    FabricItem,
    discover_fabric_items,
    summarize_items,
)
from fabriclint.models import Finding
from fabriclint.scanner import scan_path


SEVERITY_ORDER = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}

SEVERITY_LEVEL = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fabriclint",
        description=(
            "Scan Microsoft Fabric notebook source files for "
            "security, reliability and Spark performance risks."
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a Fabric project.",
    )

    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan. Default: current directory.",
    )

    scan_parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format. Default: console.",
    )

    scan_parser.add_argument(
        "--fail-on",
        choices=["low", "medium", "high"],
        default=None,
        help=(
            "Return exit code 1 when an issue at or above this "
            "severity is detected."
        ),
    )

    items_parser = subparsers.add_parser(
        "items",
        help="Discover Microsoft Fabric items in a project.",
    )

    items_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to inspect. Default: current directory.",
    )

    items_parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format. Default: console.",
    )
    return parser


def get_display_path(file_path: Path) -> str:
    """Return a readable relative path when possible."""

    try:
        return str(file_path.relative_to(Path.cwd()))
    except ValueError:
        return str(file_path)


def sort_findings(findings: list[Finding]) -> list[Finding]:
    """Sort findings by severity, file and line number."""

    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(finding.severity, 99),
            str(finding.file_path),
            finding.line_number,
        ),
    )


def threshold_reached(
    findings: list[Finding],
    fail_on: str | None,
) -> bool:
    """Return True when findings reach the configured threshold."""

    if fail_on is None:
        return False

    required_level = SEVERITY_LEVEL[fail_on.upper()]

    return any(
        SEVERITY_LEVEL.get(finding.severity.upper(), 0)
        >= required_level
        for finding in findings
    )


def print_console_report(
    findings: list[Finding],
    scanned_files: list[Path],
    fail_on: str | None,
    failed: bool,
) -> None:
    """Print a human-readable report."""

    print()
    print("FabricLint scan")
    print("=" * 60)
    print(f"Files scanned: {len(scanned_files)}")
    print(f"Issues found: {len(findings)}")
    print()

    if not findings:
        print("No issues detected.")
    else:
        for finding in sort_findings(findings):
            print(
                f"{finding.severity:<7} "
                f"{finding.rule_id:<6} "
                f"{get_display_path(finding.file_path)}:"
                f"{finding.line_number}"
            )
            print(f"        {finding.message}")
            print(f"        Suggestion: {finding.suggestion}")
            print()

    if fail_on is not None:
        status = "FAILED" if failed else "PASSED"

        print("-" * 60)
        print(
            f"Quality gate: {status} "
            f"(fail on {fail_on.upper()} or above)"
        )


def print_json_report(
    findings: list[Finding],
    scanned_files: list[Path],
    fail_on: str | None,
    failed: bool,
) -> None:
    """Print a machine-readable JSON report."""

    report = {
        "tool": "FabricLint",
        "files_scanned": len(scanned_files),
        "issues_found": len(findings),
        "quality_gate": {
            "enabled": fail_on is not None,
            "threshold": fail_on.upper() if fail_on else None,
            "passed": not failed,
        },
        "findings": [
            {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "file": get_display_path(finding.file_path),
                "line": finding.line_number,
                "message": finding.message,
                "suggestion": finding.suggestion,
            }
            for finding in sort_findings(findings)
        ],
    }

    print(json.dumps(report, indent=2))


def run_scan(
    path: str,
    output_format: str = "console",
    fail_on: str | None = None,
) -> int:
    try:
        findings, scanned_files = scan_path(path)
    except (FileNotFoundError, ValueError) as exc:
        if output_format == "json":
            print(
                json.dumps(
                    {
                        "tool": "FabricLint",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(f"Error: {exc}", file=sys.stderr)

        return 2

    failed = threshold_reached(
        findings=findings,
        fail_on=fail_on,
    )

    if output_format == "json":
        print_json_report(
            findings=findings,
            scanned_files=scanned_files,
            fail_on=fail_on,
            failed=failed,
        )
    else:
        if not scanned_files:
            print("No notebook-content.py files were found.")
        else:
            print_console_report(
                findings=findings,
                scanned_files=scanned_files,
                fail_on=fail_on,
                failed=failed,
            )

    return 1 if failed else 0

def print_items_console(
    items: list[FabricItem],
) -> None:
    """Print discovered Fabric items as a console report."""

    counts = summarize_items(items)

    print()
    print("Fabric item discovery")
    print("=" * 60)
    print(f"Items found: {len(items)}")
    print()

    if not items:
        print("No supported Fabric items were found.")
        return

    print("Items by type:")

    for item_type, count in counts.items():
        print(f"  {item_type:<16} {count}")

    print()
    print("Discovered items:")

    for item in items:
        print(
            f"  {item.item_type.upper():<16} "
            f"{get_display_path(item.path)}"
        )

def print_items_json(
    items: list[FabricItem],
) -> None:
    """Print discovered Fabric items as JSON."""

    report = {
        "tool": "FabricLint",
        "command": "items",
        "items_found": len(items),
        "counts": summarize_items(items),
        "items": [
            {
                "name": item.name,
                "type": item.item_type,
                "path": get_display_path(item.path),
            }
            for item in items
        ],
    }

    print(json.dumps(report, indent=2))


def run_items(
    path: str,
    output_format: str = "console",
) -> int:
    """Discover and report Fabric items."""

    try:
        target_path = Path(path).expanduser().resolve()

        if not target_path.exists():
            raise FileNotFoundError(
                f"Path does not exist: {target_path}"
            )

        config = load_config(target_path)
        discovered_items = discover_fabric_items(target_path)

        items = [
            item
            for item in discovered_items
            if not config.is_excluded(item.path)
        ]

    except (FileNotFoundError, ValueError) as exc:
        if output_format == "json":
            print(
                json.dumps(
                    {
                        "tool": "FabricLint",
                        "command": "items",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(f"Error: {exc}", file=sys.stderr)

        return 2

    if output_format == "json":
        print_items_json(items)
    else:
        print_items_console(items)

    return 0

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return run_scan(
            path=args.path,
            output_format=args.format,
            fail_on=args.fail_on,
        )

    if args.command == "items":
        return run_items(
            path=args.path,
            output_format=args.format,
        )

    parser.print_help()
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
