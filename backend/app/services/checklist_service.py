"""Checklist generation service."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.repo import Repo
from app.models.issue import Issue, ChecklistItem
from app.models.user import UserRepoRole
from app.models.audit import Notification
from app.utils.parser import extract_acceptance_criteria
from app.services.github_auth import get_github_api_client_async
from app.config import get_settings
from app.logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)
settings = get_settings()


async def generate_and_save_checklist(
    issue_payload: Dict[str, Any],
    db: AsyncSession
) -> None:
    """Generate checklist from issue and save to database.
    
    Args:
        issue_payload: GitHub webhook payload for issue event
        db: Database session
    """
    issue_data = issue_payload.get("issue", {})
    repo_data = issue_payload.get("repository", {})
    
    issue_number = issue_data.get("number")
    repo_full_name = repo_data.get("full_name")
    
    if not issue_number or not repo_full_name:
        logger.error("Missing issue number or repo full name in payload")
        return
    
    # Get or create repo
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo:
        logger.warning(f"Repo not found: {repo_full_name}")
        return
    
    # Get or create issue
    issue_result = await db.execute(
        select(Issue).where(
            Issue.repo_id == repo.id,
            Issue.issue_number == issue_number
        )
    )
    issue = issue_result.scalar_one_or_none()
    
    if not issue:
        issue = Issue(
            repo_id=repo.id,
            issue_number=issue_number,
            title=issue_data.get("title", ""),
            body=issue_data.get("body", ""),
            status="pending",
        )
        db.add(issue)
        await db.flush()
    else:
        # Update existing issue
        issue.title = issue_data.get("title", issue.title)
        issue.body = issue_data.get("body", issue.body)
    
    # Extract acceptance criteria
    checklist_data = extract_acceptance_criteria(issue.body or "")
    
    # Save checklist JSON
    issue.checklist_json = checklist_data
    
    # Delete existing checklist items
    await db.execute(
        select(ChecklistItem).where(ChecklistItem.issue_id == issue.id)
    )
    existing_items = await db.execute(
        select(ChecklistItem).where(ChecklistItem.issue_id == issue.id)
    )
    for item in existing_items.scalars():
        await db.delete(item)
    
    # Create checklist items
    for item_data in checklist_data:
        checklist_item = ChecklistItem(
            issue_id=issue.id,
            item_id=item_data["id"],
            text=item_data["text"],
            required="true" if item_data.get("required", True) else "false",
            status="pending",
            linked_test_ids=[],
        )
        db.add(checklist_item)
    
    issue.status = "processed"
    await db.commit()
    
    logger.info(f"Generated checklist for issue #{issue_number} in {repo_full_name}")
    # If MongoDB is configured, also upsert the checklist document to Mongo
    if settings.MONGODB_URI:
        try:
            from app.adapters.mongo import get_collection
            coll = get_collection("checklists")
            doc = {
                "issue_id": issue.id,
                "issue_number": issue_number,
                "repo_full_name": repo_full_name,
                "title": issue.title,
                "checklist": checklist_data,
                "generated_at": datetime.utcnow(),
            }
            # upsert by issue_id
            await coll.update_one({"issue_id": issue.id}, {"$set": doc}, upsert=True)
        except Exception as e:
            logger.warning(f"Failed to write checklist to MongoDB: {e}")
    
    # Post comment on GitHub (optional)
    if repo.installation_id and checklist_data:
        try:
            client = await get_github_api_client_async(repo.installation_id)
            comment_body = "## Generated Checklist\n\n"
            for item in checklist_data:
                required_marker = "✅" if item.get("required") else "⚪"
                comment_body += f"{required_marker} {item['id']}: {item['text']}\n"
            
            await client.post(
                f"/repos/{repo_full_name}/issues/{issue_number}/comments",
                json={"body": comment_body},
            )
            await client.aclose()
        except Exception as e:
            logger.warning(f"Failed to post checklist comment: {e}")
    
    # Create notifications for repo managers
    managers_result = await db.execute(
        select(UserRepoRole.user_id)
        .where(UserRepoRole.repo_id == repo.id)
        .where(UserRepoRole.role.in_(["admin", "maintainer", "manager"]))
    )
    manager_ids = [row[0] for row in managers_result.all()]
    
    for user_id in manager_ids:
        notification = Notification(
            user_id=user_id,
            repo_id=repo.id,
            kind="checklist_ready",
            payload={
                "issue_number": issue_number,
                "issue_title": issue.title,
                "checklist_count": len(checklist_data),
            },
            read=False,
        )
        db.add(notification)
    
    await db.commit()

