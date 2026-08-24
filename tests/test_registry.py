from fabriclint.rules.registry import RULES


def test_rule_registry_contains_expected_rules():
    expected_rules = {
        "FL001",
        "FL002",
        "FL003",
        "FL004",
        "FL005",
        "FL100",
        "FL101",
        "FL102",
        "FL103",
        "FL104",
        "FL105",
        "FL106",
        "FL107",
        "FL108",
        "FL109",
        "FL110",
        "FL111",
        "FL200",
        "FL201",
        "FL202",
        "FL203",
        "FL204",
        "FL205",
        "FL206",
    }

    assert expected_rules.issubset(RULES.keys())

def test_every_registered_rule_has_required_fields():
    for rule_id, rule in RULES.items():

        assert rule_id.startswith("FL")

        assert rule["severity"] in {
            "LOW",
            "MEDIUM",
            "HIGH",
        }

        assert rule["description"]
        assert rule["category"]
