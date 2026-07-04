# JWT — Structure, Verification, and Key Rotation

## Overview

The HRMS uses JSON Web Tokens (JWT) for stateless authentication. Clerk issues tokens signed with **RS256** (RSA Signature with SHA-256). The backend verifies tokens locally using Clerk's RSA public key, eliminating per-request network calls to Clerk.

## JWT Structure

A JWT consists of three Base64URL-encoded parts separated by dots:

```
Header.Payload.Signature
```

### Header

```json
{
  "alg": "RS256",
  "kid": "key_xxxxx",
  "typ": "JWT"
}
```

| Field | Description |
|-------|-------------|
| `alg` | Signing algorithm — always `RS256` |
| `kid` | Key ID — Clerk's signing key identifier |
| `typ` | Token type — `JWT` |

### Payload

```json
{
  "sub": "user_2abc123xyz",
  "metadata": {
    "role": "admin"
  },
  "exp": 1719900000,
  "iat": 1719899100,
  "iss": "https://clerk.your-app.com"
}
```

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | Clerk user ID (`user_xxxxx`) — unique identifier |
| `metadata` | object | User metadata from Clerk `public_metadata` |
| `metadata.role` | string | User role: `"admin"` or `"employee"` |
| `exp` | number | Expiration timestamp (Unix epoch) |
| `iat` | number | Issued-at timestamp (Unix epoch) |
| `iss` | string | Issuer URL (Clerk instance URL) |

### Signature

```
RS256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  RSA_PRIVATE_KEY
)
```

The signature ensures:
- **Integrity**: Payload hasn't been tampered with.
- **Authenticity**: Token was signed by Clerk (only Clerk has the private key).

## RS256 Algorithm

RS256 is an asymmetric signing algorithm:

| Property | Value |
|----------|-------|
| Algorithm | RSA Signature with SHA-256 |
| Key type | Asymmetric (public/private pair) |
| Signing | Clerk holds the **private key** |
| Verification | Backend holds the **public key** |
| Security | Much stronger than HS256 — private key never leaves Clerk |

### Why RS256 over HS256?

- **HS256** (symmetric): Same key signs and verifies. If the key leaks, anyone can forge tokens.
- **RS256** (asymmetric): Only Clerk can sign. The backend only needs the public key to verify. Key compromise on one side doesn't compromise the other.

## Claims

### `sub` (Subject)

The unique Clerk user ID. Used to:
- Look up the employee record (`Employee.clerk_id`).
- Verify admin role via Clerk API.
- Index Redis cache keys.

### `metadata.role`

Extracted from `public_metadata.role` in the Clerk user object. Clamped to allowed values:

```python
role = metadata.get("role", "employee")
if role not in ("admin", "employee"):
    role = "employee"
```

### `exp` (Expiration)

Token expiry timestamp. Enforced by `PyJWT`:

```python
jwt.decode(
    token,
    key,
    algorithms=["RS256"],
    options={"verify_exp": True},  # Default: True
)
```

If expired, `jwt.ExpiredSignatureError` is raised → mapped to `TokenExpiredError` (HTTP 401).

### `iat` (Issued At)

Token creation timestamp. Not actively used by the backend, but present for auditing and debugging.

## Verification Flow

```
Incoming JWT
    │
    ▼
Extract from Authorization header (Bearer scheme)
    │
    ▼
Decode header → verify algorithm is RS256
    │
    ▼
Verify signature against Clerk's RSA public key (CLERK_JWT_VERIFICATION_KEY)
    │
    ▼
Check `exp` claim → reject if expired
    │
    ▼
Extract `sub` → user_id
    │
    ▼
Extract `metadata.role` → clamp to {admin, employee}
    │
    ▼
Return TokenPayload(user_id, role)
```

### Code Reference

```python
# app/core/auth.py:58-85
def decode_jwt(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            CLERK_PEM_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(str(exc))

    user_id = payload.get("sub", "")
    metadata = payload.get("metadata", {})
    role = metadata.get("role", "employee")
    if role not in ("admin", "employee"):
        role = "employee"

    return TokenPayload(user_id=user_id, role=role, raw_payload=payload)
```

### PEM Key Normalization

Clerk's PEM key in `.env` may use escaped newlines (`\n`). The backend handles both formats:

```python
def _parse_pem_key(raw: str) -> str:
    key = raw.strip()
    if "\\n" in key and "\n" not in key:
        key = key.replace("\\n", "\n")
    return key
```

## Key Rotation Considerations

### Current State

The backend uses a single RSA public key loaded at startup from `CLERK_JWT_VERIFICATION_KEY`. This key is static and must be manually rotated.

### Rotation Procedure

When rotating Clerk's JWT signing key:

1. **Generate new key** in Clerk dashboard (Configure → JWT Templates → Regenerate Key).
2. **Add new key to `.env`** as `CLERK_JWT_VERIFICATION_KEY`.
3. **Deploy updated backend** — all new instances use the new key.
4. **Keep old key** available until all existing tokens expire (max 15 minutes).
5. **Monitor** for 401 errors during the transition window.

### Dual-Key Support (Future)

If zero-downtime rotation is needed, implement key rotation with multiple keys:

```python
CLERK_JWT_VERIFICATION_KEYS=key1,key2  # Comma-separated PEM keys
```

The backend would try each key until verification succeeds. This is not currently implemented.

### Key Rotation Checklist

- [ ] Generate new key in Clerk dashboard
- [ ] Update `CLERK_JWT_VERIFICATION_KEY` in all environments
- [ ] Deploy backend changes
- [ ] Verify new tokens work
- [ ] Wait for old tokens to expire (15 min max)
- [ ] Verify no 401 errors in logs
- [ ] Remove old key from Clerk dashboard (optional — Clerk handles this)

### Monitoring

Track these metrics during rotation:
- `401` response rate — should spike briefly then normalize.
- `TokenExpiredError` count — expected during transition.
- `InvalidTokenError` count — should remain near zero.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLERK_JWT_VERIFICATION_KEY` | — | RSA public key (PEM format, required) |
| `CLERK_JWT_TTL_MINUTES` | 15 | Token TTL (1–60 minutes) |
| `CACHE_ROLE_VERIFICATION_TTL` | 120 | Role cache TTL in seconds |
