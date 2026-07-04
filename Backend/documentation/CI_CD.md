# CI/CD Pipeline

GitHub Actions workflow for linting, type checking, testing, Docker builds, migration validation, and security scanning.

## Overview

The CI/CD pipeline runs on every push and pull request. It validates code quality, runs tests, builds Docker images, validates migrations, and scans for security issues.

---

## GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: HRMS CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"
```

---

## Linting (Ruff)

**Tool**: [Ruff](https://docs.astral.sh/ruff/) v0.8.6

```bash
# Check for lint errors
ruff check .

# Check formatting
ruff format --check .
```

### What Ruff Checks

- Import sorting (`isort` rules)
- Unused imports and variables
- Code style (PEP 8)
- Bug patterns (common mistakes)
- Type annotation issues

### Auto-fix

```bash
ruff check --fix .
ruff format .
```

### Configuration

In `pyproject.toml` (or `ruff.toml`):

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM"]
```

---

## Type Checking (Mypy)

**Tool**: [Mypy](https://mypy.readthedocs.io/) v1.14.1

```bash
mypy app/ --ignore-missing-imports
```

### Configuration

```toml
[tool.mypy]
python_version = "3.12"
strict = false
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
disallow_untyped_defs = false
```

### What Mypy Checks

- Function signatures and return types
- Variable type annotations
- Class attribute types
- Generic type usage
- Optional/Union handling

---

## Testing (Pytest)

**Tool**: [Pytest](https://docs.pytest.org/) v8.3.4 with `pytest-asyncio`

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=xml --cov-report=term-missing

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Verbose output
pytest -v
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_cache.py
│   ├── test_exceptions.py
│   ├── test_helpers.py
│   ├── test_schemas.py
│   └── test_webhooks.py
└── integration/
    ├── __init__.py
    └── test_api.py
```

### Coverage

```bash
pytest --cov=app --cov-report=html
```

Generates `htmlcov/index.html` for visual coverage report.

### CI Configuration

```bash
pytest --cov=app --cov-report=xml --cov-fail-under=80 -q
```

- Fails if coverage drops below 80%
- Outputs XML for CI integration (e.g., Codecov)

---

## Docker Build

Multi-stage build verified in CI:

```bash
# Build the image
docker build -t hrms-backend:ci .

# Verify it starts
docker run --rm -e DATABASE_URL=postgresql+asyncpg://test:test@localhost/test \
  hrms-backend:ci python -c "from app.core.config import get_settings; print('OK')"
```

### Dockerfile Stages

| Stage | Base | Purpose |
|---|---|---|
| `builder` | `python:3.12-slim` | Install build deps + pip packages |
| `production` | `python:3.12-slim` | Runtime only, non-root user |

### CI Docker Commands

```yaml
steps:
  - name: Build Docker image
    run: docker build -t hrms-backend:${{ github.sha }} .

  - name: Verify Docker health
    run: |
      docker run -d --name test-backend \
        -e DATABASE_URL=postgresql+asyncpg://test:test@localhost/test \
        -e REDIS_URL=redis://localhost:6379/0 \
        -e SECRET_KEY=test-secret-key-that-is-at-least-32-characters-long \
        -e CLERK_PUBLISHABLE_KEY=pk_test \
        -e CLERK_SECRET_KEY=sk_test_1234567890 \
        -e CLERK_JWT_VERIFICATION_KEY=test \
        -e RESEND_API_KEY=re_test \
        -e HR_EMAIL=hr@test.com \
        hrms-backend:${{ github.sha }}
      sleep 5
      docker exec test-backend python -c "print('Container OK')"
```

---

## Migration Validation

Validates that Alembic migrations are consistent and reversible:

```bash
# Check current migration state
alembic current

# Verify head is reachable
alembic heads

# Generate SQL diff (dry run)
alembic upgrade head --sql > /dev/null

# Test downgrade path
alembic downgrade base
alembic upgrade head
```

### CI Validation Steps

```yaml
- name: Validate migrations
  run: |
    # Generate migration SQL without applying
    alembic upgrade head --sql > migration.sql
    echo "Migration SQL generated"

    # Verify model changes are captured
    alembic revision --autogenerate --sql -m "ci-check" | head -5
    echo "Auto-generate check passed"
```

---

## Security Scanning

### Dependency Scanning

```yaml
- name: Security scan
  run: |
    pip install safety
    safety check --full-report
```

### Secret Detection

```yaml
- name: Check for hardcoded secrets
  run: |
    grep -rn "sk_live\|sk_test\|password\s*=" app/ || true
    grep -rn "BEGIN.*PRIVATE" app/ || true
```

### Docker Security

```yaml
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: hrms-backend:${{ github.sha }}
    format: table
    exit-code: 1
    severity: CRITICAL,HIGH
```

---

## Full CI Workflow

```yaml
name: HRMS CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mypy sqlalchemy asyncpg
      - run: mypy app/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: hrms_test
          POSTGRES_USER: hrms
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml -q
        env:
          ENVIRONMENT: testing
          DATABASE_URL: postgresql+asyncpg://hrms:test@localhost:5432/hrms_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-pipeline-only-32chars
          CLERK_PUBLISHABLE_KEY: pk_test
          CLERK_SECRET_KEY: sk_test_1234567890
          CLERK_JWT_VERIFICATION_KEY: test
          RESEND_API_KEY: re_test
          HR_EMAIL: hr@test.com

  docker:
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t hrms-backend:${{ github.sha }} .

  migration-validate:
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: hrms_test
          POSTGRES_USER: hrms
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://hrms:test@localhost:5432/hrms_test
      - run: python scripts/verify_database.py
        env:
          DATABASE_URL: postgresql+asyncpg://hrms:test@localhost:5432/hrms_test
```

---

## Quality Gates

| Gate | Tool | Threshold |
|---|---|---|
| Linting | Ruff | 0 errors |
| Formatting | Ruff | All files formatted |
| Type checking | Mypy | 0 errors |
| Test coverage | Pytest | ≥ 80% |
| Docker build | Docker | Build succeeds |
| Migration | Alembic | Head applies cleanly |
| Security | Trivy/Safety | No CRITICAL/HIGH |

## ngrok in CI/CD

ngrok is **not used in CI/CD pipelines**. It is a development-only tool for local webhook testing. In CI/CD:

- Webhook endpoints are tested with mock payloads
- Signature verification is tested with known test keys
- ngrok profile is never activated in automated pipelines

```yaml
# CI does NOT use ngrok
- name: Test webhook endpoint
  run: |
    curl -X POST http://localhost:8000/api/v1/webhooks/clerk \
      -H "Content-Type: application/json" \
      -H "svix-id: test_123" \
      -H "svix-timestamp: $(date +%s)" \
      -H "svix-signature: v1,test" \
      -d '{"type":"user.created","data":{"id":"user_test"}}'
```
