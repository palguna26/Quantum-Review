"""Notification service."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.audit import Notification
from app.models.user import User
from app.logging_config import get_logger

logger = get_logger(__name__)


async def get_user_notifications(
    user_id: int,
    db: AsyncSession,
    limit: int = 50
) -> List[Notification]:
    """Get notifications for a user.
    
    Args:
        user_id: User ID
        db: Database session
        limit: Maximum number of notifications to return
    
    Returns:
        List of notifications
    """
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_notification_read(
    notification_id: int,
    user_id: int,
    db: AsyncSession
) -> Optional[Notification]:
    """Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        user_id: User ID (for verification)
        db: Database session
    
    Returns:
        Updated notification or None if not found
    """
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if notification:
        notification.read = True
        await db.commit()
        await db.refresh(notification)
    
    return notification

