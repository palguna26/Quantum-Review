"""CI artifact processing and test mapping service."""
import json
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.repo import Repo
from app.models.pr import PullRequest
from app.models.issue import ChecklistItem
from app.models.test_result import TestResult
from app.models.report import Report
from app.models.audit import Notification
from app.models.user import UserRepoRole
from app.utils.junit_parser import parse_junit_xml
from app.services.github_auth import get_github_api_client_async
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def process_and_map_results(
    workflow_run_payload: Dict[str, Any],
    db: AsyncSession
) -> None:
    """Process workflow run, download artifacts, and map test results.
    
    Args:
        workflow_run_payload: GitHub webhook payload for workflow_run event
        db: Database session
    """
    workflow_run = workflow_run_payload.get("workflow_run", {})
    repo_data = workflow_run_payload.get("repository", {})
    
    repo_full_name = repo_data.get("full_name")
    run_id = workflow_run.get("id")
    head_sha = workflow_run.get("head_sha")
    
    if not repo_full_name or not run_id:
        logger.error("Missing repo or run ID in payload")
        return
    
    # Get repo
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo or not repo.installation_id:
        logger.warning(f"Repo not found or not installed: {repo_full_name}")
        return
    
    # Find PR by head SHA
    pr_result = await db.execute(
        select(PullRequest).where(
            PullRequest.repo_id == repo.id,
            PullRequest.head_sha == head_sha
        )
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        logger.warning(f"PR not found for SHA {head_sha}")
        return
    
    # Download artifacts
    client = await get_github_api_client_async(repo.installation_id)
    try:
        # Get artifacts
        artifacts_response = await client.get(
            f"/repos/{repo_full_name}/actions/runs/{run_id}/artifacts"
        )
        artifacts_response.raise_for_status()
        artifacts_data = artifacts_response.json()
        
        junit_content = None
        coverage_content = None
        
        for artifact in artifacts_data.get("artifacts", []):
            artifact_name = artifact.get("name", "")
            
            if artifact_name == "autoqa-test-report":
                # Download artifact (would need to handle zip extraction in production)
                # For now, log that artifact was found
                logger.info(f"Found artifact: {artifact_name} (ID: {artifact.get('id')})")
                # In production: download zip, extract, read XML file
                # junit_content = extract_and_read_xml(artifact_zip)
        
        # For now, we'll need to fetch the actual artifact content
        # This is simplified - in production, you'd need to handle zip extraction
    finally:
        await client.aclose()
    
    # Parse JUnit XML (if available)
    if junit_content:
        try:
            test_results_data = parse_junit_xml(junit_content)
        except Exception as e:
            logger.error(f"Error parsing JUnit XML: {e}")
            test_results_data = []
    else:
        # Mock data for now - in production, this would come from actual artifact
        test_results_data = []
    
    # Get manifest
    manifest = pr.test_manifest or {}
    manifest_tests = manifest.get("tests", [])
    
    # Create test_id to manifest mapping
    manifest_map = {test["test_id"]: test for test in manifest_tests}
    
    # Delete existing test results
    existing_results = await db.execute(
        select(TestResult).where(TestResult.pr_id == pr.id)
    )
    for result in existing_results.scalars():
        await db.delete(result)
    
    # Create test results and map to checklist
    checklist_updates = {}  # item_id -> status
    
    for test_data in test_results_data:
        test_id = test_data["test_id"]
        manifest_test = manifest_map.get(test_id, {})
        checklist_ids = manifest_test.get("checklist_ids", [])
        
        # Create test result
        test_result = TestResult(
            pr_id=pr.id,
            test_id=test_id,
            name=test_data["name"],
            status=test_data["status"],
            duration_ms=test_data.get("duration_ms"),
            checklist_ids=checklist_ids,
        )
        db.add(test_result)
        
        # Update checklist item statuses
        if test_data["status"] == "passed":
            for item_id in checklist_ids:
                if item_id not in checklist_updates:
                    checklist_updates[item_id] = "passed"
        elif test_data["status"] == "failed":
            for item_id in checklist_ids:
                checklist_updates[item_id] = "failed"
    
    # Update checklist items
    if pr.linked_issue_id:
        checklist_result = await db.execute(
            select(ChecklistItem).where(ChecklistItem.issue_id == pr.linked_issue_id)
        )
        for item in checklist_result.scalars():
            if item.item_id in checklist_updates:
                item.status = checklist_updates[item.item_id]
    
    # Compute validation status
    all_passed = all(
        test_data["status"] == "passed" for test_data in test_results_data
    ) if test_results_data else False
    
    pr.validation_status = "validated" if all_passed else "needs_work"
    
    # Create report
    report = Report(
        pr_id=pr.id,
        summary=f"Processed {len(test_results_data)} tests. All passed: {all_passed}",
        report_content=json.dumps(test_results_data, indent=2),
    )
    db.add(report)
    
    await db.commit()
    
    logger.info(f"Processed workflow run {run_id} for PR #{pr.pr_number}")
    
    # Create notifications
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
            kind="pr_validated",
            payload={
                "pr_number": pr.pr_number,
                "validation_status": pr.validation_status,
                "test_count": len(test_results_data),
            },
            read=False,
        )
        db.add(notification)
    
    await db.commit()

