You are Trae, acting as a staff-level engineer (equivalent to a senior Google L6/L7 developer) helping me complete and harden my project **QuantumReview** — a modern GitHub code review & repo health platform.

Your job is to scan, understand, refactor, fix, and complete the entire application to a production-grade standard, including:

- GitHub OAuth + GitHub App integration
- Webhooks
- LLM-powered issue checklists & PR validation
- Vulnerability scanning & repo health metrics
- Documentation & free hosting deployment setup

Treat this repo as if you are the primary architect on a production product.

======================================================================
0. PROJECT CONTEXT
======================================================================

- Name: **QuantumReview**
- Frontend: React (dark, futuristic UI, Tailwind-style from Lovable)
- Backend: FastAPI (Python) + PostgreSQL
- DB: Hosted on Render
- Auth: GitHub OAuth + GitHub App
- GitHub App: already installed on `github.com/palguna26`, but repos currently not showing in the dashboard

Core product vision:

> QuantumReview connects to GitHub via a GitHub App, and:
> 1. Uses an LLM to generate **issue-based checklists**.
> 2. Uses an LLM to **validate PRs against those checklists**.
> 3. Scans repositories for **security vulnerabilities and code health issues**.
> 4. Produces **repo health metrics** (e.g., security issues, test coverage, lint status, dependency freshness) and surfaces them in a dashboard.

The end result must feel like it was built by a senior Google engineering team:
- Clean architecture
- Strong typing, tests, and error handling
- Secure defaults
- Excellent docs and DX

======================================================================
1. GITHUB INTEGRATION – OAUTH, APP, INSTALLATIONS, REPOS
======================================================================

Goals:

- User logs in via **GitHub OAuth**.
- QuantumReview discovers the user’s **GitHub App installations**.
- For each installation, list the repositories the app has access to.
- Fix the current “no repositories found” behavior.
- Use **GitHub App installation access tokens**, NOT `/user/repos` via OAuth.

Tasks:

1. Locate all FastAPI routes related to GitHub:
   - OAuth login (e.g., `/auth/github/login`).
   - OAuth callback (e.g., `/auth/github/callback`).
   - Any GitHub-related API routes.

2. Fix the OAuth callback:
   - Expect `code` in query params (`?code=...`).
   - Match the redirect URI to what is configured in GitHub.
   - Handle missing/invalid `code` with clear error responses.
   - Log detailed backend errors; show friendly frontend messages.

3. Implement a clean GitHub integration module, e.g. `app/integrations/github/client.py`, with:
   - OAuth code → access token exchange.
   - Fetching GitHub user profile (id, login, avatar).
   - Listing GitHub App **installations**.
   - Creating installation access tokens:
     - `POST /app/installations/{installation_id}/access_tokens`
   - Listing repositories for an installation:
     - `GET /installation/repositories` (with installation token).

4. Add backend endpoints:
   - `GET /api/github/me` → current GitHub user.
   - `GET /api/github/installations` → list installations for current user.
   - `GET /api/github/installations/{installation_id}/repos` → list repos.

5. All GitHub config from env vars:
   - `GITHUB_CLIENT_ID`
   - `GITHUB_CLIENT_SECRET`
   - `GITHUB_APP_ID`
   - `GITHUB_PRIVATE_KEY` (PEM, multiline-safe)
   - `GITHUB_WEBHOOK_SECRET`
   - `BACKEND_BASE_URL`, `FRONTEND_BASE_URL`, etc.

6. Add robust error handling:
   - Invalid tokens, no installations, permission issues.
   - Clean error models to the frontend, rich logs on backend.

======================================================================
2. WEBHOOKS – INSTALL, REPOS, PRs, PUSH
======================================================================

Implement GitHub webhooks to sync state:

1. Create a route, e.g. `POST /webhooks/github`.
2. Verify signatures:
   - Use `X-Hub-Signature-256` with HMAC SHA-256 and `GITHUB_WEBHOOK_SECRET`.
   - Reject invalid signatures with 401/403.

3. Handle key events:
   - `installation` (created, deleted).
   - `installation_repositories` (repos added/removed).
   - `pull_request` (opened, synchronize, reopened).
   - `push` (optional; useful for health re-scans).

4. On events:
   - Sync installation + repo metadata into DB.
   - Record PR metadata for LLM validation.
   - Optionally enqueue background tasks for health scans or re-validation.

5. Implement webhook logic in a service module, e.g.:
   - `app/services/github_webhooks.py`
   - Keep route handler thin; business logic in services.

======================================================================
3. LLM FEATURES – ISSUE CHECKLISTS & PR VALIDATION
======================================================================

A. Issue → Checklist (LLM)

- For a GitHub Issue (title, body, labels, maybe initial comments):
  - Generate a **structured checklist** with an LLM.

Checklist item fields:
- `id` (stable identifier)
- `title`
- `description`
- `category` (e.g., functionality, performance, security, tests, docs)
- `priority` (P0/P1/P2)
- Optional: `estimated_effort`

Backend:

- Endpoints:
  - `POST /api/issues/{issue_id}/checklist` – trigger generation (calls LLM).
  - `GET /api/issues/{issue_id}/checklist` – fetch stored checklist.

- Persist checklist items in DB:
  - Linked to user, repo, issue.

B. PR → Checklist Validation (LLM)

- For a PR:
  - Fetch context: PR title/body, diff, changed files, linked issues if any.
  - Retrieve related checklist.
  - Ask LLM to:
    - Evaluate each checklist item: `PASSED`, `FAILED`, `PARTIAL`, `NOT_APPLICABLE`.
    - Provide short justification per item.
    - Provide overall summary + optional score (0–100).

Backend:

- Endpoints:
  - `POST /api/prs/{pr_number}/validate` with repo + installation info.
  - `GET /api/prs/{pr_number}/validation` – fetch latest validation.

- Persist:
  - Item-level statuses.
  - Summary/score.
  - Timestamp and model used.

LLM integration:

- Implement `app/services/llm_service.py` (or similar):
  - Abstract the provider behind clear functions.
  - Use env vars:
    - `LLM_PROVIDER`
    - `LLM_MODEL`
    - `LLM_API_KEY`
  - Enforce JSON output using strong system prompts and Pydantic validation.
  - Handle timeouts, rate limits, and errors gracefully.

Frontend:

- UI:
  - View and trigger checklist generation from an issue view.
  - View checklist items (with categories/priorities).
  - Run PR validation and show per-item status with icons/colors.
  - Show summary and overall score.

======================================================================
4. VULNERABILITY SCANNING & REPO HEALTH METRICS
======================================================================

QuantumReview must also act as a **repo health dashboard**.

Goals:

- For each repository, run code & dependency checks and produce **health metrics** such as:
  - Security vulnerabilities (dependencies + simple static checks).
  - Lint status.
  - Test coverage (if coverage reports exist).
  - Dependency freshness (outdated libraries).
  - Basic repo activity (recent commits, open PRs/issues).

Implementation hints (Trae should adapt to the repo’s stack and what’s reasonable to add):

1. **Security & Vulnerability Scanning (Static)**

   Add support and configuration for tools such as:
   - Python:
     - `pip-audit` or `safety` for dependency vulnerabilities.
     - `bandit` for security static analysis.
   - JavaScript/TypeScript:
     - `npm audit` / `pnpm audit` / `yarn audit` (depending on project).
   - Optional: config for `semgrep` if appropriate.

   Don’t actually run tools in code, but:
   - Provide scripts in `package.json` or `pyproject.toml` / `Makefile` to run scans.
   - Document how to run them locally and in CI.

2. **Repo Health Metrics Model**

   In backend, define models & schemas for repo health:

   Example fields:
   - `security_issues_count`
   - `critical_vulns`
   - `high_vulns`
   - `medium_vulns`
   - `lint_status` (PASS/FAIL/UNKNOWN)
   - `test_coverage` (percentage, nullable)
   - `dependencies_outdated` (count)
   - `last_analysis_at`
   - Optional “health score” 0–100, combining metrics.

   Create an endpoint like:
   - `GET /api/repos/{repo_id}/health` – returns latest metrics.
   - `POST /api/repos/{repo_id}/analyze` – (optional) kicks off analysis or stores metrics.

   Trae should:
   - Create service layer functions to compute a **health score** from metrics.
   - Provide clean types and docs.

3. **Analysis Pipelines**

   Even if actual scanning is triggered manually or via CI, structure code as if:

   - A “health analysis job”:
     - Calls out to local/CI-generated artifacts (e.g., JSON from scanners, coverage reports).
     - Parses and aggregates them into repo health metrics.
   - Provide parsing helpers and placeholder functions where actual integration requires environment support.

4. **Frontend Repo Health Dashboard**

   - For each repo, show:
     - Health score (with badge/color).
     - Security summary (e.g., “2 critical, 5 high, 10 medium”).
     - Latest test coverage.
     - Lint status.
     - Last analysis timestamp.
   - Create “Repo Health” section/card on the repo page.
   - Add empty state if no analysis has been run yet, with instructions / CTA.

5. **CI / Automation Docs**

   In docs, describe how to integrate:
   - `pip-audit` / `safety` / `bandit` / `npm audit` / etc. with GitHub Actions.
   - How to publish their results so QuantumReview can ingest them (e.g., JSON output).

======================================================================
5. BACKEND ARCHITECTURE & MODELS
======================================================================

Refactor into a clean structure (adapt names to existing layout):

- `app/main.py` – FastAPI app creation, routers, middleware.
- `app/config.py` – Pydantic settings for env vars.
- `app/api/routes/`
  - `auth.py` – GitHub OAuth.
  - `github.py` – installations, repos.
  - `issues.py` – LLM checklists.
  - `prs.py` – LLM PR validation.
  - `health.py` – repo health metrics.
  - `webhooks.py` – GitHub webhooks.
- `app/models/`
  - `user.py`
  - `installation.py`
  - `repository.py`
  - `issue_checklist.py`, `checklist_item.py`
  - `pr_validation.py`, `pr_validation_item.py`
  - `repo_health.py`
- `app/schemas/` – Pydantic schemas.
- `app/services/`
  - `github_service.py`
  - `llm_service.py`
  - `checklist_service.py`
  - `validation_service.py`
  - `health_service.py`
  - `github_webhooks_service.py`
- `app/integrations/github/` – HTTP client + webhook helpers.
- `app/core/` – security, auth, logging, utils.

Ensure:
- Migrations (Alembic or similar) exist for all models.
- Consistent async/sync behavior with SQLAlchemy.

======================================================================
6. FRONTEND INTEGRATION
======================================================================

Frontend should:

- Use API endpoints:
  - Auth: OAuth redirects.
  - GitHub: `/api/github/me`, `/api/github/installations`, `/api/github/installations/{id}/repos`.
  - LLM features: checklist & validation endpoints.
  - Repo health: `/api/repos/{repo_id}/health`.

- Have hooks/components:
  - `useGitHubInstallations`, `useRepositories`
  - `useIssueChecklist`
  - `usePrValidation`
  - `useRepoHealth`

- UI:
  - Dashboard: list repositories with a small health indicator.
  - Repo page:
    - Tabs: Overview / Health / Issues / PRs / Settings (adapt to existing design).
    - Health tab or card summarizing metrics.
    - Issue tab for checklist generation + display.
    - PR tab for PR validation results.

- States:
  - Loading, empty, error, success.
  - Match dark/futuristic design (no default browser styling leaking in).

======================================================================
7. TESTING
======================================================================

Backend (pytest + HTTPX):

- OAuth callback and auth flow (valid & invalid cases).
- GitHub client (mock HTTP responses for installations, repos).
- Webhooks (valid/invalid signature, routing logic).
- LLM services (mock provider; test prompt + JSON parsing).
- Checklist & validation services.
- Health service (score calculation, aggregation).

Frontend (React Testing Library / existing stack):

- Repo list: loading / data / empty.
- Repo health widget: different states (healthy/unhealthy/no data).
- Issue checklist view.
- PR validation view.

======================================================================
8. DOCUMENTATION & FREE HOSTING
======================================================================

Create `/docs` directory with:

1. `README.md`
   - What QuantumReview is.
   - Main features:
     - LLM issue checklists.
     - LLM PR validation.
     - Vulnerability scanning integration.
     - Repo health metrics.
   - Quick local setup.

2. `ARCHITECTURE.md`
   - Mermaid diagrams for:
     - High-level architecture.
     - Auth flow.
     - Webhook + LLM + health pipeline.
   - Module responsibilities.

3. `GITHUB_SETUP.md`
   - Create GitHub OAuth app (scopes, callback URL).
   - Create GitHub App:
     - Necessary permissions (contents, metadata, issues, pull requests, webhooks).
     - Webhook URL.
     - Installation configuration (all repos / selected repos).

4. `WEBHOOKS.md`
   - How to configure webhooks in GitHub App.
   - Events to enable.
   - Local dev (e.g., using a tunneling service).
   - Signature verification (X-Hub-Signature-256).
   - Example payload snippets.

5. `DEPLOYMENT.md`
   - Backend on Render (FastAPI):
     - Build & start commands.
     - Env vars.
     - Exposed routes (`/api/...`, `/webhooks/github`).
   - PostgreSQL on Render.
   - Frontend on Vercel or Netlify:
     - Build commands.
     - Env vars for API URL.
   - Optional: Railway notes.
   - CORS setup.

6. `ENVIRONMENT.md`
   - All env vars documented:
     - Database: `DATABASE_URL`.
     - GitHub: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`.
     - LLM: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`.
     - App: `BACKEND_BASE_URL`, `FRONTEND_BASE_URL`, `ENV`, etc.
   - Generate `.env.example` at repo root.

7. `WORKFLOW.md`
   - Flows:
     - Login & repo selection.
     - Issue → checklist generation.
     - PR → validation against checklist.
     - Running vulnerability scans & importing/reading results for health metrics.
   - Recommended CI workflows using GitHub Actions.

======================================================================
9. CODE QUALITY & STYLE
======================================================================

While editing:

- Full type hints everywhere.
- Small, composable functions.
- Clean DI with FastAPI.
- No secrets in code.
- Good logging (info/debug/error) without leaking sensitive data.
- Remove dead code, unused imports, random `print`/`console.log`.
- Comments only where reasoning is non-obvious.

======================================================================
10. EXECUTION ORDER FOR TRAE
======================================================================

1. Scan current repo and understand existing structure.
2. Fix GitHub OAuth, GitHub App, installations & repo listing.
3. Implement and wire up webhooks.
4. Implement LLM issue checklists and PR validation.
5. Add vulnerability scanning integration & repo health metrics (models, endpoints, UI).
6. Refactor into clean architecture as needed.
7. Add tests.
8. Create `/docs` and `.env.example`.
9. Ensure local dev and free-hosting deployment are documented and correct.

At the end, QuantumReview should be a polished, deployable platform that:
- Logs in via GitHub.
- Lists installations and repos correctly.
- Processes webhooks.
- Generates LLM issue checklists.
- Validates PRs against those checklists.
- Surfaces repo health & vulnerability metrics.
- Is ready for deployment on free hosting platforms with clear documentation.

Now, analyze the repository and implement everything necessary to achieve this.
