import json
from pathlib import Path

from fabriclint.cli import run_items
from fabriclint.items import (
    discover_fabric_items,
    summarize_items,
)


def test_discovers_supported_fabric_items(
    tmp_path: Path,
) -> None:
    item_directories = [
        "Sales.Notebook",
        "CustomerLoad.DataPipeline",
        "SalesModel.SemanticModel",
        "SparkRuntime.Environment",
        "OrderEvents.Eventstream",
    ]

    for directory_name in item_directories:
        (tmp_path / directory_name).mkdir()

    # This ordinary folder must not be identified as a Fabric item.
    (tmp_path / "documentation").mkdir()

    items = discover_fabric_items(tmp_path)

    assert len(items) == 5

    item_types = {
        item.item_type
        for item in items
    }

    assert item_types == {
        "Notebook",
        "DataPipeline",
        "SemanticModel",
        "Environment",
        "Eventstream",
    }


def test_discovers_target_when_target_is_an_item(
    tmp_path: Path,
) -> None:
    notebook_directory = tmp_path / "Sales.Notebook"
    notebook_directory.mkdir()

    items = discover_fabric_items(notebook_directory)

    assert len(items) == 1
    assert items[0].name == "Sales"
    assert items[0].item_type == "Notebook"


def test_summarizes_items_by_type(
    tmp_path: Path,
) -> None:
    (tmp_path / "Sales.Notebook").mkdir()
    (tmp_path / "Customer.Notebook").mkdir()
    (tmp_path / "Load.DataPipeline").mkdir()

    items = discover_fabric_items(tmp_path)
    counts = summarize_items(items)

    assert counts["Notebook"] == 2
    assert counts["DataPipeline"] == 1


def test_items_json_output(
    tmp_path: Path,
    capsys,
) -> None:
    (tmp_path / "Sales.Notebook").mkdir()
    (tmp_path / "Load.DataPipeline").mkdir()

    exit_code = run_items(
        path=str(tmp_path),
        output_format="json",
    )

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 0
    assert report["items_found"] == 2
    assert report["counts"]["Notebook"] == 1
    assert report["counts"]["DataPipeline"] == 1
