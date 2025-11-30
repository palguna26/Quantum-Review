"""Integration tests."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.services.checklist_service import generate_and_save_checklist
from app.models.repo import Repo
from app.models.issue import Issue, ChecklistItem

# Use test database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/quantumreview_test"


@pytest.mark.asyncio
async def test_webhook_issue_opened_creates_checklist():
    """Integration test: webhook issues.opened creates checklist in DB."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as db:
        # Create test repo
        repo = Repo(
            repo_full_name="test/repo",
            is_installed=True,
            installation_id=12345,
        )
        db.add(repo)
        await db.flush()
        
        # Simulate webhook payload
        payload = {
            "action": "opened",
            "issue": {
                "number": 1,
                "title": "Test Issue",
                "body": """
                ## Acceptance Criteria
                
                - First requirement
                - Second requirement [optional]
                - Third requirement
                """,
            },
            "repository": {
                "full_name": "test/repo",
            },
        }
        
        # Generate checklist
        await generate_and_save_checklist(payload, db)
        
        # Verify issue created
        from sqlalchemy import select
        issue_result = await db.execute(
            select(Issue).where(Issue.issue_number == 1)
        )
        issue = issue_result.scalar_one_or_none()
        assert issue is not None
        assert issue.status == "processed"
        
        # Verify checklist items created
        items_result = await db.execute(
            select(ChecklistItem).where(ChecklistItem.issue_id == issue.id)
        )
        items = list(items_result.scalars().all())
        assert len(items) == 3
        assert items[0].item_id == "C1"
        assert items[1].required == "false"  # Optional item
        assert items[2].required == "true"
    
    await engine.dispose()

