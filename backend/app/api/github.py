from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.adapters.db import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.repo import Repo, UserRepoRole
from app.schemas.user import UserResponse
from app.logging_config import get_logger
from app.integrations.github.client import list_installation_repositories

logger = get_logger(__name__)
router = APIRouter()


@router.get("/github/me", response_model=UserResponse)
async def github_me(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Compute managed repos similarly to /api/me
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


@router.get("/github/installations")
async def list_user_installations(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Repo.installation_id, func.count(Repo.id))
        .join(UserRepoRole)
        .where(UserRepoRole.user_id == current_user.id)
        .where(Repo.installation_id.isnot(None))
        .group_by(Repo.installation_id)
    )
    rows = result.all()

    installations = [
        {"installation_id": int(installation_id), "repo_count": int(count)}
        for installation_id, count in rows
        if installation_id is not None
    ]

    return {"installations": installations}


@router.get("/github/installations/{installation_id}/repos")
async def list_installation_repos(
    installation_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Optional: verify the user has access to at least one repo for this installation
    access_check = await db.execute(
        select(func.count(Repo.id))
        .join(UserRepoRole)
        .where(UserRepoRole.user_id == current_user.id)
        .where(Repo.installation_id == installation_id)
    )
    if (access_check.scalar() or 0) == 0:
        # No local repos mapped yet; still allow listing from GitHub to fix empty state
        logger.info(
            f"User {current_user.id} requested repos for installation {installation_id} with no local mapping"
        )

    try:
        data = await list_installation_repositories(installation_id)
    except Exception as e:
        logger.error(f"Failed to list installation repositories: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Failed to fetch repositories from GitHub")

    repos: List[Dict[str, Any]] = []
    for repo in data.get("repositories", []):
        repos.append({
            "repo_full_name": repo.get("full_name"),
            "name": repo.get("name"),
            "owner": repo.get("owner", {}).get("login"),
            "private": repo.get("private"),
            "html_url": repo.get("html_url"),
        })

    return {"installation_id": installation_id, "repos": repos, "total_count": data.get("total_count", len(repos))}
