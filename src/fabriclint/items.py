from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ITEM_SUFFIXES: dict[str, str] = {
    ".Notebook": "Notebook",
    ".DataPipeline": "DataPipeline",
    ".SemanticModel": "SemanticModel",
    ".Environment": "Environment",
    ".Eventstream": "Eventstream",
}


@dataclass(frozen=True)
class FabricItem:
    """A Microsoft Fabric item found in a local project."""

    name: str
    item_type: str
    path: Path


def identify_fabric_item(path: Path) -> FabricItem | None:
    """Create a FabricItem when a directory has a supported suffix."""

    if not path.is_dir():
        return None

    for suffix, item_type in ITEM_SUFFIXES.items():
        if path.name.endswith(suffix):
            item_name = path.name.removesuffix(suffix)

            if not item_name:
                return None

            return FabricItem(
                name=item_name,
                item_type=item_type,
                path=path.resolve(),
            )

    return None


def discover_fabric_items(
    target: str | Path,
) -> list[FabricItem]:
    """Discover supported Fabric item directories under a path."""

    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {target_path}"
        )

    if target_path.is_file():
        return []

    # Include target_path because it might itself be an item folder.
    candidate_directories = [
        target_path,
        *(
            path
            for path in target_path.rglob("*")
            if path.is_dir()
        ),
    ]

    discovered_items: list[FabricItem] = []

    for directory in candidate_directories:
        item = identify_fabric_item(directory)

        if item is not None:
            discovered_items.append(item)

    return sorted(
        discovered_items,
        key=lambda item: (
            item.item_type.lower(),
            item.path.as_posix().lower(),
        ),
    )


def summarize_items(
    items: list[FabricItem],
) -> dict[str, int]:
    """Return the number of discovered items by item type."""

    counts = Counter(
        item.item_type
        for item in items
    )

    return {
        item_type: counts[item_type]
        for item_type in ITEM_SUFFIXES.values()
        if counts[item_type] > 0
    }
