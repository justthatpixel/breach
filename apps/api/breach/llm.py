"""LLM client behind an interface (HANDOFF §3, §6.3): model name,
temperature, timeout and retries all live in config, never hardcoded at a
call site, so swapping models or providers is a one-file change — same
split as the embedding provider in retrieval/embeddings.py.
"""
import re
import time
from dataclasses import dataclass
from typing import Protocol

import httpx

from . import config


@dataclass
class LLMCallResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    model: str


class LLMClient(Protocol):
    def complete(self, system: str, user: str, temperature: float = 0.0) -> LLMCallResult: ...


class AnthropicLLMClient:
    """The real provider. Needs ANTHROPIC_API_KEY."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = config.LLM_MODEL,
        timeout: float = config.LLM_TIMEOUT_SECONDS,
    ):
        import anthropic  # imported lazily: only required when this client is actually used

        key = api_key or config.ANTHROPIC_API_KEY
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.model = model
        self._client = anthropic.Anthropic(api_key=key, timeout=timeout)

    def complete(self, system: str, user: str, temperature: float = 0.0) -> LLMCallResult:
        started = time.monotonic()
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency_seconds = time.monotonic() - started
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMCallResult(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_seconds=latency_seconds,
            model=self.model,
        )


class OllamaLLMClient:
    """A local model served by Ollama (HANDOFF §3's "LLM... in config, not
    hardcoded" — here that means a self-hosted provider instead of a paid
    API). No key, no per-call cost. `message.content` is the final
    answer; Qwen3's own `message.thinking` reasoning trace is discarded —
    only the content is validated against a schema downstream."""

    def __init__(
        self,
        model: str = config.OLLAMA_MODEL,
        base_url: str = config.OLLAMA_BASE_URL,
        timeout: float = config.LLM_TIMEOUT_SECONDS,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, system: str, user: str, temperature: float = 0.0) -> LLMCallResult:
        started = time.monotonic()
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,  # Qwen3's extended reasoning adds latency with no benefit for a schema-constrained judge/narrator call
                "options": {"temperature": temperature},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        return LLMCallResult(
            text=body["message"]["content"],
            input_tokens=body.get("prompt_eval_count", 0),
            output_tokens=body.get("eval_count", 0),
            latency_seconds=time.monotonic() - started,
            model=self.model,
        )


_CANDIDATE_LINE_RE = re.compile(r"^- (?P<id>\S+): (?P<name>.+?) — ")
_NOTES_RE = re.compile(r"<player_notes[^>]*>\n(?P<notes>.*?)\n</player_notes", re.S)
_ENGINE_OUTPUT_RE = re.compile(
    r"Engine output:\n(?P<json>.*?)\n(?:Flagged[^\n]*\n)?\nWrite the Red Team replay", re.S
)


class DeterministicTestLLMClient:
    """No network, no API key — a simple deterministic stand-in used when
    LLM_PROVIDER=test (local dev and e2e runs without a key, and the test
    suite). It reads the same prompts the real judge/narrator build
    (judge/prompts.py, narrator/prompts.py) and produces valid JSON for
    their schemas by simple keyword matching, so it's a believable judge
    and narrator, not just a schema-filler."""

    def complete(self, system: str, user: str, temperature: float = 0.0) -> LLMCallResult:
        del system, temperature
        started = time.monotonic()
        if "player_notes" in user:
            text = self._judge_response(user)
        else:
            text = self._narrator_response(user)
        return LLMCallResult(
            text=text,
            input_tokens=len(user) // 4,
            output_tokens=len(text) // 4,
            latency_seconds=time.monotonic() - started,
            model="deterministic-test",
        )

    def _judge_response(self, user: str) -> str:
        import json

        notes_match = _NOTES_RE.search(user)
        notes = notes_match.group("notes") if notes_match else ""
        notes_lower = notes.lower()

        credited = []
        for line in user.splitlines():
            match = _CANDIDATE_LINE_RE.match(line)
            if not match:
                continue
            name_words = [w for w in re.findall(r"[a-z0-9]+", match["name"].lower()) if len(w) > 3]
            hit_word = next((w for w in name_words if w in notes_lower), None)
            if hit_word:
                start = notes_lower.find(hit_word)
                evidence = notes[start : start + len(hit_word)]
                credited.append({"mitigation_id": match["id"], "evidence": evidence, "confidence": 0.8})

        return json.dumps(
            {
                "credited": credited,
                "rejected_claims": [],
                "injection_suspected": False,
            }
        )

    def _narrator_response(self, user: str) -> str:
        import json

        match = _ENGINE_OUTPUT_RE.search(user)
        engine_output = json.loads(match["json"]) if match else {"paths": []}

        steps = []
        through_ids: list[str] = []
        held_ids: list[str] = []
        for path in engine_output.get("paths", []):
            for step in path.get("steps", []):
                technique_id = step["technique_id"]
                blocked = step["blocked"]
                (held_ids if blocked else through_ids).append(technique_id)
                steps.append(
                    {
                        "step": step["step"],
                        "technique_id": technique_id,
                        "line": (
                            f"Blocked at {step['to']}: {technique_id} didn't get through."
                            if blocked
                            else f"Through at {step['to']} via {technique_id}."
                        ),
                    }
                )

        return json.dumps(
            {
                "steps": steps,
                "debrief": {
                    "through": sorted(set(through_ids)),
                    "held": sorted(set(held_ids)),
                    "tips": [],
                },
            }
        )


def get_default_client() -> LLMClient:
    if config.LLM_PROVIDER == "test":
        return DeterministicTestLLMClient()
    if config.LLM_PROVIDER == "ollama":
        return OllamaLLMClient()
    return AnthropicLLMClient()


def estimate_cost_usd(calls: list[LLMCallResult]) -> float:
    """A list-price estimate (HANDOFF §10) for Anthropic calls only — a
    self-hosted Ollama or deterministic-test call costs nothing to run."""
    return sum(
        call.input_tokens / 1000 * config.LLM_INPUT_PRICE_PER_1K
        + call.output_tokens / 1000 * config.LLM_OUTPUT_PRICE_PER_1K
        for call in calls
        if call.model.startswith("claude")
    )
