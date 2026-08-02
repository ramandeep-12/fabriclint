import argparse
import json
import sys
from pathlib import Path

from fabriclint.models import Finding
from fabriclint.scanner import scan_path


SEVERITY_ORDER = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
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


def print_console_report(
    findings: list[Finding],
    scanned_files: list[Path],
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
        return

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


def print_json_report(
    findings: list[Finding],
    scanned_files: list[Path],
) -> None:
    """Print a machine-readable JSON report."""

    report = {
        "tool": "FabricLint",
        "files_scanned": len(scanned_files),
        "issues_found": len(findings),
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


def run_scan(path: str, output_format: str = "console") -> int:
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

    if output_format == "json":
        print_json_report(findings, scanned_files)
    else:
        if not scanned_files:
            print("No notebook-content.py files were found.")
            return 0

        print_console_report(findings, scanned_files)

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return run_scan(
            path=args.path,
            output_format=args.format,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
