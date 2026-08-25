from dataclasses import dataclass, field, replace
from fnmatch import fnmatch
from pathlib import Path
from fabriclint.models import Finding

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


CONFIG_FILE_NAME = ".fabriclint.toml"


@dataclass
class FabricLintConfig:
    """Configuration loaded from .fabriclint.toml."""

    root: Path
    ignored_rules: set[str] = field(default_factory=set)
    excluded_patterns: list[str] = field(default_factory=list)
    per_file_ignores: dict[str, set[str]]= field(
        default_factory=dict
    )
    rule_overrides: dict[str, dict] = field(
        default_factory=dict
    )

    def is_excluded(self, file_path: Path) -> bool:
        """Return True when the file matches an excluded pattern."""

        relative_path = get_relative_path(
            file_path=file_path,
            project_root=self.root,
        )

        return any(
            fnmatch(relative_path, pattern)
            for pattern in self.excluded_patterns
        )

    def ignored_rules_for_file(
        self,
        file_path: Path,
    ) -> set[str]:
        """Return rules ignored globally and for this file."""

        ignored_rules = set(self.ignored_rules)

        relative_path = get_relative_path(
            file_path=file_path,
            project_root=self.root,
        )

        for pattern, rule_ids in self.per_file_ignores.items():
            if fnmatch(relative_path, pattern):
                ignored_rules.update(rule_ids)

        return ignored_rules
    
    def is_rule_enabled(
        self,
        rule_id: str,
    ) -> bool:
        rule_config = self.rule_overrides.get(
            rule_id,
            {},
        )

        return rule_config.get(
         "enabled",
         True,
        )


    def get_rule_severity(
        self,
        rule_id: str,
        default: str,
    ) -> str:
        rule_config = self.rule_overrides.get(
            rule_id,
            {},
        )

        severity = rule_config.get(
            "severity",
            default,
        )

        if severity not in {
            "LOW",
         "MEDIUM",
            "HIGH",
        }:
            return default

        return severity


def get_relative_path(
    file_path: Path,
    project_root: Path,
) -> str:
    """Return a normalized path relative to the configuration root."""

    resolved_file = file_path.expanduser().resolve()
    resolved_root = project_root.expanduser().resolve()

    try:
        return resolved_file.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_file.as_posix()


def find_config(start_path: Path) -> Path | None:
    """Search for .fabriclint.toml in the current or parent folders."""

    resolved_path = start_path.expanduser().resolve()

    current_directory = (
        resolved_path
        if resolved_path.is_dir()
        else resolved_path.parent
    )

    for directory in (
        current_directory,
        *current_directory.parents,
    ):
        config_path = directory / CONFIG_FILE_NAME

        if config_path.is_file():
            return config_path

    return None


def normalize_rules(values: object) -> set[str]:
    """Normalize a TOML list of rule identifiers."""

    if not isinstance(values, list):
        return set()

    return {
        str(value).strip().upper()
        for value in values
        if str(value).strip()
    }

def load_config(start_path: Path) -> FabricLintConfig:
    """Load the nearest FabricLint configuration file."""

    resolved_start_path = start_path.expanduser().resolve()
    config_path = find_config(resolved_start_path)

    if config_path is None:
        default_root = (
            resolved_start_path
            if resolved_start_path.is_dir()
            else resolved_start_path.parent
        )

        return FabricLintConfig(root=default_root)

    with config_path.open("rb") as config_file:
        data = tomllib.load(config_file)

    fabriclint_section = (
        data
        .get("tool", {})
        .get("fabriclint", {})
    )

    # ---------------------------------------------
    # Global ignored rules
    # ---------------------------------------------
    ignored_rules = normalize_rules(
        fabriclint_section.get("ignore", [])
    )

    # ---------------------------------------------
    # Excluded paths
    # ---------------------------------------------
    excluded_patterns = [
        str(pattern)
        for pattern in fabriclint_section.get(
            "exclude",
            [],
        )
    ]

    # ---------------------------------------------
    # Per-file ignores
    # ---------------------------------------------
    raw_per_file_ignores = fabriclint_section.get(
        "per-file-ignores",
        {},
    )

    per_file_ignores = {
        str(pattern): normalize_rules(rule_ids)
        for pattern, rule_ids
        in raw_per_file_ignores.items()
    }

    # ---------------------------------------------
    # Rule-level configuration
    # ---------------------------------------------
    raw_rule_overrides = fabriclint_section.get(
        "rules",
        {},
    )

    if not isinstance(raw_rule_overrides, dict):
        raw_rule_overrides = {}

    rule_overrides = {
        str(rule_id).upper(): settings
        for rule_id, settings in raw_rule_overrides.items()
        if isinstance(settings, dict)
    }

    return FabricLintConfig(
        root=config_path.parent.resolve(),
        ignored_rules=ignored_rules,
        excluded_patterns=excluded_patterns,
        per_file_ignores=per_file_ignores,
        rule_overrides=rule_overrides,
    )

def apply_rule_overrides(
    findings: list[Finding],
    config: FabricLintConfig,
) -> list[Finding]:

    result: list[Finding] = []

    for finding in findings:

        # Rule disabled
        if not config.is_rule_enabled(
            finding.rule_id
        ):
            continue

        severity = config.get_rule_severity(
            finding.rule_id,
            finding.severity,
        )

        # Finding is frozen, so create
        # a modified copy.
        if severity != finding.severity:
            finding = replace(
                finding,
                severity=severity,
            )

        result.append(finding)

    return result