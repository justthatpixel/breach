"""All config in one place, read from env vars (HANDOFF §6.3). Nothing here
is hardcoded into call sites, so swapping a model, DB, or embedding
provider never means hunting through the codebase.
"""
import os


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


DATABASE_URL = _env("DATABASE_URL", "postgresql://breach:breach@localhost:5433/breach")

# "minimax" (real, needs MINIMAX_API_KEY) or "test" (deterministic, no
# network — used by the test suite and anywhere a key isn't available).
EMBEDDING_PROVIDER = _env("EMBEDDING_PROVIDER", "minimax")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
MINIMAX_API_URL = _env("MINIMAX_API_URL", "https://api.minimax.io/v1/embeddings")
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "embo-01")
EMBEDDING_DIM = int(_env("EMBEDDING_DIM", "1536"))

RETRIEVAL_TOP_K = int(_env("RETRIEVAL_TOP_K", "5"))

# LLM config (M5/M6). "anthropic" (real, needs ANTHROPIC_API_KEY),
# "ollama" (self-hosted, free — the model used for eval numbers and the
# CI eval gate, see evals/), or "test" (deterministic, no network — used
# by the rest of the test suite), same split as EMBEDDING_PROVIDER above.
LLM_PROVIDER = _env("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
LLM_MODEL = _env("LLM_MODEL", "claude-sonnet-5-5")
OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "qwen3:8b")
JUDGE_TEMPERATURE = float(_env("JUDGE_TEMPERATURE", "0"))
JUDGE_CONFIDENCE_THRESHOLD = float(_env("JUDGE_CONFIDENCE_THRESHOLD", "0.6"))
LLM_TIMEOUT_SECONDS = float(_env("LLM_TIMEOUT_SECONDS", "20"))
LLM_RETRY_COUNT = int(_env("LLM_RETRY_COUNT", "1"))

# List-price estimate only (HANDOFF §10's "total cost estimate") — not an
# actual billed amount, so it's configurable rather than baked in.
LLM_INPUT_PRICE_PER_1K = float(_env("LLM_INPUT_PRICE_PER_1K", "0.003"))
LLM_OUTPUT_PRICE_PER_1K = float(_env("LLM_OUTPUT_PRICE_PER_1K", "0.015"))

# Security of the AI itself (HANDOFF §7.4): input limits on player notes.
MAX_NOTES_LENGTH = int(_env("MAX_NOTES_LENGTH", "1000"))

# Rate limit on POST /runs (HANDOFF §7.4), requests per minute per client IP.
RUN_RATE_LIMIT_PER_MINUTE = int(_env("RUN_RATE_LIMIT_PER_MINUTE", "10"))
