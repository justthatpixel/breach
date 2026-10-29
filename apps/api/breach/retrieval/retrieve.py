"""Hybrid retrieval (HANDOFF §6.1): structured filter first — mitigations
relevant to the component's own techniques — then rank that filtered set
by vector similarity to the player's notes. Never ranks a mitigation that
isn't structurally relevant to the component, regardless of how it scores
on embeddings.
"""
import psycopg

from .. import config
from ..levels.models import GameMap
from .embeddings import EmbeddingProvider


def relevant_mitigation_ids(conn: psycopg.Connection, component_type: str, game_map: GameMap) -> list[str]:
    technique_ids = game_map.techniques_for(component_type)
    if not technique_ids:
        return []
    rows = conn.execute(
        "SELECT DISTINCT mitigation_id FROM technique_mitigations WHERE technique_id = ANY(%s)",
        (technique_ids,),
    ).fetchall()
    return [row[0] for row in rows]


def retrieve_candidate_mitigations(
    conn: psycopg.Connection,
    provider: EmbeddingProvider,
    component_type: str,
    notes: str,
    game_map: GameMap,
    limit: int = config.RETRIEVAL_TOP_K,
) -> list[str]:
    """Mitigation IDs, nearest-to-the-notes first, restricted to
    mitigations relevant to this component type, capped at `limit`."""
    candidate_ids = relevant_mitigation_ids(conn, component_type, game_map)
    if not candidate_ids:
        return []

    [query_vector] = provider.embed([notes], embedding_type="query")

    rows = conn.execute(
        """
        SELECT mitigation_id
        FROM mitigation_embeddings
        WHERE mitigation_id = ANY(%s)
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (candidate_ids, query_vector, limit),
    ).fetchall()
    return [row[0] for row in rows]
