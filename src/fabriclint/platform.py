import json
from pathlib import Path
from uuid import UUID

from fabriclint.items import FabricItem
from fabriclint.models import Finding


PLATFORM_FILE = ".platform"
V1_METADATA_FILE = "item.metadata.json"
V1_CONFIG_FILE = "item.config.json"


def create_finding(
    rule_id: str,
    severity: str,
    message: str,
    suggestion: str,
    file_path: Path,
    line_number: int = 1,
) -> Finding:
    """Create a FabricLint finding."""

    return Finding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        suggestion=suggestion,
        file_path=file_path,
        line_number=line_number,
    )


def is_valid_uuid(value: object) -> bool:
    """Return True when the supplied value is a valid UUID."""

    if not isinstance(value, str):
        return False

    try:
        UUID(value)
        return True
    except ValueError:
        return False


def validate_platform_file(
    item: FabricItem,
    platform_path: Path,
) -> list[Finding]:
    """Validate a Fabric V2 .platform file."""

    findings: list[Finding] = []

    # ---------------------------------------------------------
    # FL103 - Invalid JSON
    # ---------------------------------------------------------
    try:
        data = json.loads(
            platform_path.read_text(encoding="utf-8")
        )

    except json.JSONDecodeError as exc:
        return [
            create_finding(
                rule_id="FL103",
                severity="HIGH",
                message="Invalid JSON in .platform file.",
                suggestion=(
                    "Fix the JSON syntax before syncing "
                    "or deploying this Fabric item."
                ),
                file_path=platform_path,
                line_number=exc.lineno,
            )
        ]

    # .platform must contain a JSON object
    if not isinstance(data, dict):
        return [
            create_finding(
                rule_id="FL103",
                severity="HIGH",
                message=".platform must contain a JSON object.",
                suggestion=(
                    "Replace the file content with a valid "
                    "Fabric platform metadata object."
                ),
                file_path=platform_path,
            )
        ]

    # ---------------------------------------------------------
    # FL104 - Invalid or missing version
    # ---------------------------------------------------------
    version = data.get("version")

    if version != "2.0":
        findings.append(
            create_finding(
                rule_id="FL104",
                severity="HIGH",
                message=(
                    "Missing or unsupported .platform version."
                ),
                suggestion=(
                    'Fabric V2 platform metadata should use '
                    '"version": "2.0".'
                ),
                file_path=platform_path,
            )
        )

    # ---------------------------------------------------------
    # FL105 - Missing schema
    # ---------------------------------------------------------
    schema = data.get("$schema")

    if not isinstance(schema, str) or not schema.strip():
        findings.append(
            create_finding(
                rule_id="FL105",
                severity="LOW",
                message="Missing $schema in .platform file.",
                suggestion=(
                    "Include the Fabric platform properties "
                    "schema reference."
                ),
                file_path=platform_path,
            )
        )

    # ---------------------------------------------------------
    # FL106 / FL107 - Config and logicalId
    # ---------------------------------------------------------
    config = data.get("config")

    if not isinstance(config, dict):
        findings.append(
            create_finding(
                rule_id="FL106",
                severity="HIGH",
                message="Missing config object in .platform.",
                suggestion=(
                    "Restore the Fabric-generated config metadata."
                ),
                file_path=platform_path,
            )
        )

    else:
        logical_id = config.get("logicalId")

        if not is_valid_uuid(logical_id):
            findings.append(
                create_finding(
                    rule_id="FL107",
                    severity="HIGH",
                    message=(
                        "Missing or invalid Fabric logicalId."
                    ),
                    suggestion=(
                        "Restore the Fabric-generated logicalId."
                    ),
                    file_path=platform_path,
                )
            )

    # ---------------------------------------------------------
    # FL108 - Missing metadata
    # ---------------------------------------------------------
    metadata = data.get("metadata")

    if not isinstance(metadata, dict):
        findings.append(
            create_finding(
                rule_id="FL108",
                severity="HIGH",
                message="Missing metadata object in .platform.",
                suggestion=(
                    "Restore the Fabric-generated item metadata."
                ),
                file_path=platform_path,
            )
        )

        # No point checking type/displayName when metadata
        # does not exist.
        return findings

    # ---------------------------------------------------------
    # FL109 - Missing item type
    # FL111 - Item type mismatch
    # ---------------------------------------------------------
    metadata_type = metadata.get("type")

    if (
        not isinstance(metadata_type, str)
        or not metadata_type.strip()
    ):
        findings.append(
            create_finding(
                rule_id="FL109",
                severity="HIGH",
                message=(
                    "Missing item type in .platform metadata."
                ),
                suggestion=(
                    "Restore the Fabric-generated metadata.type."
                ),
                file_path=platform_path,
            )
        )

    elif metadata_type.lower() != item.item_type.lower():
        findings.append(
            create_finding(
                rule_id="FL111",
                severity="HIGH",
                message=(
                    "Platform metadata type does not match "
                    "the Fabric item folder type."
                ),
                suggestion=(
                    f"Expected metadata.type to be "
                    f"'{item.item_type}', but found "
                    f"'{metadata_type}'."
                ),
                file_path=platform_path,
            )
        )

    # ---------------------------------------------------------
    # FL110 - Missing displayName
    # ---------------------------------------------------------
    display_name = metadata.get("displayName")

    if (
        not isinstance(display_name, str)
        or not display_name.strip()
    ):
        findings.append(
            create_finding(
                rule_id="FL110",
                severity="HIGH",
                message=(
                    "Missing displayName in .platform metadata."
                ),
                suggestion=(
                    "Provide a valid Fabric item display name."
                ),
                file_path=platform_path,
            )
        )

    return findings


def validate_item_system_metadata(
    item: FabricItem,
) -> list[Finding]:
    """
    Validate Fabric system metadata.

    Supported formats:

    V2:
        .platform

    V1:
        item.metadata.json
        item.config.json
    """

    platform_path = item.path / PLATFORM_FILE
    metadata_path = item.path / V1_METADATA_FILE
    config_path = item.path / V1_CONFIG_FILE

    has_platform = platform_path.is_file()
    has_metadata = metadata_path.is_file()
    has_config = config_path.is_file()

    # ---------------------------------------------------------
    # FL101 - V1 and V2 metadata mixed together
    # ---------------------------------------------------------
    if has_platform and (has_metadata or has_config):
        return [
            create_finding(
                rule_id="FL101",
                severity="HIGH",
                message=(
                    ".platform cannot coexist with Fabric V1 "
                    "system metadata files."
                ),
                suggestion=(
                    "Use either .platform or the V1 "
                    "item.metadata.json/item.config.json pair."
                ),
                file_path=platform_path,
            )
        ]

    # ---------------------------------------------------------
    # Fabric V2
    # ---------------------------------------------------------
    if has_platform:
        return validate_platform_file(
            item=item,
            platform_path=platform_path,
        )

    # ---------------------------------------------------------
    # Valid Fabric V1
    # ---------------------------------------------------------
    if has_metadata and has_config:
        return []

    # ---------------------------------------------------------
    # FL102 - Incomplete Fabric V1 metadata
    # ---------------------------------------------------------
    if has_metadata or has_config:
        return [
            create_finding(
                rule_id="FL102",
                severity="HIGH",
                message=(
                    "Incomplete Fabric V1 system metadata."
                ),
                suggestion=(
                    "Both item.metadata.json and "
                    "item.config.json are required for V1."
                ),
                file_path=item.path,
            )
        ]

    # ---------------------------------------------------------
    # FL100 - No system metadata
    # ---------------------------------------------------------
    return [
        create_finding(
            rule_id="FL100",
            severity="HIGH",
            message="Fabric system metadata is missing.",
            suggestion=(
                "Restore the .platform file, or the complete "
                "V1 metadata/config pair."
            ),
            file_path=platform_path,
        )
    ]