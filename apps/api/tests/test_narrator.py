"""Contract tests for the narrator (HANDOFF §6.2, M5 acceptance
criteria): schema validation, and the headline requirement that it can't
introduce a technique ID the engine never produced. No DB needed — the
narrator only ever sees engine output."""
import json

import pytest

from breach.engine import ComponentDefence, run_engine
from breach.llm import LLMCallResult
from breach.narrator import run_narrator


class ScriptedLLMClient:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, temperature: float = 0.0) -> LLMCallResult:
        self.calls.append((system, user))
        text = self.responses.pop(0)
        return LLMCallResult(text=text, input_tokens=5, output_tokens=5, latency_seconds=0.0, model="fake")


@pytest.fixture
def engine_result(level3, game_map, attack_data):
    # The M2 golden loadout: breaches via T1190 -> T1552.005 -> T1078.004.
    defences = {
        "gateway": ComponentDefence(cards=["mfa"]),
        "payments": ComponentDefence(cards=["least_privilege"]),
        "postgres": ComponentDefence(cards=["encryption"]),
        "secrets": ComponentDefence(cards=["private_subnet"]),
    }
    return run_engine(level3, game_map, attack_data, defences)


def _valid_response(engine_result) -> str:
    technique_ids = sorted({s.technique_id for p in engine_result.paths for s in p.steps})
    return json.dumps(
        {
            "steps": [
                {"step": s.step, "technique_id": s.technique_id, "line": f"Line for {s.technique_id}"}
                for p in engine_result.paths
                for s in p.steps
            ],
            "debrief": {"through": technique_ids, "held": [], "tips": ["Tighten access."]},
        }
    )


def test_narrator_accepts_valid_technique_ids(engine_result):
    llm = ScriptedLLMClient([_valid_response(engine_result)])
    result = run_narrator(llm, engine_result)
    allowed = {s.technique_id for p in engine_result.paths for s in p.steps}
    assert all(step.technique_id in allowed for step in result.output.steps)
    assert len(result.llm_calls) == 1


def test_narrator_rejects_unknown_technique_id_then_retries(engine_result):
    bad_response = json.dumps(
        {
            "steps": [{"step": 1, "technique_id": "T9999", "line": "Made up attack."}],
            "debrief": {"through": ["T9999"], "held": [], "tips": []},
        }
    )
    llm = ScriptedLLMClient([bad_response, _valid_response(engine_result)])
    result = run_narrator(llm, engine_result)
    allowed = {s.technique_id for p in engine_result.paths for s in p.steps}
    assert all(step.technique_id in allowed for step in result.output.steps)
    assert len(result.llm_calls) == 2


def test_narrator_falls_back_to_factual_rendering_after_exhausting_retries(engine_result):
    bad_response = json.dumps(
        {
            "steps": [{"step": 1, "technique_id": "T9999", "line": "Made up attack."}],
            "debrief": {"through": ["T9999"], "held": [], "tips": []},
        }
    )
    llm = ScriptedLLMClient([bad_response, bad_response])
    result = run_narrator(llm, engine_result)

    allowed = {s.technique_id for p in engine_result.paths for s in p.steps}
    assert all(step.technique_id in allowed for step in result.output.steps)
    expected_through = sorted({s.technique_id for p in engine_result.paths for s in p.steps if not s.blocked})
    assert result.output.debrief.through == expected_through
    assert len(result.llm_calls) == 2


def test_narrator_prompt_never_contains_player_notes(engine_result):
    llm = ScriptedLLMClient([_valid_response(engine_result)])
    run_narrator(llm, engine_result)
    _, user_prompt = llm.calls[0]
    assert "player_notes" not in user_prompt


def test_narrator_mentions_flagged_component_without_leaking_notes(engine_result):
    llm = ScriptedLLMClient([_valid_response(engine_result)])
    run_narrator(llm, engine_result, flagged_components=["gateway"])
    _, user_prompt = llm.calls[0]
    assert "gateway" in user_prompt
    assert "player_notes" not in user_prompt
