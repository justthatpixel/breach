"""Load the curated ATT&CK subset (data/attack/) into Postgres. Idempotent
— upserts, so re-running after ingest_attack.py regenerates the data is
safe.

    python -m breach.retrieval.seed
"""
from pathlib import Path

from .. import config
from ..attack import load_attack_data
from .db import connect

REPO_ROOT = Path(__file__).resolve().parents[4]
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"


def seed(database_url: str | None = None, attack_data_dir: Path = ATTACK_DATA_DIR) -> None:
    attack_data = load_attack_data(attack_data_dir)

    with connect(database_url or config.DATABASE_URL) as conn:
        for technique in attack_data.techniques.values():
            conn.execute(
                """
                INSERT INTO techniques (id, name, description, platforms, tactics)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    platforms = EXCLUDED.platforms,
                    tactics = EXCLUDED.tactics
                """,
                (technique.id, technique.name, technique.description, technique.platforms, technique.tactics),
            )

        for mitigation in attack_data.mitigations.values():
            conn.execute(
                """
                INSERT INTO mitigations (id, name, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description
                """,
                (mitigation.id, mitigation.name, mitigation.description),
            )

        conn.execute("DELETE FROM technique_mitigations")
        for mitigation_id, technique_ids in attack_data.mitigates.items():
            for technique_id in technique_ids:
                conn.execute(
                    """
                    INSERT INTO technique_mitigations (mitigation_id, technique_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (mitigation_id, technique_id),
                )


if __name__ == "__main__":
    seed()
    print("Seed complete.")
