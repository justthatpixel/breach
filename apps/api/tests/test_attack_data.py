def test_loads_all_curated_data(attack_data):
    assert len(attack_data.techniques) == 7
    assert len(attack_data.mitigations) == 9
    assert attack_data.mitigates  # at least one relationship


def test_known_technique_and_mitigation_ids(attack_data):
    assert "T1190" in attack_data.techniques
    assert attack_data.techniques["T1190"].name == "Exploit Public-Facing Application"
    assert "M1032" in attack_data.mitigations
    assert attack_data.mitigations["M1032"].name == "Multi-factor Authentication"


def test_subtechnique_names_include_parent(attack_data):
    assert attack_data.techniques["T1078.004"].name == "Valid Accounts: Cloud Accounts"
    assert (
        attack_data.techniques["T1552.005"].name
        == "Unsecured Credentials: Cloud Instance Metadata API"
    )


def test_encryption_does_not_mitigate_stolen_credentials(attack_data):
    """The Level 3 teaching moment: encryption at rest (M1041) does not stop
    an attacker using valid credentials (T1078.004)."""
    assert not attack_data.mitigates_technique("M1041", "T1078.004")
    assert attack_data.mitigates_technique("M1041", "T1530")


def test_loader_rejects_relationship_to_unknown_id(tmp_path):
    import json

    from breach.attack.loader import AttackDataError, load_attack_data

    (tmp_path / "techniques.json").write_text(
        json.dumps([{"id": "T1", "name": "x", "description": "", "platforms": [], "tactics": []}])
    )
    (tmp_path / "mitigations.json").write_text(
        json.dumps([{"id": "M1", "name": "x", "description": ""}])
    )
    (tmp_path / "relationships.json").write_text(
        json.dumps([{"mitigation_id": "M1", "technique_id": "T999"}])
    )

    try:
        load_attack_data(tmp_path)
        assert False, "expected AttackDataError"
    except AttackDataError:
        pass
