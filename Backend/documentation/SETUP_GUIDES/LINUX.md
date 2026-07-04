# Linux Setup Guide

## Prerequisites

1. **Docker** - https://docs.docker.com/engine/install/
2. **Docker Compose** - https://docs.docker.com/compose/install/
3. **Python 3.12** - https://www.python.org/downloads/
4. **pip** - Usually included with Python
5. **Git** - https://git-scm.com/download/linux

## Installation Steps

### 1. Install Docker
```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to docker group (logout and login after)
sudo usermod -aG docker $USER
```

### 2. Install Python 3.12
```bash
sudo apt update
sudo apt install -y software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

### 3. Install Git
```bash
sudo apt update
sudo apt install -y git
```

### 4. Clone the Repository
```bash
git clone <repository-url>
cd HRMS_Backend
```

### 5. Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 6. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Environment Setup
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

## Systemd Service (Optional)

### Create Service File
```bash
sudo nano /etc/systemd/system/hrms-backend.service
```

Add the following content:
```ini
[Unit]
Description=HRMS Backend API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/HRMS_Backend
ExecStart=/path/to/HRMS_Backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
Environment=PATH=/path/to/HRMS_Backend/venv/bin

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable hrms-backend
sudo systemctl start hrms-backend

# Check status
sudo systemctl status hrms-backend

# View logs
sudo journalctl -u hrms-backend -f
```

## Common Linux Issues

### Permission denied for Docker
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or run:
newgrp docker
```

### Python version conflicts
```bash
# Check available versions
ls /usr/bin/python*

# Update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

### Port 5432 already in use
```bash
# Check what's using the port
sudo lsof -i :5432

# Stop PostgreSQL if running
sudo systemctl stop postgresql
```

### Memory issues
```bash
# Check available memory
free -h

# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Firewall blocking ports
```bash
# Allow ports through firewall
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp

# Check firewall status
sudo ufw status
```

### Docker Compose not found
```bash
# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Or install standalone version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Virtual environment not activating
```bash
# Ensure python3-venv is installed
sudo apt install python3.12-venv

# Recreate venv
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
```
