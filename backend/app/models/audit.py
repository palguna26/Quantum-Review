"""Audit and notification models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    """Report model."""
    __tablename__ = "reports"
    
    pr_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    report_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Relationships
    pr = relationship("PullRequest", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, pr_id={self.pr_id})>"


class Notification(Base, TimestampMixin):
    """Notification model."""
    __tablename__ = "notifications"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(100), nullable=False)  # 'checklist_ready', 'pr_validated', 'repo_event', etc.
    payload = Column(JSON, nullable=True)  # JSONB
    read = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    repo = relationship("Repo", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, kind={self.kind}, user_id={self.user_id}, read={self.read})>"


class AuditLog(Base, TimestampMixin):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # 'flag_for_merge', 'regenerate_checklist', etc.
    target_type = Column(String(50), nullable=False)  # 'pr', 'issue', 'repo', etc.
    target_id = Column(Integer, nullable=False, index=True)
    details = Column(JSON, nullable=True)  # JSONB
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, target_type={self.target_type}, target_id={self.target_id})>"

