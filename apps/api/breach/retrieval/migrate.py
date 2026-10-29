"""Create the extensions and tables retrieval needs. Idempotent — safe to
run against an already-migrated database.

    python -m breach.retrieval.migrate
"""
from pathlib import Path

import psycopg

from .. import config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def migrate(database_url: str | None = None) -> None:
    sql = SCHEMA_PATH.read_text().format(embedding_dim=config.EMBEDDING_DIM)
    # No register_vector here: the vector type doesn't exist until this
    # script's own CREATE EXTENSION statement runs.
    with psycopg.connect(database_url or config.DATABASE_URL, autocommit=True) as conn:
        conn.execute(sql)


if __name__ == "__main__":
    migrate()
    print("Migration complete.")
