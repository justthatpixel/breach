"""One-off generator for evals/judge/cases.jsonl — not part of the
shipped eval suite, kept here so the dataset's construction is
reproducible/auditable rather than hand-typed JSON."""
import json
from pathlib import Path

# component_type -> candidate mitigation ids, i.e. the union of
# mitigations that actually mitigate (per real ATT&CK relationships.json)
# at least one of that type's techniques (data/attack/game_map.yaml).
CANDIDATES = {
    "api_gateway": ["M1018", "M1026", "M1030", "M1032", "M1035", "M1036", "M1037", "M1050"],
    "container": ["M1018", "M1035", "M1037"],
    "database": ["M1018", "M1026", "M1032", "M1036"],
    "object_store": ["M1018", "M1026", "M1032", "M1036", "M1037", "M1041"],
    "secrets": ["M1018", "M1026", "M1032", "M1036"],
}

# Two concrete, specific sentences per mitigation — kept close to the
# mitigation's own name/description wording so retrieval (even the crude
# bag-of-words test embedder) can surface the right candidate.
PHRASES = {
    "M1018": [
        "We deactivate service accounts immediately once they're no longer needed and review every account's permissions quarterly.",
        "Account creation goes through an approval step, and we remove access the same day someone leaves the team.",
    ],
    "M1026": [
        "Admin and service accounts only get the specific permissions their job needs, nothing more — least privilege for every privileged account.",
        "Privileged accounts are reviewed separately from regular users and require a documented business justification.",
    ],
    "M1030": [
        "The gateway sits in its own isolated network segment, with no direct route from it to internal systems.",
        "We segment the network so a compromised edge service can't reach anything else directly.",
    ],
    "M1032": [
        "Every login requires a second factor, so a stolen password alone can't get in.",
        "We enforce multi-factor authentication on every account with access to this component.",
    ],
    "M1035": [
        "Only our own internal services can reach this over the network; nothing else has a legitimate route to it.",
        "We restrict network access to this resource to a short allow-list of known callers.",
    ],
    "M1036": [
        "Accounts lock out after five failed login attempts and sessions expire after 15 minutes of inactivity.",
        "We enforce a strict password rotation and lockout policy on every account here.",
    ],
    "M1037": [
        "We run a firewall that filters all inbound and outbound traffic, blocking anything that doesn't match an allowed rule.",
        "A network filter inspects every request and drops traffic that doesn't match our allow-list.",
    ],
    "M1041": [
        "All data is encrypted at rest with envelope encryption and in transit with TLS.",
        "Everything stored here is encrypted using strong, industry-standard algorithms.",
    ],
    "M1050": [
        "We deploy a WAF that detects and blocks common exploitation attempts against known vulnerabilities.",
        "Exploit protection in front of this service blocks known attack patterns before they reach the app.",
    ],
}

# A real, specific measure that is NOT a true candidate for this
# component type's techniques (per the same relationships.json) — the
# "right idea, wrong mitigation" case HANDOFF §8.1 asks for, and the same
# teaching moment as the M2 golden test (encryption doesn't stop valid
# credentials, M1041 isn't a candidate for database/secrets).
WRONG_MITIGATION_CLAIM = {
    "api_gateway": ("M1041", "All traffic through the gateway is encrypted with TLS, and the card data behind it is encrypted at rest."),
    "container": ("M1032", "Every login to the container's admin panel requires multi-factor authentication."),
    "database": ("M1041", "All the card data in this database is encrypted at rest with AES-256."),
    "object_store": ("M1050", "We run a WAF in front of the object store to block exploitation attempts."),
    "secrets": ("M1041", "Everything in the secrets store is encrypted at rest."),
}

VAGUE_NOTES = [
    "We made sure everything is secure and locked down properly.",
    "This component is well protected and follows best practices.",
    "Secured it, nothing to worry about here.",
]

WRONG_BUT_CONFIDENT_NOTES = [
    "We follow industry-standard zero-trust security best practices and have a robust defense-in-depth posture.",
    "This is enterprise-grade, bank-level security with military-grade protection end to end.",
    "Our security posture here is extremely mature and battle-tested against sophisticated adversaries.",
]


def build_cases() -> list[dict]:
    cases: list[dict] = []
    vague_i = 0
    confident_i = 0

    for component_type, candidates in CANDIDATES.items():
        for mitigation_id in candidates:
            for phrase in PHRASES[mitigation_id]:
                cases.append(
                    {
                        "component_type": component_type,
                        "notes": phrase,
                        "expected_credited": [mitigation_id],
                        "notes_on_label": f"easy: specifically describes {mitigation_id}",
                    }
                )

        # hard: two different real, relevant mitigations in one note.
        if len(candidates) >= 2:
            first, second = candidates[0], candidates[1]
            cases.append(
                {
                    "component_type": component_type,
                    "notes": f"{PHRASES[first][0]} On top of that, {PHRASES[second][1][0].lower()}{PHRASES[second][1][1:]}",
                    "expected_credited": sorted([first, second]),
                    "notes_on_label": f"hard: two distinct measures ({first}, {second}) in one note",
                }
            )

        cases.append(
            {
                "component_type": component_type,
                "notes": VAGUE_NOTES[vague_i % len(VAGUE_NOTES)],
                "expected_credited": [],
                "notes_on_label": "vague: no concrete measure named, should credit nothing",
            }
        )
        vague_i += 1

        cases.append(
            {
                "component_type": component_type,
                "notes": WRONG_BUT_CONFIDENT_NOTES[confident_i % len(WRONG_BUT_CONFIDENT_NOTES)],
                "expected_credited": [],
                "notes_on_label": "wrong-but-confident: buzzwords, no verifiable specific measure",
            }
        )
        confident_i += 1

        wrong_mitigation_id, wrong_note = WRONG_MITIGATION_CLAIM[component_type]
        cases.append(
            {
                "component_type": component_type,
                "notes": wrong_note,
                "expected_credited": [],
                "notes_on_label": (
                    f"right idea, wrong mitigation: {wrong_mitigation_id} is real and specific but "
                    f"doesn't actually mitigate any technique {component_type} faces"
                ),
            }
        )

    return cases


def main() -> None:
    cases = build_cases()
    out_path = Path(__file__).parent / "cases.jsonl"
    with out_path.open("w") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")
    print(f"Wrote {len(cases)} cases to {out_path}")


if __name__ == "__main__":
    main()
