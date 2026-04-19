"""Tests for user_service — one test is currently FAILING."""

import pytest
from user_service import validate_email, format_display_name, calculate_age, sanitize_username


def test_basic_email():
    assert validate_email("user@example.com") is True


def test_plus_email():
    """This test FAILS — the regex doesn't handle + in local part."""
    assert validate_email("user+tag@example.com") is True


def test_invalid_email():
    assert validate_email("not-an-email") is False


def test_display_name():
    assert format_display_name("  john  ", "doe") == "John Doe"


def test_age():
    from datetime import datetime
    assert calculate_age(2000) == datetime.now().year - 2000


def test_sanitize():
    assert sanitize_username("Hello World!@#") == "helloworld"
