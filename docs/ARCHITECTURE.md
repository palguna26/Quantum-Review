# Architecture

## Overview

QuantumReview consists of a FastAPI backend, a React frontend, PostgreSQL for persistence, Redis for queues/cache, and GitHub integrations (OAuth + App).

```mermaid
graph TD
  FE[Frontend (React)] --> API[FastAPI Backend]
  API --> DB[(PostgreSQL)]
  API --> REDIS[(Redis)]
  API --> GH[GitHub App + OAuth]
```

## Auth Flow

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Frontend
  participant API as Backend
  participant GH as GitHub
  U->>FE: Click "Sign in with GitHub"
  FE->>API: GET /auth/github
  API->>GH: Redirect to GitHub OAuth
  GH->>API: Callback /auth/callback?code=...
  API->>API: Exchange code, create user, JWT
  API->>FE: Redirect to /auth/callback?token=...
  FE->>API: Subsequent calls with cookie/Bearer
```

## Webhooks Flow

```mermaid
sequenceDiagram
  participant GH as GitHub App
  participant API as Backend
  participant Q as Redis/RQ
  GH->>API: POST /webhooks/github (signed)
  API->>API: Verify signature, deduplicate
  API->>Q: Enqueue tasks (sync/installations/repos, manifest, workflow run)
  Q->>API: Worker updates DB
  API->>FE: SSE/notifications
```

## Modules

- `app/api/auth.py` – OAuth endpoints and session creation
- `app/api/github.py` – installations and repos endpoints
- `app/webhooks/github.py` – webhook signature verification and dispatch
- `app/services/*` – business logic (checklist, CI mapping, notifications)
- `app/integrations/github/*` – GitHub App client helpers
- `app/models/*` – SQLAlchemy models (users, repos, issues, PRs, health)
- `frontend/src/*` – pages, components, hooks

