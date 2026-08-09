from pathlib import Path

from fabriclint.scanner import scan_path
from tests.helpers import write_valid_platform

def create_notebook(
    root: Path,
    source: str,
) -> Path:
    notebook_directory = root / "SuppressionExample.Notebook"
    notebook_directory.mkdir(parents=True)

    write_valid_platform(
        notebook_directory,
        item_type="Notebook",
        display_name="SuppressionExample",
    )

    notebook_file = notebook_directory / "notebook-content.py"

    notebook_file.write_text(
        source,
        encoding="utf-8",
    )

    return notebook_file

def test_suppresses_specific_rule(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        "rows = customer_df.collect()  # fabriclint: ignore FL003",
    )

    findings, _ = scan_path(tmp_path)

    assert not any(
        finding.rule_id == "FL003"
        for finding in findings
    )


def test_does_not_suppress_different_rule(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        "rows = customer_df.collect()  # fabriclint: ignore FL004",
    )

    findings, _ = scan_path(tmp_path)

    assert any(
        finding.rule_id == "FL003"
        for finding in findings
    )


def test_suppresses_multiple_rules(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        (
            'df.coalesce(1).write.mode("overwrite") '
            "# fabriclint: ignore FL004, FL005"
        ),
    )

    findings, _ = scan_path(tmp_path)
    rule_ids = {finding.rule_id for finding in findings}

    assert "FL004" not in rule_ids
    assert "FL005" not in rule_ids


def test_ignore_without_rule_suppresses_all_on_line(
    tmp_path: Path,
) -> None:
    create_notebook(
        tmp_path,
        (
            'df.coalesce(1).write.mode("overwrite") '
            "# fabriclint: ignore"
        ),
    )

    findings, _ = scan_path(tmp_path)

    assert findings == []


def test_unsuppressed_problem_is_detected(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        "rows = customer_df.collect()",
    )

    findings, _ = scan_path(tmp_path)

    assert any(
        finding.rule_id == "FL003"
        for finding in findings
    )
