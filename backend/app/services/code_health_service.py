"""Code health scanning service."""
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pr import PullRequest
from app.models.code_health import CodeHealth
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def process_code_health(
    pr_id: int,
    code_health_data: Dict[str, Any],
    db: AsyncSession
) -> None:
    """Process code health findings and compute score.
    
    Args:
        pr_id: Pull request ID
        code_health_data: Code health findings from artifact
        db: Database session
    """
    # Get PR
    pr_result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id)
    )
    pr = pr_result.scalar_one_or_none()
    
    if not pr:
        logger.warning(f"PR not found: {pr_id}")
        return
    
    # Normalize findings
    findings = code_health_data.get("findings", [])
    
    # Compute score (0-100)
    # Simple formula: start at 100, deduct points for issues
    score = 100
    severity_penalties = {
        "critical": 20,
        "high": 10,
        "medium": 5,
        "low": 2,
    }
    
    for finding in findings:
        severity = finding.get("severity", "low").lower()
        penalty = severity_penalties.get(severity, 2)
        score = max(0, score - penalty)
    
    # Get or create code health record
    health_result = await db.execute(
        select(CodeHealth).where(CodeHealth.pr_id == pr_id)
    )
    health = health_result.scalar_one_or_none()
    
    if health:
        health.score = score
        health.findings = findings
    else:
        health = CodeHealth(
            pr_id=pr_id,
            score=score,
            findings=findings,
        )
        db.add(health)
    
    await db.commit()
    
    logger.info(f"Processed code health for PR {pr_id}: score={score}")

