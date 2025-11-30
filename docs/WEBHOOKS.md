# Webhooks

## Endpoint

- `POST /webhooks/github` – verifies signature and dispatches events.

## Signature Verification

- Uses `X-Hub-Signature-256` header with HMAC SHA-256.
- Secret: `GITHUB_WEBHOOK_SECRET`.
- Reject invalid signatures with 401.
- Duplicate deliveries are deduplicated via Redis TTL.

## Events

- `installation` – created/deleted
- `installation_repositories` – repositories added/removed
- `pull_request` – opened/synchronize/reopened/closed
- `workflow_run` – completed (artifacts mapping)

## Processing

- Route handler is thin; tasks are queued via Redis/RQ workers.
- Sync installation + repo metadata, generate test manifests, process workflow artifacts.

## Local Development

- Use `ngrok` to expose your backend: `ngrok http 8000`
- Update your GitHub App webhook URL to the public tunnel.

