# Clerk Setup Guide

## Overview

Clerk handles all authentication for the HRMS. This guide walks through creating a Clerk application, configuring JWT templates, webhooks, and role metadata.

## 1. Account Creation

1. Go to [https://clerk.com](https://clerk.com) and sign up.
2. Create a new application.
3. Select your authentication methods (email + password, Google, etc.).
4. Note the **Publishable Key** and **Secret Key** from the dashboard.

## 2. Dashboard Configuration

### API Keys

Navigate to **Configure → API Keys** in the Clerk dashboard:

| Key | Format | Usage |
|-----|--------|-------|
| Publishable Key | `pk_test_...` or `pk_live_...` | Frontend (Next.js) |
| Secret Key | `sk_test_...` or `sk_live_...` | Backend (FastAPI) — never expose to client |

### JWT Templates

1. Navigate to **Configure → JWT Templates**.
2. Create a new template named `hrms-backend`.
3. Configure the claims:

```json
{
  "metadata": "{{user.public_metadata}}",
  "email": "{{user.primary_email_address}}"
}
```

4. Set the signing algorithm to **RS256**.
5. Copy the **Public Key** (PEM format) — this goes into `CLERK_JWT_VERIFICATION_KEY`.

## 3. JWT Verification Key Setup

The PEM public key is used by FastAPI to verify JWTs locally without calling Clerk:

1. In the Clerk dashboard, go to **Configure → JWT Templates → hrms-backend**.
2. Click **PEM format** to reveal the full public key.
3. Copy the entire block including headers:

```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
...
-----END PUBLIC KEY-----
```

4. Set it in `.env`:

```bash
CLERK_JWT_VERIFICATION_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjAN...\n-----END PUBLIC KEY-----"
```

> **Note**: The backend automatically handles escaped `\n` from `.env` files. Both literal newlines and `\n` escape sequences work.

## 4. Webhook Configuration

### Create Webhook

1. Navigate to **Configure → Webhooks** in the Clerk dashboard.
2. Click **Add Endpoint**.
3. Set the endpoint URL:
   - **Development**: `http://localhost:8000/api/v1/webhooks/clerk`
   - **Production**: `https://yourdomain.com/api/v1/webhooks/clerk`
4. Copy the **Signing Secret** (format: `whsec_...`).

### Set Webhook Secret

```bash
CLERK_WEBHOOK_SECRET=whsec_your_signing_secret_here
```

### Subscribe to Events

Select the following events:

| Event | Purpose |
|-------|---------|
| `user.created` | Create employee record on signup |
| `user.updated` | Sync role/name/email changes |
| `user.deleted` | Soft-delete employee |
| `session.created` | Log session creation (informational) |
| `session.ended` | Log session end (informational) |

## 5. Role Metadata Setup

Roles are stored in Clerk's `public_metadata` field on the user object.

### Setting Roles via Clerk Dashboard

1. Navigate to **Users** in the Clerk dashboard.
2. Click a user → **Public Metadata** tab.
3. Add the `role` field:

```json
{
  "role": "admin"
}
```

Or for regular employees:

```json
{
  "role": "employee"
}
```

### Setting Roles via API

```bash
curl -X PATCH https://api.clerk.com/v1/users/user_xxxxx \
  -H "Authorization: Bearer sk_test_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "public_metadata": {
      "role": "admin"
    }
  }'
```

### Role Values

| Value | Access Level |
|-------|-------------|
| `"admin"` | Full access — employee management, leave approval, payroll, analytics |
| `"employee"` | Self-service — attendance, leave requests, profile, chat |

> **Note**: Any role value other than `"admin"` or `"employee"` defaults to `"employee"` at the backend level.

## 6. Environment Variables

Add all Clerk-related variables to your `.env` file:

```bash
# ── Clerk Authentication ───────────────────────────────────────
# From: Clerk Dashboard → Configure → API Keys
CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_key_here

# From: Clerk Dashboard → Configure → JWT Templates → hrms-backend → PEM format
CLERK_JWT_VERIFICATION_KEY="-----BEGIN PUBLIC KEY-----\nYOUR_KEY_HERE\n-----END PUBLIC KEY-----"

# From: Clerk Dashboard → Configure → Webhooks → Endpoint → Signing Secret
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `CLERK_PUBLISHABLE_KEY` | Yes | Frontend key (`pk_...`) |
| `CLERK_SECRET_KEY` | Yes | Backend API key (`sk_...`) — used for live role verification and Clerk API calls |
| `CLERK_JWT_VERIFICATION_KEY` | Yes | RSA public key (PEM) for local JWT verification |
| `CLERK_WEBHOOK_SECRET` | Yes | Webhook signing secret (`whsec_...`) for Svix signature verification |
| `CLERK_JWT_TTL_MINUTES` | No | Token TTL in minutes (default: 15, range: 1–60) |

## 7. Testing the Setup

### Verify JWT Verification

```bash
# 1. Sign in via Clerk frontend
# 2. Copy the JWT from the browser's network tab
# 3. Decode it at https://jwt.io and verify the claims include metadata.role

# 4. Test a protected endpoint
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:8000/api/v1/dashboard
```

### Verify Webhook

```bash
# Use Clerk's webhook test feature (dashboard → Webhooks → Send test event)
# Check backend logs for: "Clerk webhook received: type=user.created, id=..."
```

### Verify Live Role Check

```bash
# 1. Sign in as admin
# 2. Demote the user via Clerk dashboard (set role to "employee")
# 3. Try an admin endpoint — should get 403 within 2 minutes (cache TTL)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Token missing subject claim` | JWT doesn't contain `sub` — check JWT template includes standard claims |
| `Invalid JWT` | Wrong verification key — ensure PEM is correctly copied with newlines |
| `Admin access revoked` | Stale token — sign out and sign back in to get a fresh JWT |
| Webhook signature invalid | Wrong `CLERK_WEBHOOK_SECRET` — re-copy from Clerk dashboard |
| Employee not created on signup | Check webhook is subscribed to `user.created` event |
