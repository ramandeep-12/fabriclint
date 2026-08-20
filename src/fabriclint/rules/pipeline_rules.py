import json
import re
from pathlib import Path

from fabriclint.models import Finding


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
    nested: list[dict] = []

    activity_type = activity.get("type")
    type_properties = activity.get(
        "typeProperties",
        {},
    )

    if not isinstance(type_properties, dict):
        return nested

    if activity_type in {"ForEach", "Until"}:
        children = type_properties.get(
            "activities",
            [],
        )

        if isinstance(children, list):
            nested.extend(children)

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

    elif activity_type == "Switch":
        default_activities = type_properties.get(
            "defaultActivities",
            [],
        )

        if isinstance(default_activities, list):
            nested.extend(default_activities)

        cases = type_properties.get("cases", [])

        if isinstance(cases, list):
            for case in cases:
                if not isinstance(case, dict):
                    continue

                activities = case.get(
                    "activities",
                    [],
                )

                if isinstance(activities, list):
                    nested.extend(activities)

    return nested


def iter_all_activities(
    activities: list,
):
    for activity in activities:

        if not isinstance(activity, dict):
            continue

        yield activity

        yield from iter_all_activities(
            get_nested_activities(activity)
        )

def check_duplicate_activity_names(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:
    """Detect duplicate activity names within each pipeline scope."""

    findings: list[Finding] = []

    names_seen: set[str] = set()

    for activity in activities:

        if not isinstance(activity, dict):
            continue

        activity_name = activity.get("name")

        if not isinstance(activity_name, str):
            continue

        if activity_name in names_seen:
            findings.append(
                create_pipeline_finding(
                    rule_id="FL206",
                    severity="HIGH",
                    message=(
                        f"Duplicate activity name "
                        f"'{activity_name}' detected."
                    ),
                    suggestion=(
                        "Rename activities so every activity "
                        "within the same pipeline scope has "
                        "a unique name."
                    ),
                    file_path=pipeline_path,
                )
            )

        else:
            names_seen.add(activity_name)

    # Check nested scopes separately
    for activity in activities:

        if not isinstance(activity, dict):
            continue

        for child_scope in get_child_activity_scopes(
            activity
        ):
            findings.extend(
                check_duplicate_activity_names(
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

def check_empty_pipeline(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:

    if activities:
        return []

    return [
        create_pipeline_finding(
            rule_id="FL202",
            severity="MEDIUM",
            message="Data Pipeline contains no activities.",
            suggestion=(
                "Verify that the pipeline is intentionally empty."
            ),
            file_path=pipeline_path,
        )
    ]

def check_hardcoded_guids(
    data: dict,
    pipeline_path: Path,
) -> list[Finding]:

    pipeline_text = json.dumps(data)

    if not GUID_PATTERN.search(pipeline_text):
        return []

    return [
        create_pipeline_finding(
            rule_id="FL203",
            severity="MEDIUM",
            message=(
                "Hard-coded GUID detected in "
                "Data Pipeline definition."
            ),
            suggestion=(
                "Verify that workspace, item, connection, or "
                "environment identifiers are parameterized "
                "before deployment across environments."
            ),
            file_path=pipeline_path,
        )
    ]

def check_retry_policies(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:

    findings: list[Finding] = []

    for activity in iter_all_activities(activities):

        activity_type = activity.get("type")

        if activity_type not in RETRY_REVIEW_ACTIVITY_TYPES:
            continue

        activity_name = activity.get(
            "name",
            "<unnamed activity>",
        )

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

    return findings

def check_dependencies(
    activities: list,
    pipeline_path: Path,
) -> list[Finding]:

    return validate_dependencies_recursive(
        activities,
        pipeline_path,
    )


