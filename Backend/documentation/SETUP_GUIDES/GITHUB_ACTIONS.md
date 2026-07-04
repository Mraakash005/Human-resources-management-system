# GitHub Actions CI/CD Setup Guide

## Repository Setup

### 1. Create GitHub Repository
1. Go to https://github.com
2. Click "New repository"
3. Enter repository name (e.g., `hrms-backend`)
4. Select visibility (Private/Public)
5. Initialize with README if desired
6. Click "Create repository"

### 2. Clone Repository Locally
```bash
git clone https://github.com/your-username/hrms-backend.git
cd hrms-backend
```

### 3. Create GitHub Actions Directory
```bash
mkdir -p .github/workflows
```

## Secrets Configuration

### Access Repository Settings
1. Go to your repository on GitHub
2. Click "Settings" tab
3. Scroll down to "Security" section
4. Click "Secrets and variables" → "Actions"

### Add Required Secrets
Click "New repository secret" for each:

#### Database Secrets
- **Name**: `DATABASE_URL`
- **Value**: `postgresql://postgres:password@localhost:5432/hrms_db`

- **Name**: `TEST_DATABASE_URL`
- **Value**: `postgresql://postgres:password@localhost:5432/hrms_test_db`

#### Clerk Authentication Secrets
- **Name**: `CLERK_SECRET_KEY`
- **Value**: `sk_your_clerk_secret_key`

- **Name**: `CLERK_JWKS_URL`
- **Value**: `https://your-app.clerk.accounts.dev/.well-known/jwks.json`

- **Name**: `CLERK_WEBHOOK_SECRET`
- **Value**: `whsec_your_webhook_secret`

#### Email Secrets
- **Name**: `RESEND_API_KEY`
- **Value**: `re_your_resend_api_key`

#### Application Secrets
- **Name**: `SECRET_KEY`
- **Value**: `your-super-secret-key`

- **Name**: `OLLAMA_BASE_URL`
- **Value**: `http://localhost:11434`

### List All Secrets
```bash
# Using GitHub CLI
gh secret list
```

## Workflow Files

### Create CI/CD Workflow
Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
          POSTGRES_DB: hrms_test_db
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
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:password@localhost:5432/hrms_test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY }}
          CLERK_JWKS_URL: ${{ secrets.CLERK_JWKS_URL }}
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
  
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install black isort flake8 mypy
      
      - name: Check formatting
        run: |
          black --check .
          isort --check-only .
      
      - name: Lint with flake8
        run: |
          flake8 .
      
      - name: Type check with mypy
        run: |
          mypy app/
  
  build:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/hrms-backend:latest
            ${{ secrets.DOCKER_USERNAME }}/hrms-backend:${{ github.sha }}
```

### Create Deploy Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types:
      - completed
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/hrms-backend
            git pull origin main
            docker-compose down
            docker-compose up -d --build
            docker-compose exec -T app alembic upgrade head
            docker-compose restart app
```

### Create Release Workflow
Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

## Running CI/CD

### Manual Trigger
```bash
# Using GitHub CLI
gh workflow run ci.yml

# With parameters
gh workflow run ci.yml -f branch=main
```

### Automatic Triggers
- **Push to main**: Runs full CI/CD pipeline
- **Push to develop**: Runs tests and linting
- **Pull request to main**: Runs tests and linting
- **Tag push (v*)**: Creates release

### View Workflow Runs
```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Cancel Running Workflows
```bash
# Cancel specific run
gh run cancel <run-id>

# Cancel all runs for a branch
gh run cancel --branch <branch-name>
```

## Branch Protection

### Enable Branch Protection Rules
1. Go to repository Settings
2. Click "Branches" in left sidebar
3. Click "Add rule" next to "Branch protection rules"

### Configure Protection Rules
#### For `main` branch:
- **Branch name pattern**: `main`
- **Require pull request reviews before merging**
  - Required approvals: 1
  - Dismiss stale pull request approvals when new commits are pushed
- **Require status checks to pass before merging**
  - Required checks: `test`, `lint`, `build`
- **Require branches to be up to date before merging**
- **Require conversation resolution before merging**
- **Require linear history** (optional)
- **Include administrators** (optional)

#### For `develop` branch:
- **Branch name pattern**: `develop`
- **Require pull request reviews before merging**
  - Required approvals: 1
- **Require status checks to pass before merging**
  - Required checks: `test`, `lint`
- **Allow force pushes** (optional)

### Using GitHub CLI
```bash
# Create branch protection rule
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test","lint","build"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### Repository Variables
1. Go to Settings → Secrets and variables → Actions
2. Click "Variables" tab
3. Add variables:
   - **Name**: `APP_NAME`
   - **Value**: `HRMS Backend`

## Common Issues

### Workflow Not Running
- Check if Actions are enabled in repository settings
- Verify the workflow file is in `.github/workflows/`
- Check the YAML syntax

### Secrets Not Available
- Ensure secrets are added in Settings → Secrets and variables → Actions
- Check the secret name matches exactly (case-sensitive)
- Verify the secret is not empty

### Tests Failing in CI
- Check if all dependencies are in requirements.txt
- Verify environment variables are set correctly
- Check if services (PostgreSQL, Redis) are running

### Build Failing
- Check Dockerfile syntax
- Verify all required files are present
- Check for hardcoded paths

### Deploy Failing
- Verify SSH key is correct
- Check server access permissions
- Verify deployment script syntax

## Useful Resources

- GitHub Actions Documentation: https://docs.github.com/en/actions
- GitHub CLI Documentation: https://cli.github.com/
- GitHub Actions Marketplace: https://github.com/marketplace?type=actions
