"""Simple user service with a known bug for A/B testing."""

import re
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format. BUG: rejects valid emails with + in local part."""
    pattern = r'^[a-zA-Z0-9.]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_display_name(first: str, last: str) -> str:
    """Format a user's display name."""
    return f"{first.strip().title()} {last.strip().title()}"


def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year."""
    return datetime.now().year - birth_year


def sanitize_username(username: str) -> str:
    """Strip special characters, lowercase."""
    return re.sub(r'[^a-zA-Z0-9_]', '', username).lower()
