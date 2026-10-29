"""Embed every mitigation's name+description and upsert into
mitigation_embeddings. Requires the DB to be migrated and seeded first.

    python -m breach.retrieval.embed_mitigations
"""
from .. import config
from .db import connect
from .embeddings import EmbeddingProvider, get_default_provider


def chunk_text(name: str, description: str) -> str:
    return f"{name}: {description}"


def embed_mitigations(
    provider: EmbeddingProvider | None = None, database_url: str | None = None
) -> int:
    provider = provider or get_default_provider()

    with connect(database_url or config.DATABASE_URL) as conn:
        rows = conn.execute("SELECT id, name, description FROM mitigations ORDER BY id").fetchall()
        if not rows:
            return 0

        texts = [chunk_text(name, description) for _id, name, description in rows]
        vectors = provider.embed(texts)

        for (mitigation_id, name, description), vector in zip(rows, vectors):
            conn.execute(
                """
                INSERT INTO mitigation_embeddings (mitigation_id, chunk_text, embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (mitigation_id) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding
                """,
                (mitigation_id, chunk_text(name, description), vector),
            )

        return len(rows)


if __name__ == "__main__":
    count = embed_mitigations()
    print(f"Embedded {count} mitigations.")
