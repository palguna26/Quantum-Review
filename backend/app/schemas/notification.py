"""Notification schemas."""
from typing import Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Notification response schema matching frontend TypeScript interface."""
    id: str
    type: str  # 'info', 'warning', 'error', 'success'
    message: str
    repo_full_name: Optional[str] = None
    created_at: str
    read: bool
    
    class Config:
        from_attributes = True

