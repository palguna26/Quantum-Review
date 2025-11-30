"""Code health model."""
from sqlalchemy import Column, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class CodeHealth(Base, TimestampMixin):
    """Code health model."""
    __tablename__ = "code_health"
    
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    score = Column(Integer, nullable=False)  # 0-100
    findings = Column(JSON, nullable=True)  # JSONB array of findings
    
    # Relationships
    pr = relationship("PullRequest", back_populates="code_health")
    
    def __repr__(self):
        return f"<CodeHealth(id={self.id}, pr_id={self.pr_id}, score={self.score})>"

