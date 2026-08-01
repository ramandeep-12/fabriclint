import re
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern

from fabriclint.models import Finding


@dataclass(frozen=True)
class RegexRule:
    """A FabricLint rule based on a regular-expression pattern."""

    rule_id: str
    severity: str
    pattern: Pattern[str]
    message: str
    suggestion: str

    def scan(self, source: str, file_path: Path) -> list[Finding]:
        """Scan source code and return all matches for this rule."""

        findings: list[Finding] = []

        for line_number, line in enumerate(source.splitlines(), start=1):
            if self.pattern.search(line):
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=self.message,
                        suggestion=self.suggestion,
                        file_path=file_path,
                        line_number=line_number,
                    )
                )

        return findings