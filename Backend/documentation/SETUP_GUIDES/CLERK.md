# Clerk Authentication Setup Guide

## Account Creation

1. Go to https://clerk.com/
2. Click "Get Started" or "Sign Up"
3. Enter your email address and create a password
4. Verify your email address
5. Complete the onboarding process

## Creating a New Application

1. After logging in, you'll see the Clerk Dashboard
2. Click "Create Application" or "+ New Application"
3. Enter a name for your application (e.g., "HRMS Backend")
4. Select your preferred authentication methods:
   - Email address
   - Phone number
   - Social providers (Google, GitHub, etc.)
5. Click "Create"

## Obtaining API Keys

### Find Your Keys
1. In the Clerk Dashboard, go to "API Keys" in the left sidebar
2. You'll see two types of keys:
   - **Publishable Key**: Safe to use in client-side code
   - **Secret Key**: Keep this confidential, use only server-side

### Copy Keys
```env
# .env file
CLERK_SECRET_KEY=sk_your_secret_key_here
CLERK_PUBLISHABLE_KEY=pk_your_publishable_key_here
```

### Key Formats
- **Secret Key**: Starts with `sk_` (e.g., `sk_live_...`)
- **Publishable Key**: Starts with `pk_` (e.g., `pk_live_...`)

## Setting Up JWT Verification Key

### Get JWT Verification Key
1. In Clerk Dashboard, go to "API Keys"
2. Scroll down to "JWT Templates" or "Advanced"
3. Find "JWT Verification Key" or "JWKS URL"
4. Copy the JWKS URL

### Configure in Application
```env
# .env file
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
```

### Verify JWT in Code
```python
import jwt
import requests

def verify_clerk_token(token: str):
    jwks_url = "https://your-app.clerk.accounts.dev/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    
    # Decode and verify the token
    # Use your preferred JWT verification method
```

## Configuring Webhooks

### Create Webhook
1. In Clerk Dashboard, go to "Webhooks" in the left sidebar
2. Click "Add Endpoint"
3. Enter your webhook URL (e.g., `https://your-domain.com/api/webhooks/clerk`)
4. Select events to subscribe to:
   - `user.created`
   - `user.updated`
   - `user.deleted`
   - `session.created`
   - `session.ended`
5. Click "Create"

### Webhook Secret
1. After creating the webhook, copy the "Signing Secret"
2. Add to your `.env` file:
```env
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Verify Webhook Signatures
```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str):
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Setting User Metadata (Role)

### In Clerk Dashboard
1. Go to "Users" in the left sidebar
2. Click on a user
3. Go to "Metadata" tab
4. Add public metadata:
```json
{
  "role": "admin"
}
```

### Available Roles
```json
{
  "role": "admin"      // Full access
  "role": "hr_manager" // HR management access
  "role": "employee"   // Basic employee access
  "role": "viewer"     // Read-only access
}
```

### Update Metadata via API
```python
import requests

def update_user_role(user_id: str, role: str):
    headers = {
        "Authorization": f"Bearer sk_your_secret_key",
        "Content-Type": "application/json"
    }
    
    data = {
        "public_metadata": {
            "role": role
        }
    }
    
    response = requests.patch(
        f"https://api.clerk.com/v1/users/{user_id}",
        headers=headers,
        json=data
    )
    return response.json()
```

## Testing Authentication

### Test Sign Up
1. Go to your application's sign-up page
2. Create a new account
3. Check Clerk Dashboard for the new user

### Test Sign In
1. Sign in with the created account
2. Verify the session is created

### Test API Endpoints
```bash
# Get authentication token from your frontend
TOKEN="your_session_token"

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/protected-endpoint
```

### Test Webhooks
```bash
# Use ngrok or similar to expose local endpoint
ngrok http 8000

# Update webhook URL in Clerk Dashboard
# Trigger events and check webhook logs
```

## Common Issues

### Invalid API Key
- Ensure you're using the correct key type (secret vs publishable)
- Check for typos in the key
- Ensure the key is for the correct environment (live vs test)

### JWT Verification Failed
- Check that JWKS URL is correct
- Ensure the token hasn't expired
- Verify the audience and issuer claims

### Webhook Not Receiving Events
- Check the webhook URL is accessible
- Verify the signing secret is correct
- Check webhook logs in Clerk Dashboard

### User Metadata Not Updating
- Ensure you have the correct permissions
- Check the metadata structure
- Verify the API call is successful

### CORS Issues
- Configure allowed origins in Clerk Dashboard
- Ensure your frontend domain is whitelisted

## Environment Variables Reference

```env
# Required
CLERK_SECRET_KEY=sk_your_secret_key
CLERK_PUBLISHABLE_KEY=pk_your_publishable_key
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json

# Optional (for webhooks)
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret
```

## Useful Resources

- Clerk Documentation: https://clerk.com/docs
- Clerk Dashboard: https://dashboard.clerk.com
- Clerk Community: https://clerk.com/community
