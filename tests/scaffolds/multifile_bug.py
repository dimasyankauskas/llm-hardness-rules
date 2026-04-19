"""
Multi-file project with a DECEPTIVE bug.
The obvious fix (in validator.py) doesn't work — the real root cause is in config.py.
Tests AP-22 (Critic-Refiner Loop): agent must fail once, pivot, find real cause.
"""

# === config.py ===
CONFIG_PY = '''\
"""Application configuration."""

# Email validation settings
EMAIL_SETTINGS = {
    "max_length": 254,
    "allowed_special_chars": ".-_",  # BUG: missing "+" — this is the REAL root cause
    "require_tld": True,
    "min_local_length": 1,
}

# User settings
USER_SETTINGS = {
    "max_username_length": 32,
    "allow_unicode": False,
}
'''

# === validator.py ===
VALIDATOR_PY = '''\
"""Email and input validation using config-driven rules."""

import re
from config import EMAIL_SETTINGS


def validate_email(email: str) -> bool:
    """Validate email against config-driven rules."""
    if not email or len(email) > EMAIL_SETTINGS["max_length"]:
        return False

    parts = email.split("@")
    if len(parts) != 2:
        return False

    local, domain = parts

    if len(local) < EMAIL_SETTINGS["min_local_length"]:
        return False

    # Check local part against allowed special characters from config
    allowed = EMAIL_SETTINGS["allowed_special_chars"]
    pattern = f"^[a-zA-Z0-9{re.escape(allowed)}]+$"
    if not re.match(pattern, local):
        return False

    # Check domain
    if EMAIL_SETTINGS["require_tld"]:
        if "." not in domain:
            return False

    domain_pattern = r"^[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    return bool(re.match(domain_pattern, domain))


def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username or len(username) > 32:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_]+$", username))
'''

# === test_validation.py ===
TEST_VALIDATION_PY = '''\
"""Tests for validation module."""

import pytest
from validator import validate_email, validate_username


class TestEmailValidation:
    def test_basic_email(self):
        assert validate_email("user@example.com") is True

    def test_email_with_dots(self):
        assert validate_email("first.last@example.com") is True

    def test_email_with_plus(self):
        """FAILING: user+tag should be valid per RFC 5321."""
        assert validate_email("user+tag@example.com") is True

    def test_email_with_underscore(self):
        assert validate_email("user_name@example.com") is True

    def test_invalid_no_at(self):
        assert validate_email("noatsign.com") is False

    def test_invalid_no_tld(self):
        assert validate_email("user@localhost") is False

    def test_empty_email(self):
        assert validate_email("") is False

    def test_too_long(self):
        assert validate_email("a" * 250 + "@example.com") is False


class TestUsernameValidation:
    def test_valid_username(self):
        assert validate_username("john_doe123") is True

    def test_invalid_special_chars(self):
        assert validate_username("john@doe") is False

    def test_empty_username(self):
        assert validate_username("") is False
'''
