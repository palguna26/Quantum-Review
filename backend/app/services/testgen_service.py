"""Test manifest generation service."""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.repo import Repo
from app.models.pr import PullRequest
from app.models.issue import Issue, ChecklistItem
from app.utils.parser import extract_changed_symbols
from app.services.github_auth import get_github_api_client_async
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def generate_and_save_manifest(
    pr_payload: Dict[str, Any],
    db: AsyncSession
) -> None:
    """Generate test manifest for PR and save to database.
    
    Args:
        pr_payload: GitHub webhook payload for PR event
        db: Database session
    """
    pr_data = pr_payload.get("pull_request", {})
    repo_data = pr_payload.get("repository", {})
    
    pr_number = pr_data.get("number")
    repo_full_name = repo_data.get("full_name")
    head_sha = pr_data.get("head", {}).get("sha")
    
    if not pr_number or not repo_full_name:
        logger.error("Missing PR number or repo full name in payload")
        return
    
    # Get repo
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo or not repo.installation_id:
        logger.warning(f"Repo not found or not installed: {repo_full_name}")
        return
    
    # Get or create PR
    pr_result = await db.execute(
        select(PullRequest).where(
            PullRequest.repo_id == repo.id,
            PullRequest.pr_number == pr_number
        )
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        # Try to find linked issue
        issue_number = pr_data.get("body", "").split("#")[1] if "#" in pr_data.get("body", "") else None
        linked_issue_id = None
        if issue_number:
            issue_result = await db.execute(
                select(Issue).where(
                    Issue.repo_id == repo.id,
                    Issue.issue_number == int(issue_number)
                )
            )
            linked_issue = issue_result.scalar_one_or_none()
            if linked_issue:
                linked_issue_id = linked_issue.id
        
        pr = PullRequest(
            repo_id=repo.id,
            pr_number=pr_number,
            head_sha=head_sha,
            linked_issue_id=linked_issue_id,
            validation_status="pending",
        )
        db.add(pr)
        await db.flush()
    else:
        pr.head_sha = head_sha
    
    # Fetch PR files from GitHub
    client = await get_github_api_client_async(repo.installation_id)
    try:
        files_response = await client.get(
            f"/repos/{repo_full_name}/pulls/{pr_number}/files"
        )
        files_response.raise_for_status()
        files_data = files_response.json()
    finally:
        await client.aclose()
    
    # Extract changed symbols and generate manifest
    manifest_tests = []
    test_id_counter = 1
    
    # Get checklist items if linked issue exists
    checklist_items = []
    if pr.linked_issue_id:
        checklist_result = await db.execute(
            select(ChecklistItem).where(ChecklistItem.issue_id == pr.linked_issue_id)
        )
        checklist_items = checklist_result.scalars().all()
    
    for file_data in files_data:
        file_path = file_data.get("filename", "")
        patch = file_data.get("patch", "")
        
        if not patch or not file_path:
            continue
        
        # Extract changed symbols
        symbols = extract_changed_symbols(patch, file_path)
        
        # Determine framework from file extension
        ext = file_path.split(".")[-1].lower()
        if ext in ["py"]:
            framework = "pytest"
        elif ext in ["js", "jsx", "ts", "tsx"]:
            framework = "jest"
        else:
            framework = "unknown"
        
        # Generate test suggestions for each symbol
        for symbol in symbols:
            # Map to checklist items (simple heuristic)
            checklist_ids = []
            for item in checklist_items:
                if symbol.lower() in item.text.lower():
                    checklist_ids.append(item.item_id)
            
            test_id = f"T{test_id_counter}"
            test_id_counter += 1
            
            manifest_tests.append({
                "test_id": test_id,
                "name": f"test_{symbol.lower()}",
                "framework": framework,
                "target_file": file_path,
                "checklist_ids": checklist_ids,
            })
    
    # Save manifest
    pr.test_manifest = {"tests": manifest_tests}
    await db.commit()
    
    logger.info(f"Generated test manifest for PR #{pr_number} in {repo_full_name}")

