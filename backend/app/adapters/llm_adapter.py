"""LLM adapter (stubbed for MVP)."""
from typing import Optional, List, Dict, Any
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def generate_suggested_tests(
    code_diff: str,
    checklist_items: List[Dict[str, Any]],
    file_path: str
) -> List[Dict[str, Any]]:
    """Generate suggested tests (stubbed - feature flagged off for MVP).
    
    Args:
        code_diff: Code diff text
        checklist_items: Checklist items to cover
        file_path: File path
    
    Returns:
        List of suggested tests (empty for MVP)
    """
    if not settings.LLM_PROVIDER or not settings.LLM_API_KEY:
        logger.debug("LLM integration disabled - returning empty suggestions")
        return []
    
    # Stub implementation - would call LLM API here
    return []


async def analyze_coverage(
    coverage_data: Dict[str, Any],
    changed_files: List[str]
) -> List[Dict[str, Any]]:
    """Analyze coverage gaps (stubbed - feature flagged off for MVP).
    
    Args:
        coverage_data: Coverage report data
        changed_files: List of changed file paths
    
    Returns:
        List of coverage advice (empty for MVP)
    """
    if not settings.LLM_PROVIDER or not settings.LLM_API_KEY:
        logger.debug("LLM integration disabled - returning empty coverage advice")
        return []
    
    # Stub implementation - would call LLM API here
    return []

