"""Issue models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Issue(Base, TimestampMixin):
    """Issue model."""
    __tablename__ = "issues"
    
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_number = Column(Integer, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    checklist_json = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'processed', 'needs_attention'
    
    # Relationships
    repo = relationship("Repo", back_populates="issues")
    checklist_items = relationship("ChecklistItem", back_populates="issue", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Issue(id={self.id}, issue_number={self.issue_number}, repo_id={self.repo_id})>"


class ChecklistItem(Base, TimestampMixin):
    """Checklist item model."""
    __tablename__ = "checklist_items"
    
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(50), nullable=False)  # C1, C2, etc.
    text = Column(Text, nullable=False)
    required = Column(String(50), nullable=False, default="false")  # Store as string for JSON compatibility
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'passed', 'failed', 'skipped'
    linked_test_ids = Column(JSON, nullable=True)  # JSONB array of test IDs
    
    # Relationships
    issue = relationship("Issue", back_populates="checklist_items")
    
    def __repr__(self):
        return f"<ChecklistItem(id={self.id}, item_id={self.item_id}, issue_id={self.issue_id})>"

