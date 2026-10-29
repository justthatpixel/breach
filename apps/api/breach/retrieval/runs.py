"""Persistence for the `runs` table (HANDOFF §4.4) — kept for debugging
and eval mining, and so a debrief can be re-fetched by id (HANDOFF §10's
GET /runs/{id}, for sharing)."""
import json
from uuid import UUID

import psycopg


def insert_run(
    conn: psycopg.Connection,
    level_id: str,
    defences: dict,
    judge_output: dict,
    engine_output: dict,
    narrator_output: dict,
) -> UUID:
    row = conn.execute(
        """
        INSERT INTO runs (level_id, defences, judge_output, engine_output, narrator_output)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            level_id,
            json.dumps(defences),
            json.dumps(judge_output),
            json.dumps(engine_output),
            json.dumps(narrator_output),
        ),
    ).fetchone()
    return row[0]


def get_run(conn: psycopg.Connection, run_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT id, level_id, defences, judge_output, engine_output, narrator_output, created_at
        FROM runs WHERE id = %s
        """,
        (run_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": str(row[0]),
        "level_id": row[1],
        "defences": row[2],
        "judge_output": row[3],
        "engine_output": row[4],
        "narrator_output": row[5],
        "created_at": row[6].isoformat(),
    }
