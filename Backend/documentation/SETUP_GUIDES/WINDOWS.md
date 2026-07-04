# Windows Setup Guide

## Prerequisites

1. **Docker Desktop** - https://docs.docker.com/desktop/install/windows-install/
2. **Python 3.12** - https://www.python.org/downloads/
3. **Git** - https://git-scm.com/download/win
4. **PostgreSQL** (if not using Docker) - https://www.postgresql.org/download/windows/
5. **Redis** (if not using Docker) - https://redis.io/download

## Installation Steps

### 1. Install Docker Desktop
- Download from https://docs.docker.com/desktop/install/windows-install/
- Run the installer and follow the prompts
- Enable WSL 2 backend when prompted (recommended)
- Restart your computer after installation
- Open Docker Desktop and wait for it to start

### 2. Install Python 3.12
- Download from https://www.python.org/downloads/
- Run the installer
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Click "Install Now"
- Verify installation: `python --version`

### 3. Install Git
- Download from https://git-scm.com/download/win
- Run the installer with default settings
- Verify installation: `git --version`

### 4. Clone the Repository
```bash
git clone <repository-url>
cd HRMS_Backend
```

### 5. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 6. Install Dependencies
```bash
pip install -r requirements.txt
```

### 7. Environment Setup
```bash
copy .env.example .env
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

### 8. Start Services with Docker Compose
```bash
docker-compose up -d postgres redis
```

### 9. Run Database Migrations
```bash
alembic upgrade head
```

### 10. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## Common Windows Issues

### PATH not recognized
If `python` or `pip` commands are not recognized:
1. Open System Properties > Advanced > Environment Variables
2. Edit the Path variable
3. Add `C:\Python312\` and `C:\Python312\Scripts\`

### Docker Desktop won't start
1. Ensure WSL 2 is installed: `wsl --install`
2. Restart your computer
3. Run Docker Desktop as Administrator

### Permission denied errors
- Run PowerShell as Administrator
- Or change execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Port already in use
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Virtual environment activation issues
If PowerShell blocks script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### PostgreSQL connection refused
1. Ensure PostgreSQL service is running: `services.msc`
2. Check the port (default 5432)
3. Verify credentials in `.env`

### Redis connection refused
1. Ensure Redis service is running
2. Check the port (default 6379)
3. Verify Redis is installed and started

### Memory issues with Docker
- Increase Docker Desktop memory limit in Settings > Resources > Advanced
- Set to at least 4GB for development
