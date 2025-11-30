# Integration Test Examples

## cURL Examples

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Start OAuth Flow
```bash
# This will redirect to GitHub
curl -L http://localhost:8000/auth/github
```

### 3. Get User Profile (after authentication)
```bash
# Replace YOUR_JWT_TOKEN with actual token from OAuth callback
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/me
```

### 4. List Repositories
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos
```

### 5. Get Issues for a Repository
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos/owner/repo/issues
```

### 6. Get Issue Details with Checklist
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos/owner/repo/issues/123
```

### 7. Update Checklist Item Status
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "passed"}' \
  http://localhost:8000/api/repos/owner/repo/issues/123/checklist/c1
```

### 8. Regenerate Checklist
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos/owner/repo/issues/123/regenerate
```

### 9. Get PR Details
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/repos/owner/repo/prs/456
```

### 10. Test Webhook (with signature)
```bash
# Generate signature
WEBHOOK_SECRET="your_webhook_secret"
PAYLOAD='{"action":"opened","issue":{"number":123,"title":"Test Issue"},"repository":{"full_name":"owner/repo","id":12345}}'

# Calculate HMAC SHA256 signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

# Send webhook
curl -X POST http://localhost:8000/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -H "X-GitHub-Delivery: test-delivery-$(date +%s)" \
  -H "X-GitHub-Event: issues" \
  -d "$PAYLOAD"
```

### 11. Connect to SSE Stream
```bash
# Connect to Server-Sent Events stream
curl -N -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/events/stream
```

## Postman Collection

### Environment Variables
Create a Postman environment with:
- `base_url`: `http://localhost:8000`
- `jwt_token`: (set after OAuth flow)

### Example Requests

#### 1. Health Check
```
GET {{base_url}}/health
```

#### 2. Get User Profile
```
GET {{base_url}}/api/me
Authorization: Bearer {{jwt_token}}
```

#### 3. List Repositories
```
GET {{base_url}}/api/repos
Authorization: Bearer {{jwt_token}}
```

#### 4. Get Issues
```
GET {{base_url}}/api/repos/:owner/:repo/issues
Authorization: Bearer {{jwt_token}}
```

#### 5. Update Checklist Item
```
PATCH {{base_url}}/api/repos/:owner/:repo/issues/:issue_number/checklist/:item_id
Authorization: Bearer {{jwt_token}}
Content-Type: application/json

{
  "status": "passed"
}
```

#### 6. Test Webhook
```
POST {{base_url}}/webhooks/github
Content-Type: application/json
X-Hub-Signature-256: sha256={{signature}}
X-GitHub-Delivery: test-delivery-123
X-GitHub-Event: issues

{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Test Issue"
  },
  "repository": {
    "full_name": "owner/repo",
    "id": 12345
  }
}
```

## Python Test Example

```python
import httpx
import asyncio

async def test_api():
    base_url = "http://localhost:8000"
    token = "YOUR_JWT_TOKEN"  # Get from OAuth callback
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Get user profile
        response = await client.get(f"{base_url}/api/me", headers=headers)
        print("User:", response.json())
        
        # List repos
        response = await client.get(f"{base_url}/api/repos", headers=headers)
        print("Repos:", response.json())
        
        # Get issues
        response = await client.get(
            f"{base_url}/api/repos/owner/repo/issues",
            headers=headers
        )
        print("Issues:", response.json())

asyncio.run(test_api())
```

## JavaScript/Frontend Test

```javascript
// Using fetch API
const token = localStorage.getItem('quantum_auth_token');

// Get user profile
const response = await fetch('/api/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const user = await response.json();
console.log('User:', user);

// Update checklist item
await fetch('/api/repos/owner/repo/issues/123/checklist/c1', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ status: 'passed' })
});
```

## Webhook Testing with ngrok

For local webhook testing:

1. Start ngrok:
```bash
ngrok http 8000
```

2. Use the ngrok HTTPS URL in GitHub App webhook settings:
```
https://your-ngrok-url.ngrok.io/webhooks/github
```

3. Test webhook:
```bash
# From GitHub or using curl as shown above
```

