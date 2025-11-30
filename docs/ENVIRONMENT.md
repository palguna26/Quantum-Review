# Environment Variables

All configuration is loaded via `.env`.

## Core

- `DATABASE_URL` – PostgreSQL URL (async): `postgresql+asyncpg://user:pass@host:5432/db`
- `REDIS_URL` – Redis connection URL
- `JWT_SECRET` – long, random secret for session tokens
- `DEBUG` – `true/false`
- `RENDER` – `true/false` (enables JSON logging)

## Origins & CORS

- `BACKEND_ORIGIN` – e.g., `http://localhost:8000` or your Render URL
- `FRONTEND_ORIGIN` – e.g., `http://localhost:8080` or your Vercel/Netlify URL
- `CORS_ORIGINS` – JSON array of allowed origins

## GitHub OAuth

- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_CLIENT_SECRET`
- Callback: `${BACKEND_ORIGIN}/auth/callback`

## GitHub App

- `GITHUB_APP_ID`
- `GITHUB_PRIVATE_KEY` – PEM private key (multiline-safe with `\n`)
- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_API_BASE` – default `https://api.github.com`

## LLM (optional)

- `LLM_PROVIDER` – e.g., `openai`
- `LLM_API_KEY`

## Frontend

- `VITE_API_BASE` – e.g., `/api` locally or full backend URL in production

