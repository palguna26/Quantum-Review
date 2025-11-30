"""Tests for diff parsing utilities."""
import pytest
from app.utils.parser import extract_changed_symbols


def test_extract_changed_symbols_python():
    """Test extracting Python symbols from diff."""
    diff = """
    diff --git a/src/auth.py b/src/auth.py
    +def login_user(email, password):
    +    pass
    +class AuthService:
    +    pass
    """
    symbols = extract_changed_symbols(diff, "src/auth.py")
    assert "login_user" in symbols
    assert "AuthService" in symbols


def test_extract_changed_symbols_javascript():
    """Test extracting JavaScript symbols from diff."""
    diff = """
    diff --git a/src/auth.js b/src/auth.js
    +function loginUser(email, password) {
    +}
    +class AuthService {
    +}
    +const authHelper = function() {}
    """
    symbols = extract_changed_symbols(diff, "src/auth.js")
    assert "loginUser" in symbols
    assert "AuthService" in symbols
    assert "authHelper" in symbols


def test_extract_changed_symbols_no_symbols():
    """Test with diff containing no symbols."""
    diff = """
    diff --git a/README.md b/README.md
    +Some documentation text
    """
    symbols = extract_changed_symbols(diff, "README.md")
    assert len(symbols) == 0

