"""Background job tasks for RQ."""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.adapters.db import get_db
from app.services.checklist_service import generate_and_save_checklist
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create database session for workers
engine = create_async_engine(settings.DATABASE_URL)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """Get database session for worker."""
    return async_session_maker()


def generate_checklist(issue_payload: Dict[str, Any]) -> None:
    """Generate checklist for an issue (RQ task).
    
    Args:
        issue_payload: GitHub webhook payload for issue event
    """
    import asyncio
    
    async def _generate():
        db = await get_db_session()
        try:
            await generate_and_save_checklist(issue_payload, db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error generating checklist: {e}", exc_info=True)
            raise
        finally:
            await db.close()
    
    asyncio.run(_generate())


def generate_test_manifest(pr_payload: Dict[str, Any]) -> None:
    """Generate test manifest for a PR (RQ task).
    
    Args:
        pr_payload: GitHub webhook payload for PR event
    """
    import asyncio
    
    async def _generate():
        db = await get_db_session()
        try:
            from app.services.testgen_service import generate_and_save_manifest
            await generate_and_save_manifest(pr_payload, db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error generating test manifest: {e}", exc_info=True)
            raise
        finally:
            await db.close()
    
    asyncio.run(_generate())


def process_workflow_run(workflow_run_payload: Dict[str, Any]) -> None:
    """Process workflow run and update test results (RQ task).
    
    Args:
        workflow_run_payload: GitHub webhook payload for workflow_run event
    """
    import asyncio
    
    async def _process():
        db = await get_db_session()
        try:
            from app.services.ci_mapper import process_and_map_results
            await process_and_map_results(workflow_run_payload, db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing workflow run: {e}", exc_info=True)
            raise
        finally:
            await db.close()
    
    asyncio.run(_process())


def handle_installation(installation_payload: Dict[str, Any]) -> None:
    """Handle installation events (RQ task).
    
    Args:
        installation_payload: GitHub webhook payload for installation event
    """
    import asyncio
    
    async def _handle():
        db = await get_db_session()
        try:
                from app.services.github_auth import get_github_api_client_async
                installation_data = installation_payload.get("installation", {})
                installation_id = installation_data.get("id")
                
                if installation_payload.get("action") == "created":
                    # Fetch repositories for this installation
                    client = await get_github_api_client_async(installation_id)
                    try:
                        repos_response = await client.get("/installation/repositories")
                        repos_data = repos_response.json()
                        
                        # Create/update repos in database
                        from app.models.repo import Repo
                        from sqlalchemy import select
                        
                        for repo_data in repos_data.get("repositories", []):
                            repo_full_name = repo_data["full_name"]
                            result = await db.execute(
                                select(Repo).where(Repo.repo_full_name == repo_full_name)
                            )
                            repo = result.scalar_one_or_none()
                            
                            if repo:
                                repo.installation_id = installation_id
                                repo.is_installed = True
                            else:
                                repo = Repo(
                                    repo_full_name=repo_full_name,
                                    installation_id=installation_id,
                                    is_installed=True,
                                )
                                db.add(repo)
                        
                        await db.commit()
                        logger.info(f"Updated repos for installation {installation_id}")
                    finally:
                        await client.aclose()
                
                elif installation_payload.get("action") == "deleted":
                    # Mark repos as uninstalled
                    from app.models.repo import Repo
                    from sqlalchemy import select, update
                    
                    await db.execute(
                        update(Repo)
                        .where(Repo.installation_id == installation_id)
                        .values(is_installed=False, installation_id=None)
                    )
                    await db.commit()
                    logger.info(f"Marked repos as uninstalled for installation {installation_id}")
                    
        except Exception as e:
            await db.rollback()
            logger.error(f"Error handling installation: {e}", exc_info=True)
            raise
        finally:
            await db.close()
    
    asyncio.run(_handle())


def handle_installation_repositories(repositories_payload: Dict[str, Any]) -> None:
    """Handle installation_repositories events (RQ task).
    
    Args:
        repositories_payload: GitHub webhook payload for installation_repositories event
    """
    # Similar to handle_installation but for repository access changes
    handle_installation(repositories_payload)


def handle_pr_closed(pr_payload: Dict[str, Any]) -> None:
    """Handle PR closed event (RQ task).
    
    Args:
        pr_payload: GitHub webhook payload for PR closed event
    """
    # Placeholder - can add cleanup logic here
    logger.info(f"PR closed: {pr_payload.get('pull_request', {}).get('number')}")


def refresh_repository(payload: Dict[str, Any]) -> None:
    """Refresh repository metadata and recent activity (RQ task)."""
    import asyncio

    async def _refresh():
        db = await get_db_session()
        try:
            repo_id = payload.get("repo_id")
            repo_full_name = payload.get("repo_full_name")
            from sqlalchemy import select
            from app.models.repo import Repo
            result = await db.execute(select(Repo).where(Repo.id == repo_id))
            repo = result.scalar_one_or_none()
            if not repo:
                return
            # Optionally fetch latest metadata via GitHub API if installed
            if repo.is_installed and repo.installation_id:
                from app.services.github_auth import get_github_api_client_async
                client = await get_github_api_client_async(repo.installation_id)
                try:
                    await client.get(f"/repos/{repo_full_name}")
                finally:
                    await client.aclose()
            await db.commit()
            logger.info(f"Refreshed repo {repo_full_name}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error refreshing repo: {e}", exc_info=True)
            raise
        finally:
            await db.close()

    asyncio.run(_refresh())

