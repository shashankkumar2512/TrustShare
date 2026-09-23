# server/src/analytics/setup.py
"""
One-time setup script for the analytics module.

Run this AFTER the main app has been started at least once
(so users/files/share_links tables already exist).

Usage:
    cd project-root/server
    python -m src.analytics.setup

What it does:
  1. Creates all analytics tables (if not exist)
  2. Seeds event types + statuses (master data)
  3. Seeds default config values
  4. Seeds severity mapping
  5. Generates demo events (only if table is empty)
"""

from src.database.core import Base, engine, SessionLocal

# ── Import ALL referenced entities so SQLAlchemy knows the FK targets ────────
# analytics_events has foreign keys to users, files, share_links
from src.entities.user       import User        # noqa: F401
from src.entities.file       import File        # noqa: F401
from src.entities.folder     import Folder      # noqa: F401
from src.entities.share_link import ShareLink   # noqa: F401

# ── Import analytics models ──────────────────────────────────────────────────
from src.analytics.models.analytics_event  import AnalyticsEvent      # noqa: F401
from src.analytics.models.analytics_config import AnalyticsConfig     # noqa: F401
from src.analytics.models.event_type       import AnalyticsEventType  # noqa: F401
from src.analytics.models.event_status     import AnalyticsEventStatus # noqa: F401
from src.analytics.models.severity_map     import AnalyticsSeverityMap # noqa: F401

from src.analytics.seed import (
    seed_event_types,
    seed_event_statuses,
    seed_analytics_config,
    seed_severity_map,
    seed_demo_data,
)


def main():
    print("═" * 60)
    print("TrustShare Analytics — Setup")
    print("═" * 60)

    # 1. Create tables
    print("\n[1/5] Creating analytics tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created")

    # 2-5. Seed data
    db = SessionLocal()
    try:
        print("\n[2/5] Seeding event types...")
        seed_event_types(db)
        print("  ✓ Event types seeded")

        print("\n[3/5] Seeding event statuses...")
        seed_event_statuses(db)
        print("  ✓ Event statuses seeded")

        print("\n[4/5] Seeding analytics config...")
        seed_analytics_config(db)
        print("  ✓ Config seeded")

        print("\n[5/5] Seeding severity map...")
        seed_severity_map(db)
        print("  ✓ Severity map seeded")

        # ⚠️ DISABLED FOR PRODUCTION SUBMISSION
        #print("\n[Bonus] Generating demo data...")
        #seed_demo_data(db)

    finally:
        db.close()

    print("\n" + "═" * 60)
    print("✅ Analytics setup complete!")
    print("═" * 60)
    print("\nYou can now:")
    print("  • Start the server: python -m uvicorn src.api:app --reload")
    print("  • Visit dashboard:  http://localhost:3000/analytics")
    print("  • API endpoint:     http://localhost:8000/api/analytics/summary")


if __name__ == "__main__":
    main()