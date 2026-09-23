"""
Assistant Module Seeders

Runs all seed scripts in the correct order.
Idempotent — safe to run multiple times.
Only inserts missing rows, never overwrites existing.
"""
import logging

from sqlalchemy.orm import Session

from src.assistant.seed.seed_configs import seed_configs
from src.assistant.seed.seed_functions import seed_functions
from src.assistant.seed.seed_prompts import seed_prompts
from src.assistant.seed.seed_suggested_queries import seed_suggested_queries

logger = logging.getLogger(__name__)


def seed_all_assistant_data(db: Session) -> dict:
    """
    Seed all assistant reference data.

    Returns dict with counts of rows added per seeder.
    """
    results = {}

    try:
        results["configs"] = seed_configs(db)
        results["functions"] = seed_functions(db)
        results["prompts"] = seed_prompts(db)
        results["suggested_queries"] = seed_suggested_queries(db)

        total = sum(results.values())
        logger.info(f"Assistant seeding complete: {total} rows added")
        print(f"  ✓ Assistant seeded: {results}")

    except Exception as e:
        logger.error(f"Assistant seeding failed: {e}", exc_info=True)
        db.rollback()
        raise

    return results