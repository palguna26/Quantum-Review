"""Tests for parser utilities."""
import pytest
from app.utils.parser import extract_acceptance_criteria


def test_extract_acceptance_criteria_with_section():
    """Test extracting acceptance criteria from explicit section."""
    text = """
    ## Acceptance Criteria
    
    - User can login with email and password
    - User receives error for invalid credentials
    - User can reset password
    """
    result = extract_acceptance_criteria(text)
    assert len(result) == 3
    assert result[0]["id"] == "C1"
    assert "login" in result[0]["text"].lower()
    assert result[0]["required"] is True


def test_extract_acceptance_criteria_without_section():
    """Test extracting from first bullet list when no section."""
    text = """
    This is an issue description.
    
    - First requirement
    - Second requirement [optional]
    - Third requirement
    """
    result = extract_acceptance_criteria(text)
    assert len(result) >= 2
    assert result[0]["required"] is True
    assert result[1]["required"] is False


def test_extract_acceptance_criteria_with_required_tags():
    """Test parsing [required] and [optional] tags."""
    text = """
    ## Acceptance Criteria
    
    - Required item [required]
    - Optional item [optional]
    - Another required item
    """
    result = extract_acceptance_criteria(text)
    assert len(result) == 3
    assert result[0]["required"] is True
    assert result[1]["required"] is False
    assert result[2]["required"] is True


def test_extract_acceptance_criteria_with_custom_tags():
    """Test extracting custom tags from items."""
    text = """
    ## Acceptance Criteria
    
    - Item with [tag1] and [tag2] tags
    - Another item [tag3]
    """
    result = extract_acceptance_criteria(text)
    assert len(result) == 2
    assert "tag1" in result[0]["tags"]
    assert "tag2" in result[0]["tags"]
    assert "tag3" in result[1]["tags"]


def test_extract_acceptance_criteria_empty_text():
    """Test with empty text."""
    result = extract_acceptance_criteria("")
    assert result == []


def test_extract_acceptance_criteria_no_bullets():
    """Test with text but no bullet points."""
    text = "This is just regular text without any bullets."
    result = extract_acceptance_criteria(text)
    # Should return empty or handle gracefully
    assert isinstance(result, list)

