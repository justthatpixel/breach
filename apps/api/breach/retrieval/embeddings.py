"""Embeddings behind an interface (HANDOFF §3) — swap providers without
touching call sites. EMBEDDING_PROVIDER in config picks which one
`get_default_provider()` returns.
"""
import hashlib
import math
import re
from typing import Protocol

import httpx

from .. import config


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str], embedding_type: str = "db") -> list[list[float]]: ...


class MiniMaxEmbeddingProvider:
    """The real provider. Needs MINIMAX_API_KEY. `embedding_type` is
    MiniMax's own split between indexed documents ("db") and a search
    query ("query") — mitigations get embedded as "db", player notes as
    "query"."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = config.MINIMAX_API_URL,
        model: str = config.EMBEDDING_MODEL,
        timeout: float = 20.0,
    ):
        self.api_key = api_key or config.MINIMAX_API_KEY
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY is not set")
        self.api_url = api_url
        self.model = model
        self.timeout = timeout

    def embed(self, texts: list[str], embedding_type: str = "db") -> list[list[float]]:
        response = httpx.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "texts": texts, "type": embedding_type},
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        base_resp = body.get("base_resp", {})
        if base_resp.get("status_code", 0) != 0:
            raise RuntimeError(f"MiniMax embeddings error: {base_resp}")
        return body["vectors"]


_WORD_RE = re.compile(r"[a-z0-9]+")


class DeterministicTestEmbedder:
    """No network, no API key — a bag-of-words vector where each
    dimension is a hashed word bucket. Good enough to make "similar
    wording -> similar vector" hold for the retrieval test; not a stand-in
    for real semantic quality. Used when EMBEDDING_PROVIDER=test, and by
    the test suite so it never depends on a live API key."""

    def __init__(self, dim: int = config.EMBEDDING_DIM):
        self.dim = dim

    def embed(self, texts: list[str], embedding_type: str = "db") -> list[list[float]]:
        del embedding_type  # the bag-of-words embedder doesn't distinguish
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        words = _WORD_RE.findall(text.lower())
        for word in words:
            bucket = int(hashlib.sha256(word.encode()).hexdigest(), 16) % self.dim
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def get_default_provider() -> EmbeddingProvider:
    if config.EMBEDDING_PROVIDER == "test":
        return DeterministicTestEmbedder()
    return MiniMaxEmbeddingProvider()
