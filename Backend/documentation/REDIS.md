# Redis Integration

Async Redis configuration with connection pooling, typed helpers, Pub/Sub for SSE, and caching patterns.

## Redis Manager Class

The `RedisManager` class in `app/core/redis.py` manages the async Redis connection pool and exposes typed helper methods.

```python
from app.core.redis import redis_manager
```

### Lifecycle

```python
await redis_manager.connect()   # Initialize pool + client
await redis_manager.disconnect()  # Close all connections
```

The manager is initialized during FastAPI lifespan (`app/main.py:38`) and torn down on shutdown.

### Accessing the Raw Client

```python
client: Redis = redis_manager.client
```

Raises `RuntimeError` if `connect()` has not been called.

---

## Connection Pooling

Uses `redis.asyncio.ConnectionPool` configured from `settings.REDIS_URL`.

| Setting | Config | Default |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | — |
| `REDIS_MAX_CONNECTIONS` | `max_connections` param | `20` |
| `REDIS_DECODER_RESPONSES` | `decode_responses` | `True` |

The pool is created via `ConnectionPool.from_url()` and shared across all async tasks. All Redis operations are async and safe for concurrent use.

---

## Typed Helpers

### `get_json(key) -> dict | None`

Deserialize a JSON value from Redis. Returns `None` on miss, connection error, or decode error.

```python
data = await redis_manager.get_json("dashboard:emp123:admin")
```

### `set_json(key, value, ttl=60) -> bool`

Serialize a dict to JSON and store with a TTL (seconds). Returns `True` on success.

```python
await redis_manager.set_json("dashboard:emp123:admin", data, ttl=60)
```

### `delete_pattern(pattern) -> int`

Scan and delete all keys matching a glob pattern. Returns the number of deleted keys. Uses `SCAN` with `count=100` to avoid blocking.

```python
deleted = await redis_manager.delete_pattern("dashboard:emp123:*")
```

### `exists(key) -> bool`

Check if a key exists in Redis.

```python
locked = await redis_manager.exists("attendance:checkin:emp123:2026-07-04")
```

### `setex(key, ttl, value) -> bool`

Set a raw string value with TTL.

```python
await redis_manager.setex("rate:limit:ip:1.2.3.4", 60, "ok")
```

### `get(key) -> str | None`

Get a raw string value. Handles `bytes` → `str` decoding.

```python
role = await redis_manager.get("role_verified:clerk_user_abc")
```

### `increment(key, ttl=60) -> int`

Atomically increment a counter and set/refresh its TTL using a pipeline. Returns the new count.

```python
count = await redis_manager.increment("api:hits:1.2.3.4", ttl=60)
```

---

## Pub/Sub for Team Chat SSE

Redis Pub/Sub powers real-time team chat via Server-Sent Events.

### Publishing Messages

When a chat message is sent, it is persisted to PostgreSQL and then published:

```python
# app/services/chat_service.py:84
await redis_manager.publish(f"chat:{channel_id}", json.dumps(message_data))
```

Channel format: `chat:{channel_id}` (UUID).

### Subscribing to SSE

The `GET /api/v1/chat/stream/{channel_id}` endpoint subscribes to the Redis channel and streams events:

```python
# app/routers/chat.py:165-184
pubsub = redis_manager.pubsub()
await pubsub.subscribe(f"chat:{channel_id}")
async for message in pubsub.listen():
    if message["type"] == "message":
        yield f"data: {message['data'].decode()}\n\n"
```

The `StreamingResponse` uses `text/event-stream` media type with `X-Accel-Buffering: no` for nginx compatibility.

### Helper Methods

```python
await redis_manager.publish(channel, message)  # Publish to channel
pubsub = redis_manager.pubsub()                # Get PubSub instance
```

---

## Cache Key Patterns

All cache keys are managed through `app/services/cache.py` (`CacheService`).

| Pattern | Purpose | TTL |
|---|---|---|
| `dashboard:{user_id}:{role}` | Dashboard data per role | `CACHE_DASHBOARD_TTL` = 60s |
| `role_verified:{clerk_user_id}` | Cached Clerk role lookup | `CACHE_ROLE_VERIFICATION_TTL` = 120s |
| `chatbot_context:{user_id}` | Chatbot conversation context | `CACHE_CHATBOT_CONTEXT_TTL` = 300s |
| `leave_advisor:{user_id}:{date}` | Leave advisor suggestions | `CACHE_LEAVE_ADVISOR_TTL` = 3600s |
| `heatmap:{employee_id}:{year}` | Attendance heatmap | `CACHE_HEATMAP_TTL` = 3600s |
| `leave_balance:{employee_id}` | Leave balance snapshot | 300s (hardcoded) |
| `attendance:checkin:{employee_id}:{date}` | Double check-in lock | 86400s (24h) |
| `ratelimit:{category}:{ip}` | Sliding window rate limit | 60s (matches window) |

### TTL Reference

| Cache Type | Env Variable | Default |
|---|---|---|
| Dashboard | `CACHE_DASHBOARD_TTL` | 60s |
| Role verification | `CACHE_ROLE_VERIFICATION_TTL` | 120s |
| Chatbot context | `CACHE_CHATBOT_CONTEXT_TTL` | 300s |
| Leave advisor | `CACHE_LEAVE_ADVISOR_TTL` | 3600s |
| Heatmap | `CACHE_HEATMAP_TTL` | 3600s |
| Team health | `CACHE_TEAM_HEALTH_TTL` | 21600s (6h) |

### Cache Invalidation

```python
# Invalidate all dashboard caches for a user
await redis_manager.delete_pattern(f"dashboard:{user_id}:*")

# Also invalidate admin dashboards (they show aggregate data)
await redis_manager.delete_pattern("dashboard:*:admin")
```

---

## Health Check

```python
ok: bool = await redis_manager.health_check()
```

Returns `True` if `PING` succeeds, `False` on `ConnectionError` or `TimeoutError`.

The `/health` endpoint (`app/main.py:127`) calls this and includes the result:

```json
{
  "status": "healthy",
  "database": true,
  "redis": true,
  "version": "3.0.0",
  "environment": "development"
}
```

---

## Redis Configuration (docker-compose)

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

- **Max memory**: 256 MB
- **Eviction policy**: `allkeys-lru` — least-recently-used keys evicted first
- **Data persistence**: None (ephemeral cache store)
