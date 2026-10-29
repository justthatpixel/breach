"""API contract tests (HANDOFF §10). /healthz and /levels need no DB and
always run. /runs exercises the whole judge -> engine -> narrator loop
against a real Postgres with the deterministic (no-network) embedding and
LLM providers, and is skipped cleanly if Docker/Postgres isn't up, same
pattern as test_retrieval.py.
"""
import pytest
from fastapi.testclient import TestClient

from breach.app import app, get_embedding_provider, get_llm_client
from breach.llm import DeterministicTestLLMClient
from breach.retrieval import DeterministicTestEmbedder
from breach.retrieval.embed_mitigations import embed_mitigations
from breach.retrieval.migrate import migrate
from breach.retrieval.seed import seed as seed_db

client = TestClient(app)


def test_healthz_ok():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_levels_includes_level3():
    response = client.get("/levels")
    assert response.status_code == 200
    ids = [level["id"] for level in response.json()]
    assert "03-payments" in ids


def test_get_level3_returns_full_definition():
    response = client.get("/levels/03-payments")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "03-payments"
    assert any(c["id"] == "postgres" for c in body["components"])


def test_get_unknown_level_is_404():
    response = client.get("/levels/does-not-exist")
    assert response.status_code == 404


@pytest.fixture(scope="module")
def pg_ready():
    try:
        migrate()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres not reachable for API run tests: {exc}")
    seed_db()
    embed_mitigations(provider=DeterministicTestEmbedder())


@pytest.fixture
def api_client(pg_ready):
    app.dependency_overrides[get_embedding_provider] = lambda: DeterministicTestEmbedder()
    app.dependency_overrides[get_llm_client] = lambda: DeterministicTestLLMClient()
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.retrieval
def test_create_run_full_flow(api_client):
    response = api_client.post(
        "/runs",
        json={
            "level_id": "03-payments",
            "defences": {
                "gateway": {"cards": ["mfa"], "notes": ""},
                "payments": {"cards": ["least_privilege"], "notes": ""},
                "postgres": {"cards": ["encryption"], "notes": ""},
                "secrets": {"cards": ["private_subnet"], "notes": ""},
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["level_id"] == "03-payments"
    assert "id" in body
    assert body["engine_output"]["grade"] in {"A", "B", "C", "D", "F"}
    assert body["narrator_output"]["steps"]
    assert body["total_cost_usd_estimate"] >= 0


@pytest.mark.retrieval
def test_create_run_unknown_level_is_404(api_client):
    response = api_client.post("/runs", json={"level_id": "nope", "defences": {}})
    assert response.status_code == 404


@pytest.mark.retrieval
def test_create_run_unknown_card_is_400(api_client):
    response = api_client.post(
        "/runs",
        json={"level_id": "03-payments", "defences": {"gateway": {"cards": ["not_a_real_card"], "notes": ""}}},
    )
    assert response.status_code == 400


@pytest.mark.retrieval
def test_create_run_unknown_component_is_400(api_client):
    response = api_client.post(
        "/runs",
        json={"level_id": "03-payments", "defences": {"not_a_component": {"cards": [], "notes": ""}}},
    )
    assert response.status_code == 400


@pytest.mark.retrieval
def test_create_run_can_be_fetched_back(api_client):
    created = api_client.post("/runs", json={"level_id": "03-payments", "defences": {}}).json()
    fetched = api_client.get(f"/runs/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["level_id"] == "03-payments"


@pytest.mark.retrieval
def test_create_run_is_rate_limited(api_client, monkeypatch):
    import breach.app as app_module

    monkeypatch.setattr(app_module._rate_limiter, "limit", 1)
    app_module._rate_limiter._hits.clear()
    try:
        first = api_client.post("/runs", json={"level_id": "03-payments", "defences": {}})
        second = api_client.post("/runs", json={"level_id": "03-payments", "defences": {}})
        assert first.status_code == 200
        assert second.status_code == 429
    finally:
        app_module._rate_limiter._hits.clear()
