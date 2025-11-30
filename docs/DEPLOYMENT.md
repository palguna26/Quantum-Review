# Deployment

## Backend on Render

- Create a new Web Service pointing to the backend directory.
- Start command (Render): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `DATABASE_URL` (Render Postgres connection string)
  - `REDIS_URL` (Render Redis or external)
  - `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`
  - `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`
  - `JWT_SECRET`
  - `BACKEND_ORIGIN` and `FRONTEND_ORIGIN`
  - `CORS_ORIGINS` (JSON array, e.g., `["https://your-frontend.app"]`)

## PostgreSQL on Render

- Create a managed Postgres instance.
- Use the connection string as `DATABASE_URL`; ensure `+asyncpg` for async driver in the backend.
- Run migrations with Alembic against the database.

## Frontend on Vercel/Netlify

- Build command: `npm run build`
- Environment variables:
  - `VITE_API_BASE` (e.g., `https://your-backend.onrender.com/api`)
- Ensure CORS and cookies (SameSite/Lax) are compatible with your deployment domains.

## Notes

- In production, set `SESSION_COOKIE_SECURE=true`.
- Keep secrets out of logs. Use `DEBUG=false`.
- Monitor health via `/health` endpoint.

