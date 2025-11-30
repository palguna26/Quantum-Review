"""Repository schemas."""
from typing import Optional
from pydantic import BaseModel


class RepoSummaryResponse(BaseModel):
    """Repo summary response schema matching frontend TypeScript interface."""
    repo_full_name: str
    owner: str
    name: str
    health_score: int
    is_installed: bool
    pr_count: int
    issue_count: int
    last_activity: Optional[str] = None
    
    class Config:
        from_attributes = True

