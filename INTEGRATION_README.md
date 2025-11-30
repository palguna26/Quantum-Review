# QuantumReview Frontend-Backend Integration Guide

This guide provides complete setup instructions for integrating the React frontend with the FastAPI backend.

## Quick Start

### Backend Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment variables:**
Create a `.env` file in the `backend` directory:

```bash
# GitHub OAuth (for user authentication)
GITHUB_OAUTH_CLIENT_ID=your_github_oauth_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_oauth_client_secret

# GitHub App (for repository access)
GITHUB_APP_ID=your_github_app_id
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/quantumreview

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your_jwt_secret_min_32_chars_long

# Frontend Origin (optional, defaults to first CORS_ORIGIN)
FRONTEND_ORIGIN=http://localhost:8080

# Optional: LLM Configuration
LLM_PROVIDER=openai  # or anthropic, etc.
LLM_API_KEY=your_llm_api_key
```

3. **Run database migrations:**
```bash
cd backend
alembic upgrade head
```

4. **Start backend:**
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker Compose
docker-compose up -d
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies:**
```bash
cd quantum-review-frontend
npm install
```

2. **Configure environment (optional):**
Create `.env.local` file:

```bash
# API Base URL (defaults to /api which uses Vite proxy)
VITE_API_BASE=/api
```

3. **Start frontend:**
```bash
npm run dev
```

Frontend will be available at: `http://localhost:8080`

## Architecture Overview

### Authentication Flow

1. User clicks "Sign in with GitHub" → redirects to `/auth/github`
2. Backend redirects to GitHub OAuth
3. GitHub redirects back to `/auth/callback` with code
4. Backend exchanges code for access token, creates/updates user, issues JWT
5. Backend redirects to frontend `/auth/callback?token=<jwt>`
6. Frontend stores JWT in localStorage
7. Frontend redirects to dashboard

### API Communication

- **Base URL**: `/api` (proxied to `http://localhost:8000/api` in dev)
- **Authentication**: Bearer token in `Authorization` header OR cookie
- **Token Storage**: localStorage (for Bearer token) or httpOnly cookie (set by backend)

### Real-Time Updates (SSE)

- **Endpoint**: `/events/stream`
- **Protocol**: Server-Sent Events
- **Events**: `issue_updated`, `checklist_ready`, `pr_validated`, etc.
- **Connection**: Managed by `useSSE` hook

## API Endpoints

### Authentication
- `GET /auth/github` - Start GitHub OAuth flow
- `GET /auth/callback?code=<code>` - OAuth callback handler

### User & Repos
- `GET /api/me` - Get current user profile
- `GET /api/repos` - List user's repositories
- `GET /api/repos/{owner}/{repo}` - Get repository details

### Issues
- `GET /api/repos/{owner}/{repo}/issues` - List issues
- `GET /api/repos/{owner}/{repo}/issues/{issue_number}` - Get issue with checklist
- `PATCH /api/repos/{owner}/{repo}/issues/{issue_number}/checklist/{item_id}` - Update checklist item
- `POST /api/repos/{owner}/{repo}/issues/{issue_number}/regenerate` - Regenerate checklist

### Pull Requests
- `GET /api/repos/{owner}/{repo}/prs/{pr_number}` - Get PR details
- `POST /api/repos/{owner}/{repo}/prs/{pr_number}/revalidate` - Revalidate PR

### Notifications
- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/{id}/read` - Mark notification as read

### Real-Time Events
- `GET /events/stream` - SSE stream for real-time updates

### Webhooks
- `POST /webhooks/github` - GitHub webhook receiver

## Testing the Integration

### 1. Test Authentication

```bash
# Start OAuth flow (opens in browser)
curl -L http://localhost:8000/auth/github

# After GitHub redirect, you'll get a JWT token
# Test authenticated endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/me
```

### 2. Test API Endpoints

```bash
# Get user profile
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/me

# List repositories
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/repos

# Get issues for a repo
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos/owner/repo/issues
```

### 3. Test Webhook (with signature)

```bash
# Generate signature (requires webhook secret)
payload='{"action":"opened","issue":{"number":123}}'
signature=$(echo -n "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

curl -X POST http://localhost:8000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$signature" \
  -H "X-GitHub-Delivery: test-delivery-id" \
  -H "X-GitHub-Event: issues" \
  -d "$payload"
```

### 4. Test SSE Connection

```bash
# Connect to SSE stream (requires authentication)
curl -N -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/events/stream
```

## Example Frontend Usage

### Using the API Client

```typescript
import { api } from '@/lib/api';

// Get user profile
const user = await api.getMe();

// List repositories
const repos = await api.getRepos();

// Get issues
const issues = await api.getIssues('owner', 'repo');

// Update checklist item
await api.updateChecklistItem('owner', 'repo', 123, 'c1', 'passed');
```

### Using SSE for Real-Time Updates

```typescript
import { useSSE } from '@/hooks/useSSE';

function Dashboard() {
  useSSE((event) => {
    console.log('Event received:', event);
    
    if (event.type === 'issue_updated') {
      // Refresh issues list
      refetchIssues();
    }
  }, ['issue_updated', 'checklist_ready']);
  
  // ... component code
}
```

## Security Considerations

### Token Storage

**Option 1: Bearer Token (Current Implementation)**
- Stored in `localStorage`
- Sent in `Authorization` header
- ✅ Works with all APIs
- ⚠️ Vulnerable to XSS (mitigated with CSP headers)

**Option 2: HttpOnly Cookie (Recommended for Production)**
- Backend sets cookie after OAuth
- Cookie is httpOnly, secure, sameSite
- ✅ More secure (not accessible to JavaScript)
- ⚠️ Requires CORS credentials

To switch to httpOnly cookies:
1. Backend already sets cookie in `/auth/callback`
2. Remove `Authorization` header from frontend
3. Ensure `withCredentials: true` in axios config (already set)
4. Backend `get_current_user` already checks cookies

### CORS Configuration

Backend allows these origins (configured in `app/config.py`):
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (alternative)
- `http://localhost:8080` (frontend port)

### Rate Limiting

Simple in-memory rate limiter included (60 requests/minute per IP).
For production, use Redis-based rate limiting.

## Deployment

### Backend (Render.com example)

1. Set all environment variables in Render dashboard
2. Build command: `cd backend && pip install -r requirements.txt && alembic upgrade head`
3. Start command: `cd backend && gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### Frontend (Vercel/Netlify example)

1. Build command: `cd quantum-review-frontend && npm run build`
2. Output directory: `quantum-review-frontend/dist`
3. Environment variable: `VITE_API_BASE=https://your-backend-url.com/api`

## Troubleshooting

### CORS Errors

- Ensure frontend origin is in `CORS_ORIGINS` list
- Check `withCredentials: true` in axios config
- Verify backend is setting `Access-Control-Allow-Credentials: true`

### Authentication Issues

- Check JWT token is valid: `jwt.decode(token, secret)`
- Verify token expiration
- Ensure backend `/auth/callback` redirects with token

### SSE Not Connecting

- Check browser console for connection errors
- Verify authentication token is valid
- Ensure Redis is running (required for pub/sub)
- Check network tab for `/events/stream` connection

### Webhook Not Receiving Events

- Verify webhook secret matches GitHub App settings
- Check signature validation logs
- Ensure webhook URL is publicly accessible
- Test with ngrok for local development: `ngrok http 8000`

## Next Steps

1. ✅ Authentication with GitHub OAuth
2. ✅ API endpoints for repos, issues, PRs
3. ✅ SSE for real-time updates
4. ✅ Webhook handling
5. ✅ Checklist updates
6. ⏳ Background job processing (RQ workers)
7. ⏳ LLM integration for checklist generation
8. ⏳ Health score calculation
9. ⏳ Test manifest generation

## Testing

See `INTEGRATION_TEST_EXAMPLES.md` for:
- cURL examples for all endpoints
- Postman collection setup
- Python test examples
- Webhook testing with ngrok

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

## Support

For issues and questions, check the backend README (`backend/README.md`) or open an issue in the repository.

