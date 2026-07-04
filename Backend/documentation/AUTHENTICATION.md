# Authentication — Clerk JWT RS256 Flow

## Overview

The HRMS backend uses **Clerk** as a managed authentication service. Every API request carries a JWT signed with RS256. The backend verifies tokens locally using Clerk's public key, with real-time API verification for admin role checks to prevent stale-token privilege escalation.

## Authentication Flow

```
Client → Clerk (login) → JWT issued → Client sends JWT in Authorization header
                                          ↓
                                   FastAPI Bearer extraction
                                          ↓
                                   JWT decode (RS256, local)
                                          ↓
                                   TokenPayload(user_id, role)
                                          ↓
                                   ┌──── admin? ────┐
                                   │                 │
                              require_admin    get_current_user
                                   │                 │
                          Clerk API live check    Return payload
                          (Redis-cached 2min)
```

## JWT Structure

Clerk issues JWTs in standard three-part format:

```
xxxxx.yyyyy.zzzzz
│       │       │
│       │       └─ Signature (RS256)
│       └───────── Payload (claims)
└───────────────── Header (algorithm, key ID)
```

### Claims

| Claim | Source | Description |
|-------|--------|-------------|
| `sub` | Clerk user ID | Unique user identifier (`user_xxxxx`) |
| `metadata.role` | `public_metadata.role` | `"admin"` or `"employee"` (defaults to `"employee"`) |
| `exp` | Clerk-issued | Expiration timestamp (default TTL: **15 minutes**) |
| `iat` | Clerk-issued | Issued-at timestamp |
| `iss` | Clerk | Issuer URL (not verified client-side) |

### Token Payload Extraction

```python
# app/core/auth.py:58-85
def decode_jwt(token: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        CLERK_PEM_KEY,
        algorithms=["RS256"],
        options={"verify_aud": False, "verify_exp": True},
    )
    user_id = payload.get("sub", "")
    metadata = payload.get("metadata", {})
    role = metadata.get("role", "employee")
    # Clamp to allowed roles
    if role not in ("admin", "employee"):
        role = "employee"
    return TokenPayload(user_id=user_id, role=role, raw_payload=payload)
```

## Role Extraction

Roles are stored in Clerk's `public_metadata` field and embedded in the JWT:

1. **At login**, Clerk encodes `metadata.role` into the JWT payload.
2. **At verification**, `decode_jwt()` extracts `metadata.role` from the decoded payload.
3. **Clamping**: Any role value not in `{"admin", "employee"}` defaults to `"employee"`.
4. **Fallback**: If `metadata` is missing or not a dict, role defaults to `"employee"`.

## Stale Token Protection

JWTs have a **15-minute TTL**. If an admin is demoted between token issuance and expiry, the stale token still carries `role=admin`. This is mitigated by real-time Clerk API verification:

```python
# app/core/auth.py:88-119
async def verify_admin_role_live(clerk_user_id: str) -> bool:
    cache_key = f"role_verified:{clerk_user_id}"
    cached = await redis_manager.get(cache_key)
    if cached is not None:
        return cached == "admin"  # Cache hit — skip API call

    # Call Clerk API
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
        )
    user_data = resp.json()
    role = user_data.get("public_metadata", {}).get("role", "employee")

    # Cache for 2 minutes
    await redis_manager.setex(cache_key, settings.CACHE_ROLE_VERIFICATION_TTL, role)
    return role == "admin"
```

### Flow

1. JWT says `role=admin` → call `verify_admin_role_live()`.
2. Check Redis cache (`role_verified:{user_id}`).
3. **Cache hit**: return cached role (skip API call).
4. **Cache miss**: call Clerk API → get `public_metadata.role` → cache for 2 minutes.
5. If Clerk API fails, **fail closed** (return `False` — admin access denied).

## Redis Caching of Role Verification

| Property | Value |
|----------|-------|
| Cache key pattern | `role_verified:{clerk_user_id}` |
| TTL | 120 seconds (2 minutes) |
| Stored value | `"admin"` or `"employee"` |
| Invalidation | On role change via webhook (`_handle_user_updated`) |
| Fail-closed | If Clerk API unreachable, deny admin access |

## Token TTL

- **Default**: 15 minutes (`CLERK_JWT_TTL_MINUTES` in `config.py:80`)
- **Range**: 1–60 minutes (validated by pydantic)
- **Enforcement**: Local JWT `exp` claim verification via `PyJWT`

## FastAPI Dependencies

### `get_current_user`

Extracts and validates the JWT from the `Authorization: Bearer <token>` header. Returns `TokenPayload` with `user_id` and `role`.

```python
@app.get("/dashboard")
async def dashboard(user: TokenPayload = Depends(get_current_user)):
    ...
```

**Behavior**:
- Returns 401 if no credentials provided.
- Returns 401 if token is expired or invalid.
- Does NOT perform live Clerk verification (performance optimization).

### `require_admin`

Extends `get_current_user` with admin role verification. Performs live Clerk API check to catch stale tokens.

```python
@app.get("/admin/employees")
async def list_all(user: TokenPayload = Depends(require_admin)):
    ...
```

**Behavior**:
- Returns 403 if JWT role is not `admin` AND live verification fails.
- Returns 403 if JWT role is `admin` but live verification says otherwise (demotion).
- Invalidates Redis cache on role changes.

### `get_optional_user`

Extracts user if present, returns `None` if not. Useful for public endpoints with optional personalization.

```python
@app.get("/public/announcements")
async def announcements(user: TokenPayload | None = Depends(get_optional_user)):
    if user:
        # personalized
    ...
```

**Behavior**:
- Returns `None` if no credentials or token invalid/expired.
- Never raises 401.

## Role Hierarchy

```
admin
  └── Full access: employee CRUD, leave approval, payroll generation,
      attendance override, dashboard analytics

employee
  └── Self-service: attendance, leave requests, profile, chat,
      payroll view (own only)
```

## Key Configuration

| Setting | Env Variable | Default |
|---------|-------------|---------|
| JWT verification key | `CLERK_JWT_VERIFICATION_KEY` | — (required) |
| Token TTL | `CLERK_JWT_TTL_MINUTES` | 15 |
| Role cache TTL | `CACHE_ROLE_VERIFICATION_TTL` | 120s |
| Clerk secret key | `CLERK_SECRET_KEY` | — (required) |

## Security Considerations

- **Never store Clerk secret key in source code.** Always use environment variables.
- **PEM key normalization**: Handles escaped `\n` from `.env` files automatically.
- **RS256**: Asymmetric signing — only Clerk can sign, backend only verifies with public key.
- **Fail-closed**: If Clerk API is unreachable, admin verification fails (denies access).
- **No audience verification**: `verify_aud` is disabled since Clerk doesn't set a consistent audience claim.
