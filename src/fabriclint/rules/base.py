import re
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern

from fabriclint.models import Finding


IGNORE_PATTERN = re.compile(
    r"#\s*fabriclint:\s*ignore(?:\s+([A-Z0-9_,\-\s]+))?",
    re.IGNORECASE,
)


def is_rule_ignored(line: str, rule_id: str) -> bool:
    """Return True when the line suppresses the given rule."""

    match = IGNORE_PATTERN.search(line)

    if match is None:
        return False

    ignored_rules_text = match.group(1)

    # `# fabriclint: ignore` suppresses every rule on the line.
    if ignored_rules_text is None:
        return True

    ignored_rules = {
        value.strip().upper()
        for value in ignored_rules_text.split(",")
        if value.strip()
    }

    return rule_id.upper() in ignored_rules


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
            if is_rule_ignored(line, self.rule_id):
                continue

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