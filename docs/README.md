# QuantumReview

Modern GitHub code review & repo health platform.

## Features

- GitHub OAuth login and GitHub App integration
- Webhooks for installations, repositories, PRs, and workflow runs
- LLM-powered issue checklists and PR validation
- Vulnerability scanning and repo health metrics
- Secure defaults, strong typing, tests, and clean architecture

## Stack

- Backend: FastAPI (Python) + PostgreSQL + Redis
- Frontend: React + Vite + Tailwind (Lovable UI)
- Integrations: GitHub App + OAuth

## Quick Start (Local)

- Prerequisites: `Python 3.11+`, `Node 18+`, `PostgreSQL`, `Redis`

1) Backend setup
- Copy `.env.example` to `.env` and fill values
- Create database and run migrations
  - Ensure `DATABASE_URL` points to your local db
  - Install Alembic: `pip install alembic`
  - Run: `alembic upgrade head`
- Start API: `uvicorn app.main:app --reload --port 8000`

2) Frontend setup
- `cd frontend && npm install`
- `npm run dev` (default `http://localhost:8080`)

## Configuration

- See `docs/ENVIRONMENT.md` for all environment variables
- Important:
  - `BACKEND_ORIGIN` and `FRONTEND_ORIGIN` must match actual URLs
  - OAuth callback is `${BACKEND_ORIGIN}/auth/callback`
  - Set GitHub OAuth client and GitHub App credentials

## GitHub Integration

- User logs in via OAuth; backend creates a session token and redirects to frontend
- Installations and repos are listed using GitHub App installation tokens
- When dashboard has no local repos, frontend queries `/api/github/installations` and `/api/github/installations/{id}/repos`

## Webhooks

- `POST /webhooks/github` verifies HMAC SHA-256 signature via `X-Hub-Signature-256`
- Handles events: `installation`, `installation_repositories`, `pull_request`, `workflow_run`
- Enqueues tasks via Redis/RQ; syncs installation/repo metadata and generates test manifests

## LLM & Validation

- Issue → checklist generation stored in DB
- PR → validation against checklist, plus code health findings

## Deployment

- See `docs/DEPLOYMENT.md` for Render (backend & Postgres) and Vercel/Netlify (frontend)
- Ensure CORS and origins are configured correctly

