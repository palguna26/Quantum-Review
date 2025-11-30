# Workflows

## Login & Repo Selection

- User clicks “Sign in with GitHub”
- Backend handles OAuth and sets a session cookie
- Dashboard lists managed repos from DB
- If empty, user selects a GitHub App installation and views accessible repos

## Issue → Checklist Generation

- On issue open webhook, backend extracts acceptance criteria and stores checklist items
- Items include `id`, `text`, `required`, `status`, and `linked_tests`
- Users can regenerate or update statuses via API

## PR → Validation Against Checklist

- On PR events, backend generates a test manifest and may process CI artifacts
- Validation compares PR diff/context against checklist items and records per-item status
- Provides summary, score, suggested tests, and coverage advice (when available)

## Vulnerability Scans & Health Metrics

- CI runs scanners (e.g., `pip-audit`, `bandit`, `npm audit`) and publishes JSON artifacts
- Backend parses and aggregates into repo health metrics
- Frontend displays health score and findings in a repo page

