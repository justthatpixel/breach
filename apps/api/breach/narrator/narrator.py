"""The narrator (HANDOFF §6.2): turns engine output into replay/debrief
text. Input is the engine's own output (plus which component ids, if any,
were flagged for prompt injection) — never raw player notes, so an
injection attempt in the notes can't reach this prompt at all.
"""
import json
from dataclasses import dataclass

from .. import config
from ..engine.models import EngineResult
from ..llm import LLMCallResult, LLMClient
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import Debrief, NarratorOutput, ReplayStep


@dataclass
class NarratorRunResult:
    output: NarratorOutput
    llm_calls: list[LLMCallResult]


def run_narrator(
    llm_client: LLMClient,
    engine_result: EngineResult,
    flagged_components: list[str] | None = None,
) -> NarratorRunResult:
    flagged_components = flagged_components or []
    allowed_technique_ids = {step.technique_id for path in engine_result.paths for step in path.steps}
    # by_alias=True: HANDOFF §5 describes the step contract as {from, to, ...}.
    engine_result_json = engine_result.model_dump_json(by_alias=True)
    user_prompt = build_user_prompt(engine_result_json, flagged_components)

    llm_calls: list[LLMCallResult] = []
    parsed: NarratorOutput | None = None
    for _ in range(config.LLM_RETRY_COUNT + 1):
        call = llm_client.complete(SYSTEM_PROMPT, user_prompt, temperature=config.JUDGE_TEMPERATURE)
        llm_calls.append(call)
        parsed = _try_parse(call.text, allowed_technique_ids)
        if parsed is not None:
            break

    if parsed is None:
        return NarratorRunResult(_fallback(engine_result), llm_calls)
    return NarratorRunResult(parsed, llm_calls)


def _try_parse(raw_text: str, allowed_technique_ids: set[str]) -> NarratorOutput | None:
    try:
        data = json.loads(_extract_json(raw_text))
        output = NarratorOutput.model_validate(data)
    except Exception:
        return None
    # The narrator cannot introduce unknown technique IDs (HANDOFF §6.2 / M5 acceptance criteria).
    if any(step.technique_id not in allowed_technique_ids for step in output.steps):
        return None
    return output


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in LLM output")
    return text[start : end + 1]


def _fallback(engine_result: EngineResult) -> NarratorOutput:
    """If the narrator fails validation twice, fall back to a plain,
    factual rendering straight from the engine output rather than
    returning nothing."""
    steps = [
        ReplayStep(
            step=step.step,
            technique_id=step.technique_id,
            line=(
                f"Blocked at {step.to_component}: {step.technique_id} didn't get through."
                if step.blocked
                else f"Through at {step.to_component} via {step.technique_id}."
            ),
        )
        for path in engine_result.paths
        for step in path.steps
    ]
    through = sorted({s.technique_id for p in engine_result.paths for s in p.steps if not s.blocked})
    held = sorted({s.technique_id for p in engine_result.paths for s in p.steps if s.blocked})
    return NarratorOutput(steps=steps, debrief=Debrief(through=through, held=held, tips=[]))
