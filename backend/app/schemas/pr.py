"""Pull request schemas."""
from typing import List, Optional
from pydantic import BaseModel


class TestResultResponse(BaseModel):
    """Test result response schema."""
    test_id: str
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    checklist_ids: List[str] = []


class CodeHealthIssueResponse(BaseModel):
    """Code health issue response schema."""
    id: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class SuggestedTestResponse(BaseModel):
    """Suggested test response schema."""
    test_id: str
    name: str
    framework: str
    target: str
    checklist_ids: List[str] = []
    snippet: str
    reasoning: Optional[str] = None


class CoverageAdviceResponse(BaseModel):
    """Coverage advice response schema."""
    file_path: str
    lines: List[int] = []
    suggestion: str


class PRDetailResponse(BaseModel):
    """PR detail response schema matching frontend TypeScript interface."""
    pr_number: int
    title: str
    author: str
    created_at: str
    health_score: int
    validation_status: str  # 'pending', 'validated', 'needs_work'
    manifest: Optional[dict] = None
    test_results: List[TestResultResponse] = []
    code_health: List[CodeHealthIssueResponse] = []
    coverage_advice: List[CoverageAdviceResponse] = []
    suggested_tests: List[SuggestedTestResponse] = []
    github_url: str
    
    class Config:
        from_attributes = True

