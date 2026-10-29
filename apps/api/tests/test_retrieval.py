"""Requires a running Postgres+pgvector (docker compose up -d db, then
breach.retrieval.migrate / seed / embed_mitigations with
EMBEDDING_PROVIDER=test). Skips itself if it can't connect, so the rest of
the suite stays runnable without Docker.
"""
import pytest

from breach.retrieval import DeterministicTestEmbedder, connect, retrieve_candidate_mitigations
from breach.retrieval.db import connect as db_connect
from breach.retrieval.embed_mitigations import embed_mitigations
from breach.retrieval.migrate import migrate
from breach.retrieval.seed import seed as seed_db

pytestmark = pytest.mark.retrieval


@pytest.fixture(scope="module")
def pg_ready():
    try:
        migrate()
    except Exception as exc:  # noqa: BLE001 - any connection/driver failure means "skip"
        pytest.skip(f"Postgres not reachable for retrieval tests: {exc}")
    seed_db()
    embed_mitigations(provider=DeterministicTestEmbedder())


@pytest.fixture
def conn(pg_ready):
    with db_connect() as c:
        yield c


@pytest.fixture
def provider():
    return DeterministicTestEmbedder()


KNOWN_CASES = [
    (
        "database",
        "We require multi-factor authentication for all logins so stolen "
        "passwords alone cannot get in.",
        "M1032",
    ),
    (
        "object_store",
        "All card numbers are encrypted at rest using envelope encryption, "
        "so a stolen storage bucket is unreadable.",
        "M1041",
    ),
    (
        "container",
        "The service account only has permission to read the one table it "
        "needs, nothing more, least privilege everywhere.",
        "M1018",
    ),
    (
        "api_gateway",
        "We deploy exploit protection to detect and block exploitation "
        "attempts and harden the gateway against vulnerabilities.",
        "M1050",
    ),
]


@pytest.mark.parametrize("component_type,notes,expected_mitigation", KNOWN_CASES)
def test_known_notes_surface_expected_mitigation_in_top_3(
    conn, provider, game_map, component_type, notes, expected_mitigation
):
    results = retrieve_candidate_mitigations(conn, provider, component_type, notes, game_map)
    assert expected_mitigation in results[:3]


def test_structured_filter_excludes_irrelevant_mitigations(conn, provider, game_map):
    """Even notes written entirely about MFA shouldn't surface M1032 for a
    component type whose techniques nothing in the ATT&CK data says MFA
    mitigates (secrets: only T1078.004 is a candidate there, which M1032
    *does* mitigate — database tests that path above. Use a component
    whose techniques are untouched by MFA instead: container's T1552.005 /
    T1528.)"""
    results = retrieve_candidate_mitigations(
        conn,
        provider,
        "container",
        "Multi-factor authentication everywhere, password stuffing stopped cold.",
        game_map,
    )
    assert "M1032" not in results


def test_retrieval_empty_for_component_type_with_no_techniques(conn, provider, game_map):
    assert retrieve_candidate_mitigations(conn, provider, "queue", "anything", game_map) == []
