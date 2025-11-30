# GitHub Setup

## OAuth App

- Create a GitHub OAuth App:
  - Homepage URL: your frontend origin (e.g., `http://localhost:8080`)
  - Authorization callback URL: `${BACKEND_ORIGIN}/auth/callback` (e.g., `http://localhost:8000/auth/callback`)
  - Scopes: `read:user`, `user:email`
- Record `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` in backend `.env`.

## GitHub App

- Create a GitHub App for repository access:
  - Permissions:
    - Repository permissions: Contents (Read), Metadata (Read), Issues (Read), Pull requests (Read), Actions (Read)
    - Organization permissions: Members (Read) if needed
  - Webhook URL: `${BACKEND_ORIGIN}/webhooks/github`
  - Webhook secret: set `GITHUB_WEBHOOK_SECRET`
  - Generate a Private Key and store as `GITHUB_PRIVATE_KEY` in `.env` (PEM, multiline-safe)
  - App ID: `GITHUB_APP_ID`
  - Install the App on your account/org (all or selected repos)

## Installation Tokens

- The backend uses installation access tokens to list repositories:
  - `POST /app/installations/{installation_id}/access_tokens`
  - `GET /installation/repositories`

## Testing Locally

- For webhooks, use a tunneling solution (e.g., `ngrok`) to expose your `BACKEND_ORIGIN` to GitHub.
- Ensure your environment variables match the actual URLs.

