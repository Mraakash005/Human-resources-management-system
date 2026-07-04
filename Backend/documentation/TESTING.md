# Testing

## Overview

The HRMS backend uses `pytest` for both unit and integration tests. All tests are organized under the `tests/` directory.

---

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py           # Database model tests
│   ├── test_auth.py             # Authentication logic
│   ├── test_ai_services.py      # Ollama/Whisper integration
│   ├── test_email.py            # Resend email sending
│   ├── test_file_uploads.py     # File validation/scanning
│   ├── test_leave.py            # Leave request logic
│   └── test_payroll.py          # Payroll calculations
├── integration/
│   ├── __init__.py
│   ├── test_api_endpoints.py    # API endpoint tests
│   ├── test_database.py         # Database operations
│   ├── test_ai_pipeline.py      # Full AI workflow
│   └── test_email_workflow.py   # Email end-to-end
└── fixtures/
    ├── sample_audio.wav
    ├── sample_resume.pdf
    └── test_data.json
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run Specific Test File

```bash
pytest tests/unit/test_leave.py
```

### Run Specific Test

```bash
pytest tests/unit/test_leave.py::test_create_leave_request
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Failed Tests Only

```bash
pytest --lf
```

---

## pytest Configuration

### pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--disable-warnings",
    "-x",  # Stop on first failure
]
markers = [
    "unit: Unit tests (fast, no external deps)",
    "integration: Integration tests (may need DB, services)",
    "slow: Tests that take >1s",
    "ai: Tests requiring Ollama/Whisper",
    "email: Tests requiring Resend API key",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### Running by Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Fast tests (no AI, no email)
pytest -m "not slow and not ai and not email"

# Only AI tests
pytest -m ai
```

---

## Mock Fixtures

### conftest.py

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

# ──── API Client ────

@pytest.fixture
def client():
    return TestClient(app)

# ──── Database ────

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.commit.return_value = None
    return db

@pytest.fixture
def override_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()

# ──── Authentication ────

@pytest.fixture
def auth_headers():
    token = create_test_token(user_id=1, role="admin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def employee_headers():
    token = create_test_token(user_id=2, role="employee")
    return {"Authorization": f"Bearer {token}"}

# ──── AI Services ────

@pytest.fixture
def mock_ollama():
    with patch("app.services.ai.call_ollama") as mock:
        mock.return_value = "Mocked AI response"
        yield mock

@pytest.fixture
def mock_ollama_json():
    with patch("app.services.ai.call_ollama_json") as mock:
        mock.return_value = {
            "leave_type": "sick",
            "start_date": "2026-07-10",
            "end_date": "2026-07-12",
            "reason": "Feeling unwell",
            "confidence": 0.9
        }
        yield mock

@pytest.fixture
def mock_whisper():
    with patch("app.services.ai.transcribe_audio") as mock:
        mock.return_value = "I need sick leave from July 10th to July 12th"
        yield mock

# ──── Email ────

@pytest.fixture
def mock_resend():
    with patch("resend.Emails.send") as mock:
        mock.return_value = {"id": "test_email_123"}
        yield mock

# ──── File Uploads ────

@pytest.fixture
def mock_clamav():
    with patch("app.services.file_upload.scan_file") as mock:
        mock.return_value = {"clean": True, "threat": None}
        yield mock

@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "test_resume.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    return pdf_path

@pytest.fixture
def sample_audio(tmp_path):
    audio_path = tmp_path / "test_recording.wav"
    audio_path.write_bytes(b"RIFF fake wav content")
    return audio_path

# ──── Employee ────

@pytest.fixture
def sample_employee():
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john@company.com",
        "department": "Engineering",
        "role": "Software Engineer"
    }
```

---

## Test Coverage Targets

| Module | Target | Priority |
|--------|--------|----------|
| Authentication | 95% | Critical |
| Leave Management | 90% | High |
| Payroll | 90% | High |
| AI Services | 85% | High |
| File Uploads | 85% | Medium |
| Email Service | 80% | Medium |
| API Endpoints | 80% | Medium |
| Models/DB | 75% | Medium |
| **Overall** | **85%** | — |

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "app/tests/*",
    "app/main.py",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "raise NotImplementedError",
]
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: hrms_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          ruff check app/
          mypy app/

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/hrms_test

      - name: Run integration tests
        run: pytest tests/integration/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/hrms_test
          OLLAMA_BASE_URL: http://localhost:11434
          RESEND_API_KEY: ${{ secrets.TEST_RESEND_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=85
```

### Local CI Simulation

```bash
# Run the full CI pipeline locally
docker compose -f docker-compose.test.yml up -d postgres
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
```

---

## Best Practices

1. **One assertion per test** — Each test function tests one behavior
2. **Descriptive names** — `test_leave_request_rejects_past_dates`
3. **Arrange-Act-Assert** — Clear test structure
4. **No test interdependence** — Tests run in any order
5. **Fast unit tests** — Mock external services
6. **Realistic integration tests** — Use test database
7. **Clean up** — Use fixtures for setup/teardown

## ngrok Testing

ngrok is **not used in automated tests**. It is a development-only tool. For webhook testing in tests:

```python
# Use mock payloads in tests
def test_webhook_handler():
    payload = {
        "type": "user.created",
        "data": {
            "id": "user_test123",
            "email_addresses": [{"email_address": "test@example.com"}],
            "first_name": "Test",
            "last_name": "User",
            "public_metadata": {"role": "employee"}
        }
    }
    # Test with mock svix headers
    response = client.post("/api/v1/webhooks/clerk", json=payload, headers=mock_headers)
    assert response.status_code == 200
```

For manual webhook testing with real Clerk events, use ngrok (see `docs/NGROK.md`).
