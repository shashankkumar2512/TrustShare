# server/src/analytics/seed/seed_demo_data.py
"""
Generates realistic demo analytics events so the dashboard has data to show.
Safe to run multiple times — only inserts if events table is empty.

⚠️ REMOVE OR DISABLE THIS FILE BEFORE PRODUCTION SUBMISSION!

To disable: Comment out the call to seed_demo_data() in your main.py or setup.py
"""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.analytics.models.analytics_event import AnalyticsEvent
from src.analytics.constants import AnalyticsEventType, AnalyticsEventStatus
from src.entities.user import User
from src.entities.file import File
from src.entities.folder import Folder  # ✅ Add this line
from src.entities.share_link import ShareLink

# ═══════════════════════════════════════════════════════════════════════
# DEMO DATA POOLS
# ═══════════════════════════════════════════════════════════════════════

IPS = [
    ("91.108.56.183", "Kyiv", "UA"),
    ("180.163.10.88", "Shanghai", "CN"),
    ("82.132.10.44", "London", "UK"),
    ("104.28.91.99", "New York", "US"),
    ("52.14.22.101", "Berlin", "DE"),
    ("13.107.42.14", "Sydney", "AU"),
    ("203.0.113.42", "Tokyo", "JP"),
    ("198.51.100.5", "Paris", "FR"),
]

BROWSERS = ["Chrome", "Firefox", "Safari", "Edge"]
OS = ["Windows", "macOS", "Linux", "iOS", "Android"]

# ═══ Sample file names for demo files ═══
DEMO_FILES = [
    ("Q4-Report.pdf", "pdf", 2_500_000),
    ("Financial-Analysis.pdf", "pdf", 1_800_000),
    ("Contract-2024.pdf", "pdf", 850_000),
    ("Employee-Handbook.pdf", "pdf", 3_200_000),
    ("Product-Roadmap.docx", "docx", 450_000),
    ("Meeting-Notes.docx", "docx", 120_000),
    ("Project-Plan.docx", "docx", 380_000),
    ("Sales-Data.xlsx", "xlsx", 720_000),
    ("Budget-2024.xlsx", "xlsx", 550_000),
    ("Metrics-Dashboard.xlsx", "xlsx", 890_000),
    ("Presentation.pptx", "pptx", 4_500_000),
    ("Team-Slides.pptx", "pptx", 2_100_000),
    ("Logo-Design.png", "png", 650_000),
    ("Screenshot-01.png", "png", 420_000),
    ("Screenshot-02.png", "png", 380_000),
    ("Product-Photo.jpg", "jpg", 1_800_000),
    ("Team-Photo.jpg", "jpg", 2_400_000),
    ("Banner.jpg", "jpg", 1_100_000),
    ("Notes.txt", "txt", 15_000),
    ("Config.txt", "txt", 8_000),
    ("Archive.zip", "zip", 8_500_000),
    ("Backup.zip", "zip", 12_000_000),
    ("Demo-Video.mp4", "mp4", 25_000_000),
    ("Tutorial.mp4", "mp4", 18_500_000),
]


def _get_mimetype(ext: str) -> str:
    """Get proper mimetype for file extension."""
    mimetypes = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ppt": "application/vnd.ms-powerpoint",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "mp4": "video/mp4",
        "mp3": "audio/mpeg",
        "zip": "application/zip",
        "txt": "text/plain",
    }
    return mimetypes.get(ext.lower(), "application/octet-stream")


# ═══ Demo users to create ═══
DEMO_USERS = [
    {"name": "Alice Johnson", "email": "alice@demo.com"},
    {"name": "Bob Smith", "email": "bob@demo.com"},
    {"name": "Carol Davis", "email": "carol@demo.com"},
    {"name": "David Wilson", "email": "david@demo.com"},
    {"name": "Emma Brown", "email": "emma@demo.com"},
]

SEC_EVENT_PRESETS = [
    {
        "severity_key": "brute_force",
        "label": "Brute force blocked",
        "detail": "8 attempts from Kyiv, UA",
        "target": "alex@acme.com",
        "attempts": 8,
        "status": AnalyticsEventStatus.FAILED,
    },
    {
        "severity_key": "new_device",
        "label": "Login from new device",
        "detail": "Chrome on Windows · NYC · 104.28.91.42",
        "target": "sarah@acme.com",
        "attempts": 1,
        "status": AnalyticsEventStatus.SUCCESS,
    },
    {
        "severity_key": "external_link",
        "label": "External link accessed",
        "detail": "Brand-Assets.zip opened from London, UK",
        "target": "Brand-Assets.zip",
        "attempts": 1,
        "status": AnalyticsEventStatus.SUCCESS,
    },
    {
        "severity_key": "unusual_access",
        "label": "Unusual access pattern",
        "detail": "12 files accessed in 4 min by partner user",
        "target": "Finance Reports/",
        "attempts": 12,
        "status": AnalyticsEventStatus.WARNING,
    },
    {
        "severity_key": "admin_role",
        "label": "Admin role granted",
        "detail": "New admin access provisioned",
        "target": "system",
        "attempts": 1,
        "status": AnalyticsEventStatus.SUCCESS,
    },
]

UNAUTH_PRESETS = [
    {"target": "alex@acme.com", "attempts": 8, "hours_ago": 2, "blocked": True},
    {"target": "Finance Reports/", "attempts": 12, "hours_ago": 5, "blocked": True},
    {"target": "Brand-Assets.zip", "attempts": 3, "hours_ago": 30, "blocked": False},
    {"target": "alex@acme.com", "attempts": 2, "hours_ago": 50, "blocked": False},
]


# ═══════════════════════════════════════════════════════════════════════
# MAIN SEED FUNCTION
# ═══════════════════════════════════════════════════════════════════════


def seed_demo_data(db: Session, force: bool = False):
    """
    Seeds demo analytics events + files + users for testing.
    Set force=True to reset and add more events.
    """
    existing = db.query(AnalyticsEvent).count()
    if existing > 0 and not force:
        print(f"  ↷ analytics_events already has {existing} rows — skipping demo seed")
        return

    # ═══ Step 1: Create demo users (for Top Active Users feature) ═══
    print("  → Creating demo users...")
    demo_user_ids = _seed_demo_users(db)

    # Also get all existing users
    all_users = db.query(User).all()
    if not all_users:
        print("  ⚠ No users in DB — cannot seed demo events")
        return

    user_ids = [u.id for u in all_users]
    now = datetime.now(timezone.utc)
    events_added = 0
    files_added = 0

    # ═══ Step 2: Create demo files (for File Type Distribution) ═══
    print("  → Creating demo files...")
    files_added = _seed_demo_files(db, user_ids)

    # ═══ Step 3: LOGIN events — spread across 30 days ═══
    print("  → Seeding login events...")
    for day_offset in range(30):
        day = now - timedelta(days=day_offset)
        success_count = random.randint(15, 45)
        failed_count = random.randint(2, 12)

        for _ in range(success_count):
            ip, city, country = random.choice(IPS)
            ts = day - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            db.add(
                AnalyticsEvent(
                    event_type=AnalyticsEventType.LOGIN,
                    user_id=random.choice(user_ids),
                    status=AnalyticsEventStatus.SUCCESS,
                    ip_address=ip,
                    city=city,
                    country=country,
                    browser=random.choice(BROWSERS),
                    operating_system=random.choice(OS),
                    created_at=ts,
                )
            )
            events_added += 1

        # Failed logins with realistic patterns (for heatmap)
        for _ in range(failed_count):
            ip, city, country = random.choice(IPS)
            # Attackers often work at odd hours
            hour = random.choices(
                [0, 1, 2, 3, 4, 5, 22, 23, 10, 11, 15, 16],
                weights=[3, 4, 5, 5, 4, 3, 3, 3, 1, 1, 2, 2],
            )[0]
            ts = day.replace(hour=hour, minute=random.randint(0, 59))
            db.add(
                AnalyticsEvent(
                    event_type=AnalyticsEventType.LOGIN,
                    user_id=random.choice(user_ids),
                    status=AnalyticsEventStatus.FAILED,
                    ip_address=ip,
                    city=city,
                    country=country,
                    event_metadata={
                        "target": f"user{random.randint(1, 10)}@example.com",
                        "attempts": random.randint(1, 8),
                    },
                    created_at=ts,
                )
            )
            events_added += 1

    # ═══ Step 4: UPLOAD events ═══
    print("  → Seeding upload events...")
    all_files = db.query(File).all()
    file_ids = [f.id for f in all_files] if all_files else []

    for day_offset in range(25):
        day = now - timedelta(days=day_offset)
        for _ in range(random.randint(3, 10)):
            ts = day - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            db.add(
                AnalyticsEvent(
                    event_type=AnalyticsEventType.UPLOAD,
                    user_id=random.choice(user_ids),
                    file_id=random.choice(file_ids) if file_ids else None,
                    status=AnalyticsEventStatus.SUCCESS,
                    ip_address=random.choice(IPS)[0],
                    created_at=ts,
                )
            )
            events_added += 1

    # ═══ Step 5: DOWNLOAD events ═══
    print("  → Seeding download events...")
    for day_offset in range(20):
        day = now - timedelta(days=day_offset)
        for _ in range(random.randint(10, 35)):
            ts = day - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            db.add(
                AnalyticsEvent(
                    event_type=AnalyticsEventType.DOWNLOAD,
                    user_id=random.choice(user_ids),
                    file_id=random.choice(file_ids) if file_ids else None,
                    status=AnalyticsEventStatus.SUCCESS,
                    created_at=ts,
                )
            )
            events_added += 1

    # ═══ Step 6: SHARE events (spread across users for department donut) ═══
    print("  → Seeding share events...")
    for _ in range(120):
        ts = now - timedelta(days=random.randint(0, 30))
        db.add(
            AnalyticsEvent(
                event_type=AnalyticsEventType.SHARE,
                user_id=random.choice(user_ids),
                file_id=random.choice(file_ids) if file_ids else None,
                status=AnalyticsEventStatus.SUCCESS,
                created_at=ts,
            )
        )
        events_added += 1

    # ═══ Step 7: SECURITY events — for the timeline ═══
    print("  → Seeding security events...")
    for i, preset in enumerate(SEC_EVENT_PRESETS):
        ts = now - timedelta(hours=i * 4)
        db.add(
            AnalyticsEvent(
                event_type=AnalyticsEventType.SECURITY,
                user_id=random.choice(user_ids),
                status=preset["status"],
                ip_address=random.choice(IPS)[0],
                event_metadata={
                    "severity_key": preset["severity_key"],
                    "label": preset["label"],
                    "detail": preset["detail"],
                    "target": preset["target"],
                    "attempts": preset["attempts"],
                },
                created_at=ts,
            )
        )
        events_added += 1

    # ═══ Step 8: Unauthorized attempts ═══
    print("  → Seeding unauthorized attempts...")
    for preset in UNAUTH_PRESETS:
        ip, city, country = random.choice(IPS)
        ts = now - timedelta(hours=preset["hours_ago"])
        event_type = (
            AnalyticsEventType.SECURITY
            if preset["blocked"]
            else AnalyticsEventType.LOGIN
        )
        db.add(
            AnalyticsEvent(
                event_type=event_type,
                user_id=random.choice(user_ids),
                status=AnalyticsEventStatus.FAILED,
                ip_address=ip,
                city=city,
                country=country,
                event_metadata={
                    "severity_key": (
                        "brute_force" if preset["blocked"] else "login_failed"
                    ),
                    "target": preset["target"],
                    "attempts": preset["attempts"],
                },
                created_at=ts,
            )
        )
        events_added += 1

    # ═══ Step 9: Create share links ═══
    print("  → Creating share links...")
    shares_added = _seed_demo_shares(db, user_ids, file_ids)

    # ═══ Step 10: Enable MFA for some users (for MFA Adoption card) ═══
    print("  → Setting MFA on some demo users...")
    mfa_count = _seed_mfa_data(db, user_ids)

    db.commit()

    # ═══ Summary ═══
    print("")
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║           DEMO DATA SEED COMPLETE                 ║")
    print("  ╠═══════════════════════════════════════════════════╣")
    print(
        f"  ║  ✓ Users seeded:       {len(demo_user_ids):>4}                        ║"
    )
    print(f"  ║  ✓ Files seeded:       {files_added:>4}                        ║")
    print(f"  ║  ✓ Events seeded:      {events_added:>4}                        ║")
    print(f"  ║  ✓ Share links:        {shares_added:>4}                        ║")
    print(f"  ║  ✓ MFA-enabled users:  {mfa_count:>4}                        ║")
    print("  ╚═══════════════════════════════════════════════════╝")


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════


def _seed_demo_users(db: Session) -> list:
    """
    Create demo users if they don't exist.
    Uses bcrypt directly to avoid import dependencies.
    """
    import bcrypt

    def _make_hash(password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    demo_ids = []
    for user_data in DEMO_USERS:
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            demo_ids.append(existing.id)
            continue

        try:
            # Try to create with common User model fields
            new_user = User(
                name=user_data["name"],
                email=user_data["email"],
                hashed_password=_make_hash("Demo@1234"),  # ✅ Fixed field name
                role="user",
                plan="free",
                mfa_enabled=False,
                storage_used=random.randint(100_000_000, 3_000_000_000),
                storage_quota=5_368_709_120,
                is_active=True,
            )
            db.add(new_user)
            db.flush()
            demo_ids.append(new_user.id)
            print(f"    ✓ Created demo user: {user_data['email']}")
        except Exception as e:
            # If failed (e.g., different field names), skip that user
            db.rollback()
            print(f"    ⚠ Skipped {user_data['email']}: {str(e)[:80]}")

    return demo_ids


def _seed_demo_files(db: Session, user_ids: list) -> int:
    """Create demo files with varied types."""
    if not user_ids:
        return 0

    added = 0
    now = datetime.now(timezone.utc)

    for i, (filename, ext, size) in enumerate(DEMO_FILES):
        # Check if similar file already exists
        existing = db.query(File).filter(File.original_name == filename).first()
        if existing:
            continue

        try:
            days_ago = random.randint(0, 90)
            created_at = now - timedelta(days=days_ago)

            new_file = File(
                original_name=filename,
                stored_name=f"demo_{i}_{filename}",
                size=size,
                mimetype=_get_mimetype(ext),  # ✅ Fixed field name
                encrypted=False,
                hash_sha256=f"demo_hash_{i}_{filename}",
                version=1,
                owner_id=random.choice(user_ids),
                is_deleted=False,
                download_count=random.randint(0, 50),
                created_at=created_at,
            )
            db.add(new_file)
            added += 1
        except Exception as e:
            print(f"    ⚠ Could not create file {filename}: {e}")

    db.flush()
    return added


def _seed_demo_shares(db: Session, user_ids: list, file_ids: list) -> int:
    """Create some share links for top shared files."""
    if not user_ids or not file_ids:
        return 0

    added = 0
    now = datetime.now(timezone.utc)

    # Create 10-15 share links
    for _ in range(random.randint(10, 15)):
        try:
            new_share = ShareLink(
                file_id=random.choice(file_ids),
                created_by=random.choice(user_ids),
                token=f"demo_{random.randint(100000, 999999)}",
                access_count=random.randint(0, 50),
                is_active=random.choice([True, True, True, False]),  # 75% active
                created_at=now - timedelta(days=random.randint(0, 60)),
            )
            db.add(new_share)
            added += 1
        except Exception as e:
            pass  # skip if schema mismatch

    return added


def _seed_mfa_data(db: Session, user_ids: list) -> int:
    """
    Enable MFA on ~40% of DEMO users only (not existing real users).
    Safe: Only affects demo users created by this seed script.
    """
    if not user_ids:
        return 0

    mfa_count = 0
    try:
        # Only enable MFA on DEMO users (identified by email @demo.com)
        demo_emails = [u["email"] for u in DEMO_USERS]
        demo_users_in_db = db.query(User).filter(User.email.in_(demo_emails)).all()

        if not demo_users_in_db:
            return 0

        # Enable MFA on 40% of demo users only
        users_to_enable = random.sample(
            demo_users_in_db, k=max(1, len(demo_users_in_db) * 40 // 100)
        )

        for user in users_to_enable:
            if hasattr(user, "mfa_enabled"):
                user.mfa_enabled = True
                mfa_count += 1

        print(f"    ✓ MFA enabled on {mfa_count} DEMO users (real users untouched)")
    except Exception as e:
        print(f"    ⚠ MFA seed skipped: {str(e)[:80]}")

    return mfa_count


# ═══════════════════════════════════════════════════════════════════════
# CLEANUP FUNCTION (For removing demo data before submission!)
# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
# CLEANUP FUNCTION — Run BEFORE submission!
# ═══════════════════════════════════════════════════════════════════════


def cleanup_demo_data(db: Session):
    """
    ⚠️ Removes ALL demo data added by seed_demo_data().

    Usage:
        cd server
        python
        >>> from src.database.core import SessionLocal
        >>> from src.analytics.seed.seed_demo_data import cleanup_demo_data
        >>> db = SessionLocal()
        >>> cleanup_demo_data(db)
        >>> db.close()
        >>> exit()
    """
    print("")
    print("  🗑  Cleaning up demo data...")
    print("")

    # Get demo user IDs
    demo_emails = [u["email"] for u in DEMO_USERS]
    demo_users = db.query(User).filter(User.email.in_(demo_emails)).all()
    demo_user_ids = [u.id for u in demo_users]

    # Get demo file IDs (both by name AND owned by demo users)
    demo_filenames = [f[0] for f in DEMO_FILES]
    demo_files = (
        db.query(File)
        .filter(
            (File.original_name.in_(demo_filenames))
            | (File.owner_id.in_(demo_user_ids) if demo_user_ids else False)
        )
        .all()
    )
    demo_file_ids = [f.id for f in demo_files]

    # 1. Delete share links from demo users OR pointing to demo files
    shares_deleted = 0
    if demo_user_ids or demo_file_ids:
        shares_deleted = (
            db.query(ShareLink)
            .filter(
                (ShareLink.created_by.in_(demo_user_ids) if demo_user_ids else False)
                | (ShareLink.file_id.in_(demo_file_ids) if demo_file_ids else False)
            )
            .delete(synchronize_session=False)
        )

    # 2. Delete analytics events from demo users OR pointing to demo files
    events_deleted = 0
    if demo_user_ids or demo_file_ids:
        events_deleted = (
            db.query(AnalyticsEvent)
            .filter(
                (AnalyticsEvent.user_id.in_(demo_user_ids) if demo_user_ids else False)
                | (
                    AnalyticsEvent.file_id.in_(demo_file_ids)
                    if demo_file_ids
                    else False
                )
            )
            .delete(synchronize_session=False)
        )

    # 3. Also delete events with brute_force or demo severity keys
    extra_events_deleted = (
        db.query(AnalyticsEvent)
        .filter(
            AnalyticsEvent.event_metadata.op("->>")("severity_key").in_(
                [
                    "brute_force",
                    "new_device",
                    "external_link",
                    "unusual_access",
                    "admin_role",
                    "login_failed",
                ]
            )
        )
        .delete(synchronize_session=False)
    )
    events_deleted += extra_events_deleted

    # 4. Delete demo files
    files_deleted = 0
    if demo_file_ids:
        files_deleted = (
            db.query(File)
            .filter(File.id.in_(demo_file_ids))
            .delete(synchronize_session=False)
        )

    # 5. Delete demo users (last, after their data is cleared)
    users_deleted = 0
    if demo_user_ids:
        users_deleted = (
            db.query(User)
            .filter(User.id.in_(demo_user_ids))
            .delete(synchronize_session=False)
        )

    db.commit()

    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║        DEMO DATA CLEANUP COMPLETE                 ║")
    print("  ╠═══════════════════════════════════════════════════╣")
    print(f"  ║  ✓ Users deleted:      {users_deleted:>4}                        ║")
    print(f"  ║  ✓ Files deleted:      {files_deleted:>4}                        ║")
    print(f"  ║  ✓ Events deleted:     {events_deleted:>4}                        ║")
    print(f"  ║  ✓ Share links:        {shares_deleted:>4}                        ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print("")
    print("  ✨ Database is clean and ready for submission!")
    print("")


def nuclear_cleanup(db: Session):
    """
    ⚠️ NUCLEAR OPTION: Deletes ALL analytics events + demo users/files.
    Use ONLY if you want a completely fresh database.
    """
    print("")
    print("  💣 NUCLEAR CLEANUP — Removing ALL analytics data...")
    print("")

    # Delete all analytics events
    events_deleted = db.query(AnalyticsEvent).delete(synchronize_session=False)

    # Delete all share links
    shares_deleted = db.query(ShareLink).delete(synchronize_session=False)

    # Delete demo users only (keep your real users)
    demo_emails = [u["email"] for u in DEMO_USERS]
    users_deleted = (
        db.query(User)
        .filter(User.email.in_(demo_emails))
        .delete(synchronize_session=False)
    )

    # Delete demo files only
    demo_filenames = [f[0] for f in DEMO_FILES]
    files_deleted = (
        db.query(File)
        .filter(File.original_name.in_(demo_filenames))
        .delete(synchronize_session=False)
    )

    db.commit()

    print(f"  ✓ ALL Events deleted:  {events_deleted}")
    print(f"  ✓ ALL Shares deleted:  {shares_deleted}")
    print(f"  ✓ Demo Users deleted:  {users_deleted}")
    print(f"  ✓ Demo Files deleted:  {files_deleted}")
    print("")
    print("  ✨ Database is completely clean!")
