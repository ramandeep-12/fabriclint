import argparse
import sys
from pathlib import Path

from .scanner import scan_path


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

    return parser


def run_scan(path: str) -> int:
    try:
        findings, scanned_files = scan_path(path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not scanned_files:
        print("No notebook-content.py files were found.")
        return 0

    print()
    print("FabricLint scan")
    print("=" * 60)
    print(f"Files scanned: {len(scanned_files)}")
    print(f"Issues found: {len(findings)}")
    print()

    if not findings:
        print("No issues detected.")
        return 0

    sorted_findings = sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(finding.severity, 99),
            str(finding.file_path),
            finding.line_number,
        ),
    )

    for finding in sorted_findings:
        try:
            display_path = finding.file_path.relative_to(Path.cwd())
        except ValueError:
            display_path = finding.file_path

        print(
            f"{finding.severity:<7} "
            f"{finding.rule_id:<6} "
            f"{display_path}:{finding.line_number}"
        )
        print(f"        {finding.message}")
        print(f"        Suggestion: {finding.suggestion}")
        print()

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return run_scan(args.path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
