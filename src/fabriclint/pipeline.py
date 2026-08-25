import json
from pathlib import Path
import re
from fabriclint.items import FabricItem
from fabriclint.models import Finding

from fabriclint.rules.pipeline_rules import (
    check_dependencies,
    check_empty_pipeline,
    check_hardcoded_guids,
    check_retry_policies,
    create_pipeline_finding,
    validate_dependency_scope,
    get_child_activity_scopes,
    check_duplicate_activity_names,
)

PIPELINE_FILE = "pipeline-content.json"
GUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\b"
)

RETRY_REVIEW_ACTIVITY_TYPES = {
    "Copy",
    "TridentNotebook",
    "DatabricksNotebook",
    "SparkJobDefinition",
    "ExecutePipeline",
    "WebActivity",
    "Lookup",
    "GetMetadata",
    "AzureFunction",
    "RefreshDataFlow",
    "PBISemanticModelRefresh",
}

def get_nested_activities(
    activity: dict,
) -> list[dict]:
    """Return activities nested inside a control activity."""

    nested: list[dict] = []

    activity_type = activity.get("type")
    type_properties = activity.get("typeProperties", {})

    if not isinstance(type_properties, dict):
        return nested

    # ForEach and Until
    if activity_type in {"ForEach", "Until"}:
        child_activities = type_properties.get(
            "activities",
            [],
        )

        if isinstance(child_activities, list):
            nested.extend(child_activities)

    # IfCondition
    elif activity_type == "IfCondition":

        true_activities = type_properties.get(
            "ifTrueActivities",
            [],
        )

        false_activities = type_properties.get(
            "ifFalseActivities",
            [],
        )

        if isinstance(true_activities, list):
            nested.extend(true_activities)

        if isinstance(false_activities, list):
            nested.extend(false_activities)

    # Switch
    elif activity_type == "Switch":

        default_activities = type_properties.get(
            "defaultActivities",
            [],
        )

        if isinstance(default_activities, list):
            nested.extend(default_activities)

        cases = type_properties.get(
            "cases",
            [],
        )

        if isinstance(cases, list):

            for case in cases:

                if not isinstance(case, dict):
                    continue

                case_activities = case.get(
                    "activities",
                    [],
                )

                if isinstance(case_activities, list):
                    nested.extend(case_activities)

    return nested

def iter_all_activities(
    activities: list,
):
    """Yield top-level and nested pipeline activities."""

    for activity in activities:

        if not isinstance(activity, dict):
            continue

        # Current activity
        yield activity

        # Activities inside this activity
        nested = get_nested_activities(activity)

        # Recursively inspect them
        yield from iter_all_activities(nested)




def validate_dependencies_recursive(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:
    """Validate dependencies in this scope and nested scopes."""

    findings: list[Finding] = []

    # Validate current scope
    findings.extend(
        validate_dependency_scope(
            activities,
            pipeline_path,
        )
    )

    # Validate child scopes
    for activity in activities:

        if not isinstance(activity, dict):
            continue

        child_scopes = get_child_activity_scopes(
            activity
        )

        for child_scope in child_scopes:
            findings.extend(
                validate_dependencies_recursive(
                    child_scope,
                    pipeline_path,
                )
            )

    return findings



def validate_pipeline(
    item: FabricItem,
) -> list[Finding]:
    """Validate a DataPipeline item."""

    if item.item_type != "DataPipeline":
        return []

    pipeline_path = item.path / PIPELINE_FILE

    # FL200
    if not pipeline_path.is_file():
        return [
            create_pipeline_finding(
                rule_id="FL200",
                severity="HIGH",
                message="Missing pipeline-content.json.",
                suggestion=(
                    "Restore the Fabric Data Pipeline "
                    "definition file."
                ),
                file_path=pipeline_path,
            )
        ]

    # FL201
    try:
        data = json.loads(
            pipeline_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:
        return [
            create_pipeline_finding(
                rule_id="FL201",
                severity="HIGH",
                message=(
                    "Invalid JSON in pipeline-content.json."
                ),
                suggestion=(
                    "Fix the pipeline JSON syntax "
                    "before deployment."
                ),
                file_path=pipeline_path,
                line_number=exc.lineno,
            )
        ]

    activities = data.get(
        "properties",
        {},
    ).get(
        "activities",
        [],
    )

    findings: list[Finding] = []

    findings.extend(
        check_empty_pipeline(
            activities,
            pipeline_path,
        )
    )

    findings.extend(
        check_hardcoded_guids(
            data,
            pipeline_path,
        )
    )

    findings.extend(
        check_retry_policies(
            activities,
            pipeline_path,
        )
    )

    findings.extend(
        check_dependencies(
            activities,
            pipeline_path,
        )
    )

    findings.extend(
        check_duplicate_activity_names(
            activities,
            pipeline_path,
        )
    )

    return findings


