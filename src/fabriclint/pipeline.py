import json
from pathlib import Path
import re
from fabriclint.items import FabricItem
from fabriclint.models import Finding


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

def create_pipeline_finding(
    rule_id: str,
    severity: str,
    message: str,
    suggestion: str,
    file_path: Path,
    line_number: int = 1,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        suggestion=suggestion,
        file_path=file_path,
        line_number=line_number,
    )

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


def validate_dependency_scope(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:
    """Validate dependsOn references within one activity scope."""

    findings: list[Finding] = []

    valid_names = {
        activity.get("name")
        for activity in activities
        if isinstance(activity, dict)
        and isinstance(activity.get("name"), str)
    }

    for activity in activities:

        if not isinstance(activity, dict):
            continue

        activity_name = activity.get(
            "name",
            "<unnamed activity>",
        )

        dependencies = activity.get(
            "dependsOn",
            [],
        )

        if isinstance(dependencies, list):

            for dependency in dependencies:

                if not isinstance(dependency, dict):
                    continue

                referenced_activity = dependency.get(
                    "activity"
                )

                if (
                    isinstance(referenced_activity, str)
                    and referenced_activity not in valid_names
                ):
                    findings.append(
                        create_pipeline_finding(
                            rule_id="FL205",
                            severity="HIGH",
                            message=(
                                f"Activity '{activity_name}' depends "
                                f"on unknown activity "
                                f"'{referenced_activity}'."
                            ),
                            suggestion=(
                                "Update the dependsOn reference to "
                                "an existing activity or restore the "
                                "missing activity."
                            ),
                            file_path=pipeline_path,
                        )
                    )

    return findings

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

def get_child_activity_scopes(
    activity: dict,
) -> list[list]:
    """Return separate nested activity scopes."""

    scopes: list[list] = []

    activity_type = activity.get("type")
    type_properties = activity.get(
        "typeProperties",
        {},
    )

    if not isinstance(type_properties, dict):
        return scopes

    # ForEach / Until
    if activity_type in {"ForEach", "Until"}:
        child_activities = type_properties.get(
            "activities",
            [],
        )

        if isinstance(child_activities, list):
            scopes.append(child_activities)

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
            scopes.append(true_activities)

        if isinstance(false_activities, list):
            scopes.append(false_activities)

    # Switch
    elif activity_type == "Switch":

        default_activities = type_properties.get(
            "defaultActivities",
            [],
        )

        if isinstance(default_activities, list):
            scopes.append(default_activities)

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
                    scopes.append(case_activities)

    return scopes



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
                    "Restore the Fabric Data Pipeline definition file."
                ),
                file_path=pipeline_path,
            )
        ]

    # FL201
    try:
        data = json.loads(
            pipeline_path.read_text(encoding="utf-8")
        )

    except json.JSONDecodeError as exc:
        return [
            create_pipeline_finding(
                rule_id="FL201",
                severity="HIGH",
                message="Invalid JSON in pipeline-content.json.",
                suggestion=(
                    "Fix the pipeline JSON syntax before deployment."
                ),
                file_path=pipeline_path,
                line_number=exc.lineno,
            )
        ]

    findings: list[Finding] = []

    activities = data.get("properties", {}).get(
        "activities",
        [],
    )

    # FL202
    if not activities:
        findings.append(
            create_pipeline_finding(
                rule_id="FL202",
                severity="MEDIUM",
                message="Data Pipeline contains no activities.",
                suggestion=(
                    "Verify that the pipeline is intentionally empty."
                ),
                file_path=pipeline_path,
            )
        )

    # FL203
    pipeline_text = json.dumps(data)

    if GUID_PATTERN.search(pipeline_text):
        findings.append(
            create_pipeline_finding(
                rule_id="FL203",
                severity="MEDIUM",
                message=(
                    "Hard-coded GUID detected in Data Pipeline definition."
                ),
                suggestion=(
                    "Verify that workspace, item, connection, or "
                    "environment identifiers are parameterized before "
                    "deployment across environments."
                ),
                file_path=pipeline_path,
            )
        )

    # FL204
    for activity in iter_all_activities(activities):


        activity_type = activity.get("type")
        activity_name = activity.get(
            "name",
            "<unnamed activity>",
        )

        if activity_type not in RETRY_REVIEW_ACTIVITY_TYPES:
            continue

        policy = activity.get("policy")

        retry_count = 0

        if isinstance(policy, dict):
            retry_value = policy.get("retry", 0)

            if isinstance(retry_value, int):
                retry_count = retry_value

        if retry_count <= 0:
            findings.append(
                create_pipeline_finding(
                    rule_id="FL204",
                    severity="MEDIUM",
                    message=(
                        f"Activity '{activity_name}' has no "
                        "explicit retry attempts configured."
                    ),
                    suggestion=(
                        "Review whether this activity should use "
                        "a retry policy for transient failures. "
                        "Consider idempotency before enabling retries."
                    ),
                    file_path=pipeline_path,
                )
            )
    # --------------------------------------------------
    # FL205 - Broken activity dependency
    # --------------------------------------------------
    findings.extend(
        validate_dependencies_recursive(
            activities,
            pipeline_path,
        )
    )

    return findings


