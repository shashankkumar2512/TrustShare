# server/src/analytics/utils/time_helpers.py
"""
Reusable time formatting helpers used across analytics queries.
Cross-platform safe (works on Windows, Linux, and Mac).
"""

from datetime import datetime, timezone


def relative_time(dt: datetime) -> str:
    """
    Convert a datetime to human-readable relative time.
    Examples: 'Just now', '5 min ago', '3 hrs ago', 'Yesterday', '3 days ago', 'Jan 6'
    
    ✅ Cross-platform safe — uses manual day formatting.
    """
    if dt is None:
        return "Unknown"

    # Make sure both datetimes are timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now   = datetime.now(timezone.utc)
    delta = now - dt
    secs  = delta.total_seconds()

    if secs < 60:
        return "Just now"
    if secs < 3600:
        mins = int(secs / 60)
        return f"{mins} min ago"
    if secs < 86400:
        hrs = int(secs / 3600)
        return f"{hrs} hr{'s' if hrs > 1 else ''} ago"
    if delta.days == 1:
        return "Yesterday"
    if delta.days < 7:
        return f"{delta.days} days ago"

    # Cross-platform safe date format 
    return f"{dt.strftime('%b')} {dt.day}"


def format_short_datetime(dt: datetime) -> str:
    """
    Format a datetime as 'Jan 6, 9:14 AM' (cross-platform safe).
    """
    if dt is None:
        return ""

    # Manual formatting — no platform-specific specifiers
    day = dt.day
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    month = dt.strftime("%b")
    return f"{month} {day}, {hour}:{dt.minute:02d} {ampm}"


def format_short_date(dt: datetime) -> str:
    """
    Format a datetime as 'Jan 6' (cross-platform safe).
    """
    if dt is None:
        return ""
    return f"{dt.strftime('%b')} {dt.day}"


def format_long_date(dt: datetime) -> str:
    """
    Format a datetime as 'January 6, 2024' (cross-platform safe).
    """
    if dt is None:
        return ""
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


def format_full_datetime(dt: datetime) -> str:
    """
    Format a datetime as 'Jan 6, 2024 at 9:14 AM' (cross-platform safe).
    """
    if dt is None:
        return ""
    
    day = dt.day
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    month = dt.strftime("%b")
    return f"{month} {day}, {dt.year} at {hour}:{dt.minute:02d} {ampm}"


def format_time_only(dt: datetime) -> str:
    """
    Format just the time as '9:14 AM' (cross-platform safe).
    """
    if dt is None:
        return ""
    
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.minute:02d} {ampm}"


def format_iso_date(dt: datetime) -> str:
    """
    Format a datetime as '2024-01-06' (ISO format, cross-platform safe).
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d")


def format_iso_datetime(dt: datetime) -> str:
    """
    Format a datetime as '2024-01-06 14:30:00' (ISO format, cross-platform safe).
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def humanize_bytes(size_bytes: int) -> str:
    """
    Convert bytes to human-readable size.
    Examples: '1.5 MB', '2.3 GB', '500 KB'
    """
    if size_bytes is None or size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            if unit == 'B':
                return f"{int(size_bytes)} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    
    return f"{size_bytes:.1f} PB"


def humanize_number(num: int) -> str:
    """
    Format numbers with K/M/B suffixes.
    Examples: 1500 → '1.5K', 1000000 → '1M'
    """
    if num is None:
        return "0"
    
    if abs(num) < 1000:
        return str(num)
    if abs(num) < 1_000_000:
        return f"{num/1000:.1f}K".replace(".0K", "K")
    if abs(num) < 1_000_000_000:
        return f"{num/1_000_000:.1f}M".replace(".0M", "M")
    return f"{num/1_000_000_000:.1f}B".replace(".0B", "B")