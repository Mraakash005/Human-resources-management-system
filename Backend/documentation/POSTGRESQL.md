# PostgreSQL Integration

Async SQLAlchemy with asyncpg driver, connection pooling, session management, and health checks.

## Async SQLAlchemy with asyncpg

The database layer uses **SQLAlchemy 2.0** with the **asyncpg** async driver for non-blocking PostgreSQL access.

```
DATABASE_URL=postgresql+asyncpg://hrms:password@localhost:5432/hrms_db
```

The `postgresql+asyncpg://` scheme is validated at startup — any other scheme raises an error.

### Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `sqlalchemy[asyncio]` | 2.0.36 | Async ORM + query builder |
| `asyncpg` | 0.30.0 | Async PostgreSQL driver |
| `greenlet` | 3.1.1 | Required for SQLAlchemy async context |

---

## Connection Pool Settings

The `DatabaseManager` in `app/core/database.py` configures the engine with production-grade pooling.

### Production Pool (default)

| Setting | Config | Default | Description |
|---|---|---|---|
| `pool_size` | `DB_POOL_SIZE` | `20` | Persistent connections in pool |
| `max_overflow` | `DB_MAX_OVERFLOW` | `10` | Extra connections beyond pool_size |
| `pool_timeout` | `DB_POOL_TIMEOUT` | `30` | Seconds to wait for a connection |
| `pool_recycle` | `DB_POOL_RECYCLE` | `1800` | Recycle connections after N seconds |
| `pool_pre_ping` | hardcoded | `True` | Test connections before use |
| `echo` | `DB_ECHO` | `False` | Log SQL statements |

**Total max connections**: `pool_size + max_overflow` = 30

### Testing Pool

When `ENVIRONMENT=testing`, uses `NullPool` (no pooling, fresh connection per request) and sets `search_path` to `hrms_test, public`.

---

## Session Management

### `DatabaseManager.get_session()`

```python
async with self._session_factory() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Behavior**:
- Sessions are created from `async_sessionmaker` with `expire_on_commit=False`
- `autocommit=False` and `autoflush=False` for explicit control
- Automatic **commit** on successful yield
- Automatic **rollback** on any exception
- **Close** always runs in `finally`

### FastAPI Dependency

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session
```

Used in all routers:

```python
from app.core.database import get_db

@router.get("/employees")
async def list_employees(db: AsyncSession = Depends(get_db)):
    ...
```

---

## DatabaseManager Class

```python
from app.core.database import db_manager
```

### Methods

| Method | Description |
|---|---|
| `connect()` | Create async engine + session factory |
| `disconnect()` | Dispose engine, release all connections |
| `health_check()` | Execute `SELECT 1`, return `bool` |
| `get_session_factory()` | Get the `async_sessionmaker` instance |
| `get_session()` | Async generator yielding sessions with auto-commit/rollback |

### Base Model

```python
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"
    ...
```

All ORM models inherit from `Base` (SQLAlchemy `DeclarativeBase`).

---

## Engine Initialization Flow

```
1. lifespan startup
   └─ db_manager.connect()
       ├─ create_async_engine(DATABASE_URL, pool_size=20, ...)
       └─ async_sessionmaker(bind=engine, expire_on_commit=False)

2. Request handling
   └─ Depends(get_db)
       └─ get_session() → yield session → commit/rollback → close

3. lifespan shutdown
   └─ db_manager.disconnect()
       └─ engine.dispose()
```

---

## Health Check

```python
ok: bool = await db_manager.health_check()
```

Executes `SELECT 1` via a connection from the pool. Returns `True` on success, `False` on any exception.

The `/health` endpoint includes the result in its JSON response.

---

## Database Verification Script

`scripts/verify_database.py` checks that all 16 expected tables exist:

```bash
python scripts/verify_database.py
```

Expected tables:
- `employees`, `attendance_records`, `leave_requests`, `leave_balances`
- `salary_components`, `payroll_runs`, `audit_log`
- `burnout_config`, `burnout_alerts`, `nudges`
- `public_holidays`, `office_config`
- `chat_channels`, `chat_messages`, `chat_reads`, `meeting_rsvp`

Also reports index and constraint counts.

---

## PostgreSQL Configuration (docker-compose)

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: hrms_db
    POSTGRES_USER: hrms
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-hrms_secure_password_2025}
  volumes:
    - pg_data:/var/lib/postgresql/data
  ports:
    - "5432:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U hrms -d hrms_db"]
    interval: 10s
    timeout: 5s
    retries: 5
```

- **Image**: PostgreSQL 16 Alpine (lightweight)
- **Persistent storage**: Named volume `pg_data`
- **Health check**: `pg_isready` every 10s
- **Backend depends_on**: `condition: service_healthy` — waits for PostgreSQL to be ready
