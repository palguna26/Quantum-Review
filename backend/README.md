# QuantumReview Backend

Production-ready FastAPI backend for QuantumReview, providing GitHub App integration, webhook processing, checklist generation, PR validation, and code health analysis.

## Features

- **GitHub App Authentication**: JWT-based App authentication with installation token caching
- **OAuth Flow**: User authentication via GitHub OAuth
- **Webhook Processing**: Secure webhook handling with HMAC verification and idempotency
- **Checklist Generation**: Automatic extraction of acceptance criteria from issues
- **Test Manifest Generation**: PR diff analysis and test suggestion
- **CI Integration**: JUnit XML parsing and test-to-checklist mapping
- **Code Health Analysis**: Artifact processing and health scoring
- **Background Jobs**: Redis + RQ for async task processing
- **Notifications**: Real-time notifications for repo events

## Tech Stack

- **FastAPI**: Modern async web framework
- **SQLAlchemy (async)**: Async ORM with PostgreSQL
- **Alembic**: Database migrations
- **Redis + RQ**: Background job queue
- **httpx**: Async HTTP client for GitHub API
- **PyJWT + Cryptography**: JWT and cryptographic operations

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 7+
- Docker and Docker Compose (for local development)

### Local Development with Docker

1. **Clone the repository and navigate to backend:**

```bash
cd backend
```

2. **Create `.env` file:**

```bash
cp .env.example .env
# Edit .env with your GitHub App credentials
```

3. **Start services:**

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- RQ worker for background jobs

4. **Run migrations:**

```bash
docker-compose exec backend alembic upgrade head
```

5. **Access the API:**

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Local Development without Docker

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up PostgreSQL and Redis:**

```bash
# PostgreSQL
createdb quantumreview

# Redis (if not running)
redis-server
```

3. **Configure environment:**

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/quantumreview"
export REDIS_URL="redis://localhost:6379/0"
# ... other env vars
```

4. **Run migrations:**

```bash
alembic upgrade head
```

5. **Start the server:**

```bash
uvicorn app.main:app --reload
```

6. **Start worker (in separate terminal):**

```bash
python -m app.workers.worker
```

## GitHub App Setup

### 1. Create GitHub App

1. Go to https://github.com/settings/apps/new
2. Fill in app details:
   - **Name**: QuantumReview (or your choice)
   - **Homepage URL**: Your app URL
   - **Webhook URL**: `https://your-domain.com/webhooks/github`
   - **Webhook secret**: Generate a secure random string

3. **Permissions**:
   - Issues: Read & Write
   - Pull requests: Read
   - Actions: Read
   - Checks: Read & Write (optional)
   - Metadata: Read

4. **Webhook events**:
   - `installation`
   - `installation_repositories`
   - `issues` (opened, edited)
   - `pull_request` (opened, synchronize, closed)
   - `workflow_run`
   - `check_suite`
   - `check_run`

5. **Generate private key** and download the PEM file

6. **Note your App ID** from the app settings page

### 2. Configure OAuth

1. In GitHub App settings, go to "User authorization callback URL"
2. Set to: `https://your-domain.com/auth/callback`
3. Note your **Client ID** and generate a **Client Secret**

### 3. Environment Variables

Set these in your `.env` file or deployment environment:

```bash
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_OAUTH_CLIENT_ID=your_oauth_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_oauth_client_secret
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
JWT_SECRET=your_jwt_secret_min_32_chars
```

### 4. Local Webhook Testing

For local development, use ngrok or cloudflared to expose your webhook endpoint:

**Using ngrok:**

```bash
ngrok http 8000
# Use the HTTPS URL in GitHub App webhook settings
```

**Using cloudflared:**

```bash
cloudflared tunnel --url http://localhost:8000
```

Update your GitHub App webhook URL to the provided tunnel URL.

## API Endpoints

### Authentication

- `GET /auth/github` - Start GitHub OAuth flow
- `GET /auth/callback` - OAuth callback handler

### User & Repos

- `GET /api/me` - Get current user profile and managed repos
- `GET /api/repos` - List user's managed repositories
- `GET /api/repos/{owner}/{repo}` - Get repository details
- `GET /api/repos/{owner}/{repo}/install` - Get GitHub App installation URL

### Issues

- `GET /api/repos/{owner}/{repo}/issues` - List issues
- `GET /api/repos/{owner}/{repo}/issues/{issue_number}` - Get issue with checklist
- `POST /api/repos/{owner}/{repo}/issues/{issue_number}/regenerate` - Regenerate checklist

### Pull Requests

- `GET /api/repos/{owner}/{repo}/prs/{pr_number}` - Get PR details
- `POST /api/repos/{owner}/{repo}/prs/{pr_number}/revalidate` - Revalidate PR
- `POST /api/repos/{owner}/{repo}/prs/{pr_number}/flag_for_merge` - Flag for merge (audit log)

### Notifications

- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/{id}/read` - Mark notification as read

### Webhooks

- `POST /webhooks/github` - GitHub webhook receiver

### Health

- `GET /health` - Health check endpoint

## API Examples

### Get Current User

```bash
curl -X GET "http://localhost:8000/api/me" \
  -H "Cookie: quantum_session=your_jwt_token"
```

Response:
```json
{
  "id": "1",
  "login": "username",
  "avatar_url": "https://...",
  "name": "User Name",
  "email": "user@example.com",
  "managed_repos": ["owner/repo1", "owner/repo2"]
}
```

### Get Repository Issues

```bash
curl -X GET "http://localhost:8000/api/repos/owner/repo/issues" \
  -H "Cookie: quantum_session=your_jwt_token"
```

### Regenerate Checklist

```bash
curl -X POST "http://localhost:8000/api/repos/owner/repo/issues/42/regenerate" \
  -H "Cookie: quantum_session=your_jwt_token"
```

Response:
```json
{
  "status": "accepted",
  "job_id": "job-id-here"
}
```

### Get PR Details

```bash
curl -X GET "http://localhost:8000/api/repos/owner/repo/prs/123" \
  -H "Cookie: quantum_session=your_jwt_token"
```

## CI Contract

For repositories using QuantumReview, the CI workflow must follow this contract:

### Artifact Requirements

1. **JUnit Test Report**: Upload as `autoqa-test-report.xml`
   - Location: `artifacts/autoqa/autoqa-test-report.xml`
   - Format: Standard JUnit XML

2. **Code Health Report** (optional): Upload as `code_health.json`
   - Location: `artifacts/autoqa/code_health.json`
   - Format: JSON with `findings` array

### Test ID Convention

Tests must embed their test ID in one of these formats:

1. **In testcase name**: `TID::test_name`
   ```xml
   <testcase name="T1::test_signup_email_validation" ...>
   ```

2. **In classname**: `autoqa:TID`
   ```xml
   <testcase name="test_jwt_verify" classname="autoqa:T4" ...>
   ```

### Example GitHub Actions Workflow

```yaml
name: Tests

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          pytest --junitxml=artifacts/autoqa/autoqa-test-report.xml
      
      - name: Upload test report
        uses: actions/upload-artifact@v3
        with:
          name: autoqa-test-report
          path: artifacts/autoqa/autoqa-test-report.xml
```

## Database Migrations

### Create a new migration:

```bash
alembic revision --autogenerate -m "Description"
```

### Apply migrations:

```bash
alembic upgrade head
```

### Rollback:

```bash
alembic downgrade -1
```

## Testing

### Run all tests:

```bash
pytest tests/ -v
```

### Run with coverage:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Run specific test:

```bash
pytest tests/test_parser.py::test_extract_acceptance_criteria_with_section -v
```

## Deployment

### Render.com

1. **Create new Web Service:**
   - Build Command: `cd backend && pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `cd backend && gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

2. **Create Worker Service:**
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && python -m app.workers.worker`

3. **Set environment variables** in Render dashboard

4. **Configure PostgreSQL and Redis** services in Render

The `render.yaml` file is provided for automated setup.

### Other Platforms

The application can be deployed to any platform supporting:
- Python 3.11+
- PostgreSQL 13+
- Redis 7+

Key requirements:
- Run migrations on startup
- Set all required environment variables
- Ensure webhook URL is publicly accessible
- Run worker process separately

## Architecture

### Background Jobs

Jobs are processed by RQ workers:

- `generate_checklist`: Parse issue and create checklist
- `generate_test_manifest`: Analyze PR diff and generate test manifest
- `process_workflow_run`: Download artifacts, parse JUnit, map tests
- `run_code_health_scan`: Process code health artifacts
- `handle_installation`: Process GitHub App installation events

### Token Caching

GitHub App installation tokens are cached in Redis with TTL matching token expiration. Keys:
- `gh:install:{installation_id}:token`
- `gh:install:{installation_id}:expires_at`

### Webhook Idempotency

Webhook deliveries are deduplicated using `X-GitHub-Delivery` header, stored in Redis with 1-hour TTL.

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` format: `postgresql+asyncpg://...`
- Check PostgreSQL is running and accessible
- Verify database exists

### Redis Connection Issues

- Verify `REDIS_URL` format: `redis://host:port/0`
- Check Redis is running
- Test connection: `redis-cli ping`

### Webhook Not Received

- Verify webhook URL is publicly accessible
- Check webhook secret matches
- Verify HMAC signature in logs
- Check GitHub App webhook delivery logs

### Background Jobs Not Processing

- Verify worker is running: `python -m app.workers.worker`
- Check Redis connection
- Review worker logs for errors
- Verify job queue name matches (`default`)

## License

[Your License Here]

## Support

For issues and questions, please open an issue in the repository.

