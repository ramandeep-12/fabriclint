import json
from pathlib import Path

from fabriclint.items import FabricItem
from fabriclint.pipeline import validate_pipeline


def make_pipeline(tmp_path: Path) -> FabricItem:
    pipeline_path = tmp_path / "CustomerLoad.DataPipeline"
    pipeline_path.mkdir()

    return FabricItem(
        name="CustomerLoad",
        item_type="DataPipeline",
        path=pipeline_path,
    )


def test_missing_pipeline_content_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL200"
        for finding in findings
    )


def test_invalid_pipeline_json_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    (
        item.path / "pipeline-content.json"
    ).write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL201"
        for finding in findings
    )


def test_empty_pipeline_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": []
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL202"
        for finding in findings
    )


def test_pipeline_with_activity_passes(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                        "retryIntervalInSeconds": 30
                    }
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert findings == []

def test_hard_coded_guid_is_reported(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "RunNotebook",
                    "type": "TridentNotebook",
                    "typeProperties": {
                        "workspaceId": (
                            "12345678-1234-1234-1234-123456789012"
                        )
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL203"
        for finding in findings
    )

def test_pipeline_without_guid_does_not_report_fl203(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL203"
        for finding in findings
    )

def test_activity_without_retry_reports_fl204(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL204"
        for finding in findings
    )
def test_activity_with_retry_does_not_report_fl204(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                        "retryIntervalInSeconds": 30,
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL204"
        for finding in findings
    )

def test_control_activity_does_not_report_fl204(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CheckCondition",
                    "type": "IfCondition",
                    "typeProperties": {},
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL204"
        for finding in findings
    )

def test_nested_foreach_activity_reports_fl204(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "ProcessCustomers",
                    "type": "ForEach",
                    "typeProperties": {
                        "items": {
                            "value": "@pipeline().parameters.customers",
                            "type": "Expression",
                        },
                        "activities": [
                            {
                                "name": "CopyCustomer",
                                "type": "Copy",
                            }
                        ],
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    fl204_findings = [
        finding
        for finding in findings
        if finding.rule_id == "FL204"
    ]

    assert len(fl204_findings) == 1

    assert "CopyCustomer" in fl204_findings[0].message

def test_nested_foreach_activity_with_retry_passes(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "ProcessCustomers",
                    "type": "ForEach",
                    "typeProperties": {
                        "activities": [
                            {
                                "name": "CopyCustomer",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                    "retryIntervalInSeconds": 30,
                                },
                            }
                        ]
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL204"
        for finding in findings
    )

def test_nested_if_condition_activity_reports_fl204(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CheckCustomer",
                    "type": "IfCondition",
                    "typeProperties": {
                        "expression": {
                            "value": "@equals(1, 1)",
                            "type": "Expression",
                        },
                        "ifTrueActivities": [
                            {
                                "name": "CopyCustomers",
                                "type": "Copy",
                            }
                        ],
                        "ifFalseActivities": [],
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL204"
        and "CopyCustomers" in finding.message
        for finding in findings
    )
def test_broken_dependency_reports_fl205(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "LoadBronze",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
                {
                    "name": "LoadSilver",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                    "dependsOn": [
                        {
                            "activity": "MissingActivity",
                            "dependencyConditions": [
                                "Succeeded",
                            ],
                        }
                    ],
                },
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL205"
        for finding in findings
    )

def test_valid_dependency_does_not_report_fl205(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "LoadBronze",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
                {
                    "name": "LoadSilver",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                    "dependsOn": [
                        {
                            "activity": "LoadBronze",
                            "dependencyConditions": [
                                "Succeeded",
                            ],
                        }
                    ],
                },
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL205"
        for finding in findings
    )

def test_nested_broken_dependency_reports_fl205(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "ProcessCustomers",
                    "type": "ForEach",
                    "typeProperties": {
                        "activities": [
                            {
                                "name": "CopyBronze",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                            },
                            {
                                "name": "CopySilver",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                                "dependsOn": [
                                    {
                                        "activity": "MissingActivity",
                                        "dependencyConditions": [
                                            "Succeeded",
                                        ],
                                    }
                                ],
                            },
                        ]
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL205"
        and "MissingActivity" in finding.message
        for finding in findings
    )

def test_nested_valid_dependency_does_not_report_fl205(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "ProcessCustomers",
                    "type": "ForEach",
                    "typeProperties": {
                        "activities": [
                            {
                                "name": "CopyBronze",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                            },
                            {
                                "name": "CopySilver",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                                "dependsOn": [
                                    {
                                        "activity": "CopyBronze",
                                        "dependencyConditions": [
                                            "Succeeded",
                                        ],
                                    }
                                ],
                            },
                        ]
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL205"
        for finding in findings
    )
def test_if_condition_branches_are_separate_dependency_scopes(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CheckCustomer",
                    "type": "IfCondition",
                    "typeProperties": {
                        "ifTrueActivities": [
                            {
                                "name": "CopyTrue",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                            }
                        ],
                        "ifFalseActivities": [
                            {
                                "name": "CopyFalse",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                                "dependsOn": [
                                    {
                                        "activity": "CopyTrue",
                                        "dependencyConditions": [
                                            "Succeeded",
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL205"
        and "CopyTrue" in finding.message
        for finding in findings
    )


def test_duplicate_activity_names_report_fl206(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
                {
                    "name": "CopyCustomers",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL206"
        for finding in findings
    )

def test_unique_activity_names_do_not_report_fl206(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "CopyBronze",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
                {
                    "name": "CopySilver",
                    "type": "Copy",
                    "policy": {
                        "retry": 2,
                    },
                },
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert not any(
        finding.rule_id == "FL206"
        for finding in findings
    )

def test_nested_duplicate_activity_names_report_fl206(
    tmp_path: Path,
) -> None:
    item = make_pipeline(tmp_path)

    pipeline_data = {
        "properties": {
            "activities": [
                {
                    "name": "ProcessCustomers",
                    "type": "ForEach",
                    "typeProperties": {
                        "activities": [
                            {
                                "name": "CopyCustomer",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                            },
                            {
                                "name": "CopyCustomer",
                                "type": "Copy",
                                "policy": {
                                    "retry": 2,
                                },
                            },
                        ]
                    },
                }
            ]
        }
    }

    (
        item.path / "pipeline-content.json"
    ).write_text(
        json.dumps(pipeline_data),
        encoding="utf-8",
    )

    findings = validate_pipeline(item)

    assert any(
        finding.rule_id == "FL206"
        and "CopyCustomer" in finding.message
        for finding in findings
    )

