# macOS Setup Guide

## Prerequisites

1. **Docker Desktop** - https://docs.docker.com/desktop/install/mac-install/
2. **Homebrew** - https://brew.sh/
3. **Python 3.12** - https://www.python.org/downloads/
4. **Git** - https://git-scm.com/download/mac

## Installation Steps

### 1. Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Docker Desktop
- Download from https://docs.docker.com/desktop/install/mac-install/
- Choose the appropriate version (Intel or Apple Silicon)
- Drag Docker to Applications folder
- Open Docker Desktop and wait for it to start

### 3. Install Python 3.12
```bash
brew install python@3.12
```

Verify installation:
```bash
python3.12 --version
```

### 4. Install Git
```bash
brew install git
```

Verify installation:
```bash
git --version
```

### 5. Clone the Repository
```bash
git clone <repository-url>
cd HRMS_Backend
```

### 6. Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 7. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 8. Environment Setup
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/hrms_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
CLERK_SECRET_KEY=sk_your_clerk_secret_key
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
RESEND_API_KEY=re_your_resend_api_key
OLLAMA_BASE_URL=http://localhost:11434
```

### 9. Start Services with Docker Compose
```bash
docker-compose up -d postgres redis
```

### 10. Run Database Migrations
```bash
alembic upgrade head
```

### 11. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## Common macOS Issues

### Homebrew command not found
```bash
# Add Homebrew to PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Python version conflicts
```bash
# Check installed versions
brew list python

# Use specific version
python3.12 --version

# Update PATH to prefer Homebrew Python
echo 'export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Docker Desktop won't start
1. Ensure you have the correct version for your Mac (Intel vs Apple Silicon)
2. Check if virtualization is enabled
3. Restart Docker Desktop
4. Check Docker Desktop logs for errors

### Port already in use
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Permission issues
```bash
# Fix permissions for Python packages
sudo chown -R $(whoami) /opt/homebrew/lib/python3.12/site-packages

# Or use --user flag with pip
pip install --user -r requirements.txt
```

### SSL certificate issues
```bash
# Install certificates
open /Applications/Python\ 3.12/Install\ Certificates.command

# Or manually
pip install certifi
```

### Virtual environment not activating
```bash
# Ensure python3-venv is available
brew install python@3.12

# Recreate venv
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
```

### PostgreSQL connection issues
1. Ensure Docker is running
2. Check if PostgreSQL container is running: `docker ps`
3. Verify the connection string in `.env`

### Redis connection issues
1. Ensure Docker is running
2. Check if Redis container is running: `docker ps`
3. Verify the Redis URL in `.env`

### Apple Silicon compatibility
If you're on an M1/M2/M3 Mac:
```bash
# Use Rosetta for Docker
docker pull --platform linux/x86_64 postgres:15

# Or use ARM-compatible images
docker pull postgres:15
```
