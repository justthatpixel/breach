"""FastAPI app (HANDOFF §10). POST /runs is the whole loop: judge credits
the player's notes, the deterministic engine decides what breaches, the
narrator turns that into replay/debrief text. Every LLM boundary is
schema-validated; nothing from the judge or narrator reaches the engine or
the response unverified.
"""
import time
from collections import defaultdict
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config
from .attack import AttackData, load_attack_data
from .engine import ComponentDefence, Defences, run_engine
from .judge import run_judge
from .levels import GameMap, Level, load_game_map, load_level
from .llm import LLMCallResult, LLMClient, estimate_cost_usd, get_default_client
from .narrator import run_narrator
from .retrieval import EmbeddingProvider, connect, get_default_provider
from .retrieval.runs import get_run, insert_run

REPO_ROOT = Path(__file__).resolve().parents[3]
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"
GAME_MAP_PATH = ATTACK_DATA_DIR / "game_map.yaml"
LEVELS_DIR = REPO_ROOT / "data" / "levels"

app = FastAPI(title="Breach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: no accounts, runs are anonymous (HANDOFF §12)
    allow_methods=["*"],
    allow_headers=["*"],
)


class AppState:
    """Loaded once at import time: curated ATT&CK data, the game map, and
    every level — small, static, and expensive to re-validate per request."""

    def __init__(self) -> None:
        self.attack_data: AttackData = load_attack_data(ATTACK_DATA_DIR)
        self.game_map: GameMap = load_game_map(GAME_MAP_PATH, self.attack_data)
        self.levels: dict[str, Level] = {}
        for level_path in sorted(LEVELS_DIR.glob("*.yaml")):
            level = load_level(level_path, self.game_map)
            self.levels[level.id] = level


state = AppState()


def get_embedding_provider() -> EmbeddingProvider:
    return get_default_provider()


def get_llm_client() -> LLMClient:
    return get_default_client()


class _RateLimiter:
    """A fixed-window limiter per client IP (HANDOFF §7.4). In-memory —
    fine for a single-process deploy; a multi-instance one would need a
    shared store instead."""

    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window = self._hits[key]
        window[:] = [t for t in window if now - t < 60]
        if len(window) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many runs. Try again in a minute.")
        window.append(now)


_rate_limiter = _RateLimiter(config.RUN_RATE_LIMIT_PER_MINUTE)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/levels")
def list_levels() -> list[dict]:
    # MVP ships one level; it's always playable, nothing to lock yet
    # (locked/upcoming levels are campaign-track display state the
    # frontend's own fixtures carry, per M3).
    return [
        {"id": level.id, "title": level.title, "threat_level": level.threat_level, "state": "current"}
        for level in state.levels.values()
    ]


@app.get("/levels/{level_id}", response_model=Level)
def get_level(level_id: str) -> Level:
    level = state.levels.get(level_id)
    if level is None:
        raise HTTPException(status_code=404, detail=f"Unknown level {level_id!r}")
    return level


class ComponentDefenceIn(BaseModel):
    cards: list[str] = []
    notes: str = ""


class RunRequest(BaseModel):
    level_id: str
    defences: dict[str, ComponentDefenceIn] = {}


class LLMCallLog(BaseModel):
    component: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


class RunResponse(BaseModel):
    id: str
    level_id: str
    engine_output: dict
    narrator_output: dict
    judge_output: dict[str, dict]
    llm_calls: list[LLMCallLog]
    total_cost_usd_estimate: float


@app.post("/runs", response_model=RunResponse)
def create_run(
    body: RunRequest,
    request: Request,
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    llm_client: LLMClient = Depends(get_llm_client),
) -> RunResponse:
    _rate_limiter.check(request.client.host if request.client else "unknown")

    level = state.levels.get(body.level_id)
    if level is None:
        raise HTTPException(status_code=404, detail=f"Unknown level {body.level_id!r}")

    unknown_components = set(body.defences) - level.component_ids()
    if unknown_components:
        raise HTTPException(status_code=400, detail=f"Unknown component ids: {sorted(unknown_components)}")
    for component_id, defence_in in body.defences.items():
        unknown_cards = set(defence_in.cards) - set(level.cards_available)
        if unknown_cards:
            raise HTTPException(
                status_code=400, detail=f"Unknown cards for {component_id!r}: {sorted(unknown_cards)}"
            )

    components_by_id = {c.id: c for c in level.components}
    raw_calls: list[tuple[str, LLMCallResult]] = []
    judge_outputs: dict[str, dict] = {}
    flagged_components: list[str] = []
    defences: Defences = {}

    with connect() as conn:
        for component_id, defence_in in body.defences.items():
            component = components_by_id[component_id]
            judge_result = run_judge(
                conn,
                embedding_provider,
                llm_client,
                component.type,
                defence_in.notes,
                state.game_map,
                state.attack_data,
            )
            judge_outputs[component_id] = judge_result.output.model_dump()
            raw_calls.extend((component_id, call) for call in judge_result.llm_calls)
            if judge_result.output.injection_suspected:
                flagged_components.append(component_id)

            defences[component_id] = ComponentDefence(
                cards=defence_in.cards,
                credited_mitigations=[c.mitigation_id for c in judge_result.output.credited],
            )

        engine_result = run_engine(level, state.game_map, state.attack_data, defences)

        narrator_result = run_narrator(llm_client, engine_result, flagged_components)
        raw_calls.extend(("__narrator__", call) for call in narrator_result.llm_calls)

        run_id = insert_run(
            conn,
            level.id,
            {cid: d.model_dump() for cid, d in body.defences.items()},
            judge_outputs,
            engine_result.model_dump(by_alias=True),
            narrator_result.output.model_dump(),
        )

    return RunResponse(
        id=str(run_id),
        level_id=level.id,
        engine_output=engine_result.model_dump(by_alias=True),
        narrator_output=narrator_result.output.model_dump(),
        judge_output=judge_outputs,
        llm_calls=[
            LLMCallLog(
                component=component_id,
                model=call.model,
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                latency_seconds=call.latency_seconds,
            )
            for component_id, call in raw_calls
        ],
        total_cost_usd_estimate=estimate_cost_usd([call for _, call in raw_calls]),
    )


@app.get("/runs/{run_id}")
def get_run_by_id(run_id: str) -> dict:
    with connect() as conn:
        run = get_run(conn, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run {run_id!r}")
    return run
