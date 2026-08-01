from pathlib import Path
from fabriclint.scanner import scan_path

def create_notebook(
    root: Path,
    source: str,
) -> Path:
    notebook_directory = root / "Example.Notebook"
    notebook_directory.mkdir(parents=True)

    notebook_file = notebook_directory / "notebook-content.py"
    notebook_file.write_text(source, encoding="utf-8")

    return notebook_file


def test_detects_collect(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        "rows = customer_df.collect()",
    )

    findings, files = scan_path(tmp_path)

    assert len(files) == 1
    assert any(
        finding.rule_id == "FL003"
        for finding in findings
    )


def test_detects_multiple_problems(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        """
client_secret = "fake-secret"
workspace_id = "12345678-1234-1234-1234-123456789012"
df.coalesce(1).write.mode("overwrite").save("Tables/customer")
""",
    )

    findings, _ = scan_path(tmp_path)
    rule_ids = {finding.rule_id for finding in findings}

    assert "FL001" in rule_ids
    assert "FL002" in rule_ids
    assert "FL004" in rule_ids
    assert "FL005" in rule_ids


def test_clean_notebook_has_no_findings(tmp_path: Path) -> None:
    create_notebook(
        tmp_path,
        """
customer_df = spark.table("bronze.customers")
active_df = customer_df.filter("status = 'active'")
active_df.write.format("delta").saveAsTable("silver.customers")
""",
    )

    findings, files = scan_path(tmp_path)

    assert len(files) == 1
    assert findings == []
