"""Issue schemas."""
from typing import List, Optional
from pydantic import BaseModel


class ChecklistItemResponse(BaseModel):
    """Checklist item response schema."""
    id: str
    text: str
    required: bool
    status: str  # 'pending', 'passed', 'failed', 'skipped'
    linked_tests: List[str] = []
    
    class Config:
        from_attributes = True


class ChecklistSummary(BaseModel):
    """Checklist summary schema."""
    total: int
    passed: int
    failed: int
    pending: int


class IssueResponse(BaseModel):
    """Issue response schema matching frontend TypeScript interface."""
    issue_number: int
    title: str
    status: str  # 'open', 'processing', 'completed'
    created_at: str
    updated_at: str
    checklist_summary: ChecklistSummary
    checklist: Optional[List[ChecklistItemResponse]] = None
    github_url: str
    
    class Config:
        from_attributes = True

