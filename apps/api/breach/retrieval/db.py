from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from .. import config


@contextmanager
def connect(database_url: str | None = None) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(database_url or config.DATABASE_URL, autocommit=True)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()
