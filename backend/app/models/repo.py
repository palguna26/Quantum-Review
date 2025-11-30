"""Repository models."""
from sqlalchemy import Column, String, BigInteger, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    """Organization model representing a GitHub organization."""
    __tablename__ = "organizations"
    
    github_org_id = Column(BigInteger, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Relationships
    repos = relationship("Repo", back_populates="owner_org", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class Repo(Base, TimestampMixin):
    """Repository model."""
    __tablename__ = "repos"
    
    repo_full_name = Column(String(512), unique=True, nullable=False, index=True)
    installation_id = Column(BigInteger, nullable=True, index=True)
    is_installed = Column(Boolean, default=False, nullable=False)
    owner_org_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    owner_org = relationship("Organization", back_populates="repos")
    user_roles = relationship("UserRepoRole", back_populates="repo", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="repo", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repo", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="repo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repo(id={self.id}, repo_full_name={self.repo_full_name})>"


class UserRepoRole(Base, TimestampMixin):
    """User repository role model."""
    __tablename__ = "user_repo_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'admin', 'maintainer', 'viewer', 'manager'
    
    # Relationships
    user = relationship("User", back_populates="repo_roles")
    repo = relationship("Repo", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRepoRole(user_id={self.user_id}, repo_id={self.repo_id}, role={self.role})>"

