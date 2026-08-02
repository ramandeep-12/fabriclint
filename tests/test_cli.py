import json
from pathlib import Path

from fabriclint.cli import run_scan


def create_broken_notebook(root: Path) -> None:
    notebook_directory = root / "Example.Notebook"
    notebook_directory.mkdir(parents=True)

    notebook_file = notebook_directory / "notebook-content.py"
    notebook_file.write_text(
        'rows = customer_df.collect()\n',
        encoding="utf-8",
    )


def test_json_output(
    tmp_path: Path,
    capsys,
) -> None:
    create_broken_notebook(tmp_path)

    exit_code = run_scan(
        path=str(tmp_path),
        output_format="json",
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 0
    assert report["tool"] == "FabricLint"
    assert report["files_scanned"] == 1
    assert report["issues_found"] == 1
    assert report["findings"][0]["rule_id"] == "FL003"


def test_json_output_for_invalid_path(capsys) -> None:
    exit_code = run_scan(
        path="/path/that/does/not/exist",
        output_format="json",
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 2
    assert "error" in report
def test_medium_issue_fails_medium_threshold(
    tmp_path: Path,
    capsys,
) -> None:
    create_broken_notebook(tmp_path)

    exit_code = run_scan(
        path=str(tmp_path),
        output_format="console",
        fail_on="medium",
    )

    capsys.readouterr()

    assert exit_code == 1


def test_medium_issue_does_not_fail_high_threshold(
    tmp_path: Path,
    capsys,
) -> None:
    create_broken_notebook(tmp_path)

    exit_code = run_scan(
        path=str(tmp_path),
        output_format="console",
        fail_on="high",
    )

    capsys.readouterr()

    assert exit_code == 0


def test_high_issue_fails_high_threshold(
    tmp_path: Path,
    capsys,
) -> None:
    notebook_directory = tmp_path / "Example.Notebook"
    notebook_directory.mkdir()

    notebook_file = notebook_directory / "notebook-content.py"
    notebook_file.write_text(
        'client_secret = "fake-test-secret"\n',
        encoding="utf-8",
    )

    exit_code = run_scan(
        path=str(tmp_path),
        output_format="json",
        fail_on="high",
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 1
    assert report["quality_gate"]["passed"] is False
    assert report["quality_gate"]["threshold"] == "HIGH"
