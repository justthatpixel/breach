#!/usr/bin/env python3
"""Download the MITRE Enterprise ATT&CK STIX bundle and write a curated subset.

Writes data/attack/techniques.json, mitigations.json and relationships.json,
restricted to the technique and mitigation IDs this game uses (see
data/attack/wanted_ids.yaml). Fails loudly if a wanted ID is missing or its
name doesn't match what's expected, instead of guessing.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import yaml

STIX_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "attack"
WANTED_IDS_FILE = DATA_DIR / "wanted_ids.yaml"


def attack_id_of(obj: dict) -> str | None:
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def fetch_bundle(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read())


def load_bundle(path: Path | None) -> dict:
    if path is not None:
        return json.loads(path.read_text())
    return fetch_bundle(STIX_URL)


def tactics_of(obj: dict) -> list[str]:
    return sorted(
        phase["phase_name"]
        for phase in obj.get("kill_chain_phases", [])
        if phase.get("kill_chain_name") == "mitre-attack"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-file",
        type=Path,
        default=None,
        help="Use a local STIX bundle JSON instead of downloading it",
    )
    args = parser.parse_args()

    wanted = yaml.safe_load(WANTED_IDS_FILE.read_text())
    wanted_techniques: dict[str, str] = wanted["techniques"]
    wanted_mitigations: dict[str, str] = wanted["mitigations"]

    bundle = load_bundle(args.bundle_file)
    objects = bundle["objects"]

    # MITRE's display convention for a sub-technique is "Parent: Sub", but the
    # STIX object's own "name" field holds only the "Sub" part. The parent is
    # found via a "subtechnique-of" relationship, so attack-patterns and that
    # relationship must be indexed before technique names can be finalised.
    attack_patterns_by_stix_id: dict[str, dict] = {}
    stix_id_to_attack_id: dict[str, str] = {}
    for obj in objects:
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        attack_id = attack_id_of(obj)
        if attack_id is None:
            continue
        stix_id_to_attack_id[obj["id"]] = attack_id
        if obj["type"] == "attack-pattern":
            attack_patterns_by_stix_id[obj["id"]] = obj

    subtechnique_parent_stix_id: dict[str, str] = {}
    for obj in objects:
        if obj.get("type") == "relationship" and obj.get("relationship_type") == "subtechnique-of":
            subtechnique_parent_stix_id[obj["source_ref"]] = obj["target_ref"]

    def display_name(stix_id: str, obj: dict) -> str:
        parent_stix_id = subtechnique_parent_stix_id.get(stix_id)
        if parent_stix_id is None:
            return obj["name"]
        parent = attack_patterns_by_stix_id.get(parent_stix_id)
        if parent is None:
            return obj["name"]
        return f"{parent['name']}: {obj['name']}"

    techniques_by_id: dict[str, dict] = {}
    mitigations_by_id: dict[str, dict] = {}

    for stix_id, obj in attack_patterns_by_stix_id.items():
        attack_id = stix_id_to_attack_id[stix_id]
        if attack_id in wanted_techniques:
            techniques_by_id[attack_id] = {
                "id": attack_id,
                "name": display_name(stix_id, obj),
                "description": obj.get("description", ""),
                "platforms": sorted(obj.get("x_mitre_platforms", [])),
                "tactics": tactics_of(obj),
            }

    for obj in objects:
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        attack_id = attack_id_of(obj)
        if attack_id is None:
            continue
        if obj["type"] == "course-of-action" and attack_id in wanted_mitigations:
            mitigations_by_id[attack_id] = {
                "id": attack_id,
                "name": obj["name"],
                "description": obj.get("description", ""),
            }

    errors = []
    for attack_id, expected_name in wanted_techniques.items():
        found = techniques_by_id.get(attack_id)
        if found is None:
            errors.append(f"technique {attack_id} not found in ATT&CK data")
        elif found["name"] != expected_name:
            errors.append(
                f"technique {attack_id} name mismatch: "
                f"spec says {expected_name!r}, ATT&CK says {found['name']!r}"
            )
    for attack_id, expected_name in wanted_mitigations.items():
        found = mitigations_by_id.get(attack_id)
        if found is None:
            errors.append(f"mitigation {attack_id} not found in ATT&CK data")
        elif found["name"] != expected_name:
            errors.append(
                f"mitigation {attack_id} name mismatch: "
                f"spec says {expected_name!r}, ATT&CK says {found['name']!r}"
            )

    if errors:
        print("ATT&CK ID validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    relationships = []
    seen = set()
    for obj in objects:
        if obj.get("type") != "relationship" or obj.get("relationship_type") != "mitigates":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        mitigation_id = stix_id_to_attack_id.get(obj["source_ref"])
        technique_id = stix_id_to_attack_id.get(obj["target_ref"])
        if mitigation_id in wanted_mitigations and technique_id in wanted_techniques:
            key = (mitigation_id, technique_id)
            if key not in seen:
                seen.add(key)
                relationships.append({"mitigation_id": mitigation_id, "technique_id": technique_id})

    relationships.sort(key=lambda r: (r["mitigation_id"], r["technique_id"]))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "techniques.json").write_text(
        json.dumps([techniques_by_id[k] for k in sorted(techniques_by_id)], indent=2) + "\n"
    )
    (DATA_DIR / "mitigations.json").write_text(
        json.dumps([mitigations_by_id[k] for k in sorted(mitigations_by_id)], indent=2) + "\n"
    )
    (DATA_DIR / "relationships.json").write_text(json.dumps(relationships, indent=2) + "\n")

    print(f"Wrote {len(techniques_by_id)} techniques, {len(mitigations_by_id)} mitigations, "
          f"{len(relationships)} mitigates-relationships to {DATA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
