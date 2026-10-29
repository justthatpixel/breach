"""The judge (HANDOFF §6.1): decides which mitigations a player's
free-text notes genuinely credit. Player notes are untrusted input (§7) —
delimited with a per-call nonce and never trusted to self-report a
mitigation ID or an evidence quote without verification here in code.
"""
import json
import secrets
from dataclasses import dataclass

import psycopg

from .. import config
from ..attack.models import AttackData
from ..levels.models import GameMap
from ..llm import LLMCallResult, LLMClient
from ..retrieval.embeddings import EmbeddingProvider
from ..retrieval.retrieve import retrieve_candidate_mitigations
from ..security.injection import clean_notes, heuristic_injection_suspected
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import JudgeOutput


@dataclass
class JudgeRunResult:
    output: JudgeOutput
    llm_calls: list[LLMCallResult]


def run_judge(
    conn: psycopg.Connection,
    embedding_provider: EmbeddingProvider,
    llm_client: LLMClient,
    component_type: str,
    notes: str,
    game_map: GameMap,
    attack_data: AttackData,
) -> JudgeRunResult:
    notes = clean_notes(notes)
    if not notes.strip():
        return JudgeRunResult(JudgeOutput(credited=[], rejected_claims=[], injection_suspected=False), [])

    candidate_ids = retrieve_candidate_mitigations(conn, embedding_provider, component_type, notes, game_map)
    if not candidate_ids:
        return JudgeRunResult(JudgeOutput(credited=[], rejected_claims=[], injection_suspected=False), [])

    candidates = [
        {
            "mitigation_id": mid,
            "name": attack_data.mitigations[mid].name,
            "description": attack_data.mitigations[mid].description,
        }
        for mid in candidate_ids
    ]
    nonce = secrets.token_hex(8)
    user_prompt = build_user_prompt(component_type, candidates, notes, nonce)

    llm_calls: list[LLMCallResult] = []
    parsed: JudgeOutput | None = None
    for _ in range(config.LLM_RETRY_COUNT + 1):
        call = llm_client.complete(SYSTEM_PROMPT, user_prompt, temperature=config.JUDGE_TEMPERATURE)
        llm_calls.append(call)
        parsed = _try_parse(call.text, candidate_ids)
        if parsed is not None:
            break

    if parsed is None:
        # Validation failed twice (HANDOFF §6.1): credit nothing for this
        # component rather than guess, and log it via the heuristic flag.
        return JudgeRunResult(
            JudgeOutput(credited=[], rejected_claims=[], injection_suspected=heuristic_injection_suspected(notes)),
            llm_calls,
        )

    injection_suspected = parsed.injection_suspected or heuristic_injection_suspected(notes)
    verified_credits = (
        []
        if injection_suspected
        else [
            credit
            for credit in parsed.credited
            if credit.evidence in notes and credit.confidence >= config.JUDGE_CONFIDENCE_THRESHOLD
        ]
    )

    return JudgeRunResult(
        JudgeOutput(
            credited=verified_credits,
            rejected_claims=parsed.rejected_claims,
            injection_suspected=injection_suspected,
        ),
        llm_calls,
    )


def _try_parse(raw_text: str, candidate_ids: list[str]) -> JudgeOutput | None:
    try:
        data = json.loads(_extract_json(raw_text))
        output = JudgeOutput.model_validate(data)
    except Exception:
        return None
    # Never credit a mitigation outside the candidate list (HANDOFF §6.1), however the model behaved.
    output.credited = [c for c in output.credited if c.mitigation_id in candidate_ids]
    return output


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in LLM output")
    return text[start : end + 1]
