"""User model."""
from sqlalchemy import Column, String, BigInteger
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model representing a GitHub user."""
    __tablename__ = "users"
    
    github_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    github_token = Column(String(1024), nullable=True)  # OAuth token for API access
    
    # Relationships
    repo_roles = relationship("UserRepoRole", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

