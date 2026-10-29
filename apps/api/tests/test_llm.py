import httpx
import pytest

from breach import config
from breach.llm import DeterministicTestLLMClient, LLMCallResult, OllamaLLMClient, estimate_cost_usd


def test_estimate_cost_usd_counts_only_anthropic_calls():
    calls = [
        LLMCallResult(text="", input_tokens=1000, output_tokens=1000, latency_seconds=0, model="claude-sonnet-5-5"),
        LLMCallResult(text="", input_tokens=1000, output_tokens=1000, latency_seconds=0, model="qwen3:8b"),
        LLMCallResult(text="", input_tokens=1000, output_tokens=1000, latency_seconds=0, model="deterministic-test"),
    ]
    expected = config.LLM_INPUT_PRICE_PER_1K + config.LLM_OUTPUT_PRICE_PER_1K
    assert estimate_cost_usd(calls) == pytest.approx(expected)


def test_deterministic_test_llm_client_narrator_response_is_valid_json_shape():
    import json

    client = DeterministicTestLLMClient()
    engine_json = json.dumps(
        {"paths": [{"steps": [{"step": 1, "from": "a", "to": "b", "technique_id": "T1190", "blocked": False}]}]}
    )
    user_prompt = f"Engine output:\n{engine_json}\n\nWrite the Red Team replay and debrief for this run."
    result = client.complete("system", user_prompt)
    data = json.loads(result.text)
    assert data["steps"] == [{"step": 1, "technique_id": "T1190", "line": "Through at b via T1190."}]
    assert data["debrief"]["through"] == ["T1190"]


@pytest.mark.ollama
def test_ollama_client_completes_a_simple_prompt():
    try:
        httpx.get(f"{config.OLLAMA_BASE_URL}/api/version", timeout=2.0).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Ollama not reachable: {exc}")

    client = OllamaLLMClient()
    result = client.complete(
        "Respond with only the single word OK, nothing else.",
        "Say OK.",
        temperature=0,
    )
    assert "OK" in result.text
    assert result.model == config.OLLAMA_MODEL
