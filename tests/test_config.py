from pathlib import Path

from fabriclint.scanner import scan_path
from tests.helpers import write_valid_platform


def create_notebook(
    root: Path,
    source: str,
) -> Path:
    notebook_directory = root / "Example.Notebook"
    notebook_directory.mkdir(parents=True)

    notebook_file = notebook_directory / "notebook-content.py"
    notebook_file.write_text(source, encoding="utf-8")

    return notebook_file


def test_globally_ignored_rule_is_not_reported(
    tmp_path: Path,
) -> None:
    create_notebook(
        tmp_path,
        "rows = customer_df.collect()",
    )

    config_file = tmp_path / ".fabriclint.toml"
    config_file.write_text(
        """
[tool.fabriclint]
ignore = ["FL003"]
""",
        encoding="utf-8",
    )

    findings, _ = scan_path(tmp_path)

    assert not any(
        finding.rule_id == "FL003"
        for finding in findings
    )


def test_per_file_ignore_suppresses_rule(
    tmp_path: Path,
) -> None:
    create_notebook(
        tmp_path,
        'df.coalesce(1).write.mode("overwrite").save("table")',
    )

    config_file = tmp_path / ".fabriclint.toml"
    config_file.write_text(
        """
[tool.fabriclint]

[tool.fabriclint.per-file-ignores]
"Example.Notebook/**" = ["FL004"]
""",
        encoding="utf-8",
    )

    findings, _ = scan_path(tmp_path)
    rule_ids = {
        finding.rule_id
        for finding in findings
    }

    assert "FL004" not in rule_ids
    assert "FL005" in rule_ids

def test_root_config_applies_when_scanning_subdirectory(
    tmp_path: Path,
) -> None:
    broken_project = tmp_path / "examples" / "broken-project"
    notebook_directory = broken_project / "Sales.Notebook"
    notebook_directory.mkdir(parents=True)
    write_valid_platform(
        notebook_directory,
        item_type="Notebook",
        display_name="Sales",
    )

    notebook_file = notebook_directory / "notebook-content.py"
    notebook_file.write_text(
        """
client_secret = "fake-secret"
workspace_id = "12345678-1234-1234-1234-123456789012"
rows = customer_df.collect()
df.coalesce(1).write.mode("overwrite").save("table")
""",
        encoding="utf-8",
    )

    config_file = tmp_path / ".fabriclint.toml"
    config_file.write_text(
        """
[tool.fabriclint.per-file-ignores]
"examples/broken-project/**" = [
    "FL001",
    "FL002",
    "FL003",
    "FL004",
    "FL005"
]
""",
        encoding="utf-8",
    )

    findings, files = scan_path(broken_project)

    assert len(files) == 1
    assert findings == []