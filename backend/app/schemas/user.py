"""User schemas."""
from typing import List, Optional
from pydantic import BaseModel


class UserResponse(BaseModel):
    """User response schema matching frontend TypeScript interface."""
    id: str
    login: str
    avatar_url: str
    name: Optional[str] = None
    email: Optional[str] = None
    managed_repos: List[str] = []
    
    class Config:
        from_attributes = True

