from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    """A problem detected by FabricLint."""

    rule_id: str
    severity: str
    message: str
    suggestion: str
    file_path: Path
    line_number: int
