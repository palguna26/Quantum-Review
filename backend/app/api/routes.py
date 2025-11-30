"""Main API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.adapters.db import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.repo import Repo, UserRepoRole
from app.models.issue import Issue, ChecklistItem
from app.models.pr import PullRequest
from app.schemas.user import UserResponse
from app.schemas.repo import RepoSummaryResponse
from app.schemas.issue import IssueResponse, ChecklistItemResponse, ChecklistSummary
from app.schemas.pr import PRDetailResponse, TestResultResponse, CodeHealthIssueResponse, SuggestedTestResponse, CoverageAdviceResponse
from app.schemas.notification import NotificationResponse
from app.models.pr import PullRequest, TestResult
from app.models.code_health import CodeHealth
from app.models.audit import AuditLog
from app.services.notifications import get_user_notifications, mark_notification_read
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile and managed repos."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get user's managed repos
    result = await db.execute(
        select(Repo)
        .join(UserRepoRole)
        .where(UserRepoRole.user_id == current_user.id)
        .where(UserRepoRole.role.in_(["admin", "maintainer", "manager"]))
    )
    repos = result.scalars().all()
    managed_repos = [repo.repo_full_name for repo in repos]
    
    return UserResponse(
        id=str(current_user.id),
        login=current_user.username,
        avatar_url=current_user.avatar_url or "",
        name=current_user.username,
        email=current_user.email,
        managed_repos=managed_repos,
    )


@router.get("/repos", response_model=List[RepoSummaryResponse])
async def get_repos(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's managed repos."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get user's repos with role
    result = await db.execute(
        select(Repo, UserRepoRole.role)
        .join(UserRepoRole)
        .where(UserRepoRole.user_id == current_user.id)
        .where(UserRepoRole.role.in_(["admin", "maintainer", "manager", "viewer"]))
    )
    repo_rows = result.all()
    
    repos = []
    for repo, role in repo_rows:
        # Get PR count
        pr_count_result = await db.execute(
            select(func.count(PullRequest.id)).where(PullRequest.repo_id == repo.id)
        )
        pr_count = pr_count_result.scalar() or 0
        
        # Get issue count
        issue_count_result = await db.execute(
            select(func.count(Issue.id)).where(Issue.repo_id == repo.id)
        )
        issue_count = issue_count_result.scalar() or 0
        
        # Calculate health score (simplified - can be enhanced)
        health_score = 85  # Placeholder
        
        owner, name = repo.repo_full_name.split("/", 1)
        
        repos.append(RepoSummaryResponse(
            repo_full_name=repo.repo_full_name,
            owner=owner,
            name=name,
            health_score=health_score,
            is_installed=repo.is_installed,
            pr_count=pr_count,
            issue_count=issue_count,
        ))
    
    return repos


@router.get("/repos/{owner}/{repo}", response_model=RepoSummaryResponse)
async def get_repo(
    owner: str,
    repo: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get repo details."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Check access
    role_result = await db.execute(
        select(UserRepoRole).where(
            and_(
                UserRepoRole.user_id == current_user.id,
                UserRepoRole.repo_id == repo_obj.id
            )
        )
    )
    if not role_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get counts
    pr_count_result = await db.execute(
        select(func.count(PullRequest.id)).where(PullRequest.repo_id == repo_obj.id)
    )
    pr_count = pr_count_result.scalar() or 0
    
    issue_count_result = await db.execute(
        select(func.count(Issue.id)).where(Issue.repo_id == repo_obj.id)
    )
    issue_count = issue_count_result.scalar() or 0
    
    health_score = 85  # Placeholder
    
    return RepoSummaryResponse(
        repo_full_name=repo_obj.repo_full_name,
        owner=owner,
        name=repo,
        health_score=health_score,
        is_installed=repo_obj.is_installed,
        pr_count=pr_count,
        issue_count=issue_count,
    )


@router.get("/repos/{owner}/{repo}/install")
async def get_install_url(
    owner: str,
    repo: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get GitHub App installation URL."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Return GitHub App installation URL
    install_url = f"https://github.com/apps/{settings.APP_NAME.lower()}/installations/new"
    return {"install_url": install_url}


@router.get("/repos/{owner}/{repo}/issues", response_model=List[IssueResponse])
async def get_issues(
    owner: str,
    repo: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List issues for a repo."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get issues
    issues_result = await db.execute(
        select(Issue)
        .where(Issue.repo_id == repo_obj.id)
        .order_by(Issue.created_at.desc())
    )
    issues = issues_result.scalars().all()
    
    issue_responses = []
    for issue in issues:
        # Get checklist items for summary
        checklist_result = await db.execute(
            select(ChecklistItem).where(ChecklistItem.issue_id == issue.id)
        )
        checklist_items = checklist_result.scalars().all()
        
        total = len(checklist_items)
        passed = sum(1 for item in checklist_items if item.status == "passed")
        failed = sum(1 for item in checklist_items if item.status == "failed")
        pending = sum(1 for item in checklist_items if item.status == "pending")
        
        # Map status
        status_map = {
            "pending": "processing",
            "processed": "completed",
            "needs_attention": "open",
        }
        
        issue_responses.append(IssueResponse(
            issue_number=issue.issue_number,
            title=issue.title,
            status=status_map.get(issue.status, "open"),
            created_at=issue.created_at.isoformat(),
            updated_at=issue.updated_at.isoformat(),
            checklist_summary=ChecklistSummary(
                total=total,
                passed=passed,
                failed=failed,
                pending=pending,
            ),
            github_url=f"https://github.com/{repo_full_name}/issues/{issue.issue_number}",
        ))
    
    return issue_responses


@router.get("/repos/{owner}/{repo}/issues/{issue_number}", response_model=IssueResponse)
async def get_issue(
    owner: str,
    repo: str,
    issue_number: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get issue details with checklist."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    issue_result = await db.execute(
        select(Issue)
        .where(and_(Issue.repo_id == repo_obj.id, Issue.issue_number == issue_number))
        .options(selectinload(Issue.checklist_items))
    )
    issue = issue_result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Get checklist items
    checklist_items = issue.checklist_items
    total = len(checklist_items)
    passed = sum(1 for item in checklist_items if item.status == "passed")
    failed = sum(1 for item in checklist_items if item.status == "failed")
    pending = sum(1 for item in checklist_items if item.status == "pending")
    
    checklist_responses = [
        ChecklistItemResponse(
            id=item.item_id,
            text=item.text,
            required=item.required == "true" if isinstance(item.required, str) else bool(item.required),
            status=item.status,
            linked_tests=item.linked_test_ids or [],
        )
        for item in checklist_items
    ]
    
    status_map = {
        "pending": "processing",
        "processed": "completed",
        "needs_attention": "open",
    }
    
    return IssueResponse(
        issue_number=issue.issue_number,
        title=issue.title,
        status=status_map.get(issue.status, "open"),
        created_at=issue.created_at.isoformat(),
        updated_at=issue.updated_at.isoformat(),
        checklist_summary=ChecklistSummary(
            total=total,
            passed=passed,
            failed=failed,
            pending=pending,
        ),
        checklist=checklist_responses,
        github_url=f"https://github.com/{repo_full_name}/issues/{issue.issue_number}",
    )


@router.patch("/repos/{owner}/{repo}/issues/{issue_number}/checklist/{item_id}")
async def update_checklist_item(
    owner: str,
    repo: str,
    issue_number: int,
    item_id: str,
    status_update: dict,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update checklist item status."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    issue_result = await db.execute(
        select(Issue).where(
            and_(Issue.repo_id == repo_obj.id, Issue.issue_number == issue_number)
        )
    )
    issue = issue_result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Find checklist item
    item_result = await db.execute(
        select(ChecklistItem).where(
            and_(
                ChecklistItem.issue_id == issue.id,
                ChecklistItem.item_id == item_id
            )
        )
    )
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    # Update status
    new_status = status_update.get("status")
    if new_status and new_status in ["pending", "passed", "failed", "skipped"]:
        item.status = new_status
        await db.commit()
        await db.refresh(item)
        
        return {"status": "updated", "item_id": item_id, "new_status": new_status}
    
    raise HTTPException(status_code=400, detail="Invalid status value")


@router.post("/repos/{owner}/{repo}/issues/{issue_number}/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_checklist(
    owner: str,
    repo: str,
    issue_number: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enqueue checklist regeneration job."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    issue_result = await db.execute(
        select(Issue).where(
            and_(Issue.repo_id == repo_obj.id, Issue.issue_number == issue_number)
        )
    )
    issue = issue_result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Enqueue background job (will be implemented in workers phase)
    from app.workers.tasks import generate_checklist
    from rq import Queue
    import redis
    
    redis_conn = redis.from_url(settings.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    
    # Create payload
    payload = {
        "action": "opened",
        "issue": {
            "number": issue.issue_number,
            "title": issue.title,
            "body": issue.body,
        },
        "repository": {
            "full_name": repo_full_name,
            "id": repo_obj.id,
        },
    }
    
    job = queue.enqueue(generate_checklist, payload)
    
    return {"status": "accepted", "job_id": job.id}


@router.get("/repos/{owner}/{repo}/prs/{pr_number}", response_model=PRDetailResponse)
async def get_pr(
    owner: str,
    repo: str,
    pr_number: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get PR details."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    pr_result = await db.execute(
        select(PullRequest)
        .where(and_(PullRequest.repo_id == repo_obj.id, PullRequest.pr_number == pr_number))
        .options(selectinload(PullRequest.test_results), selectinload(PullRequest.code_health))
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    
    # Get test results
    test_results = [
        TestResultResponse(
            test_id=tr.test_id,
            name=tr.name,
            status=tr.status,
            duration_ms=None,  # Could be added to model
            checklist_ids=tr.checklist_ids or [],
        )
        for tr in pr.test_results
    ]
    
    # Get code health
    code_health_list = []
    if pr.code_health and pr.code_health.findings:
        for idx, finding in enumerate(pr.code_health.findings or []):
            code_health_list.append(CodeHealthIssueResponse(
                id=f"ch{idx}",
                severity=finding.get("severity", "low"),
                category=finding.get("category", "unknown"),
                message=finding.get("message", ""),
                file_path=finding.get("file_path", ""),
                line_number=finding.get("line_number"),
                suggestion=finding.get("suggestion"),
            ))
    
    # Get health score
    health_score = pr.code_health.score if pr.code_health else 85
    
    # Mock suggested tests and coverage advice (would come from LLM or analysis)
    suggested_tests = []
    coverage_advice = []
    
    return PRDetailResponse(
        pr_number=pr.pr_number,
        title=f"PR #{pr.pr_number}",  # Would get from GitHub API
        author="unknown",  # Would get from GitHub API
        created_at=pr.created_at.isoformat(),
        health_score=health_score,
        validation_status=pr.validation_status,
        manifest=pr.test_manifest,
        test_results=test_results,
        code_health=code_health_list,
        coverage_advice=coverage_advice,
        suggested_tests=suggested_tests,
        github_url=f"https://github.com/{repo_full_name}/pull/{pr_number}",
    )


@router.post("/repos/{owner}/{repo}/prs/{pr_number}/revalidate", status_code=status.HTTP_202_ACCEPTED)
async def revalidate_pr(
    owner: str,
    repo: str,
    pr_number: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enqueue PR revalidation job."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    pr_result = await db.execute(
        select(PullRequest).where(
            and_(PullRequest.repo_id == repo_obj.id, PullRequest.pr_number == pr_number)
        )
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    
    # Enqueue revalidation (would trigger workflow run processing)
    from rq import Queue
    import redis
    
    redis_conn = redis.from_url(settings.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    
    # In real implementation, would trigger a new workflow run or re-process existing one
    # For now, just return accepted
    return {"status": "accepted", "message": "Revalidation queued"}


@router.post("/repos/{owner}/{repo}/prs/{pr_number}/flag_for_merge")
async def flag_for_merge(
    owner: str,
    repo: str,
    pr_number: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record manual 'recommend merge' action in audit logs."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    repo_full_name = f"{owner}/{repo}"
    repo_result = await db.execute(
        select(Repo).where(Repo.repo_full_name == repo_full_name)
    )
    repo_obj = repo_result.scalar_one_or_none()
    
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    pr_result = await db.execute(
        select(PullRequest).where(
            and_(PullRequest.repo_id == repo_obj.id, PullRequest.pr_number == pr_number)
        )
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    
    # Create audit log
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        action="flag_for_merge",
        target_type="pr",
        target_id=pr.id,
        details={
            "pr_number": pr_number,
            "repo_full_name": repo_full_name,
        },
    )
    db.add(audit_log)
    await db.commit()
    
    return {"status": "recorded", "message": "Merge recommendation logged"}


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user notifications."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notifications = await get_user_notifications(current_user.id, db)
    
    # Map to response format
    from app.models.repo import Repo
    
    notification_responses = []
    for notif in notifications:
        # Get repo full name
        repo_result = await db.execute(
            select(Repo).where(Repo.id == notif.repo_id)
        )
        repo = repo_result.scalar_one_or_none()
        repo_full_name = repo.repo_full_name if repo else None
        
        # Map kind to type
        type_map = {
            "checklist_ready": "success",
            "pr_validated": "info",
            "repo_event": "info",
        }
        notif_type = type_map.get(notif.kind, "info")
        
        # Generate message from payload
        message = notif.kind.replace("_", " ").title()
        if notif.payload:
            if "issue_number" in notif.payload:
                message = f"Checklist ready for issue #{notif.payload['issue_number']}"
            elif "pr_number" in notif.payload:
                message = f"PR #{notif.payload['pr_number']} validation completed"
        
        notification_responses.append(NotificationResponse(
            id=str(notif.id),
            type=notif_type,
            message=message,
            repo_full_name=repo_full_name,
            created_at=notif.created_at.isoformat(),
            read=notif.read,
        ))
    
    return notification_responses


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read_endpoint(
    notification_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notification = await mark_notification_read(notification_id, current_user.id, db)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"status": "ok", "message": "Notification marked as read"}

