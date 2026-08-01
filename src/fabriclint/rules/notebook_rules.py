import re

from .base import RegexRule


RULES: tuple[RegexRule, ...] = (
    RegexRule(
        rule_id="FL001",
        severity="HIGH",
        pattern=re.compile(
            r"""
            \b(password|client_secret|api[_-]?key|access[_-]?token)\b
            \s*=\s*
            ["'][^"']{4,}["']
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        message="Possible hard-coded credential detected.",
        suggestion=(
            "Store credentials in a secure secret store or environment "
            "configuration instead of notebook source code."
        ),
    ),
    RegexRule(
        rule_id="FL002",
        severity="MEDIUM",
        pattern=re.compile(
            r"\b[0-9a-fA-F]{8}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{12}\b"
        ),
        message="Hard-coded GUID or Fabric identifier detected.",
        suggestion=(
            "Move workspace, Lakehouse and item identifiers into "
            "environment-specific configuration."
        ),
    ),
    RegexRule(
        rule_id="FL003",
        severity="MEDIUM",
        pattern=re.compile(r"\.(collect|toPandas)\s*\("),
        message="Operation may move excessive data to the Spark driver.",
        suggestion=(
            "Prefer distributed Spark transformations or limit the "
            "amount of data before collecting it."
        ),
    ),
    RegexRule(
        rule_id="FL004",
        severity="MEDIUM",
        pattern=re.compile(r"\.(repartition|coalesce)\s*\(\s*1\s*\)"),
        message="Single-partition operation may create a bottleneck.",
        suggestion=(
            "Keep multiple partitions unless a single output partition "
            "is explicitly required."
        ),
    ),
    RegexRule(
        rule_id="FL005",
        severity="MEDIUM",
        pattern=re.compile(
            r"""\.mode\s*\(\s*["']overwrite["']\s*\)""",
            re.IGNORECASE,
        ),
        message="Full overwrite operation detected.",
        suggestion=(
            "Verify idempotency, recovery requirements and whether "
            "MERGE or partition replacement would be safer."
        ),
    ),
)
