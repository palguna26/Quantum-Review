"""Pull request models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class PullRequest(Base, TimestampMixin):
    """Pull request model."""
    __tablename__ = "pull_requests"
    
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    head_sha = Column(String(40), nullable=True)  # Git SHA
    linked_issue_id = Column(Integer, ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    test_manifest = Column(JSON, nullable=True)  # JSONB
    validation_status = Column(String(50), nullable=False, default="pending")  # 'pending', 'validated', 'needs_work'
    
    # Relationships
    repo = relationship("Repo", back_populates="pull_requests")
    linked_issue = relationship("Issue", foreign_keys=[linked_issue_id])
    test_results = relationship("TestResult", back_populates="pr", cascade="all, delete-orphan")
    code_health = relationship("CodeHealth", back_populates="pr", cascade="all, delete-orphan", uselist=False)
    reports = relationship("Report", back_populates="pr", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PullRequest(id={self.id}, pr_number={self.pr_number}, repo_id={self.repo_id})>"


class TestResult(Base, TimestampMixin):
    """Test result model."""
    __tablename__ = "test_results"
    
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(String(255), nullable=False, index=True)
    name = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False)  # 'passed', 'failed', 'skipped'
    log_url = Column(String(512), nullable=True)
    checklist_ids = Column(JSON, nullable=True)  # JSONB array of checklist item IDs
    
    # Relationships
    pr = relationship("PullRequest", back_populates="test_results")
    
    def __repr__(self):
        return f"<TestResult(id={self.id}, test_id={self.test_id}, pr_id={self.pr_id}, status={self.status})>"

