# PostgreSQL Setup Guide

## Docker Setup (Included in Compose)

PostgreSQL is included in the Docker Compose configuration. When you run:

```bash
docker-compose up -d postgres
```

It automatically:
- Pulls the `postgres:15` image
- Creates a database named `hrms_db`
- Sets up the user `postgres` with password `password`
- Exposes port `5432`
- Persists data in a Docker volume

### Verify Docker PostgreSQL
```bash
# Check if container is running
docker-compose ps postgres

# Access PostgreSQL shell
docker-compose exec postgres psql -U postgres -d hrms_db

# Check databases
\l

# Check tables
\dt

# Exit shell
\q
```

## Manual Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (Homebrew)
```bash
brew install postgresql@15

# Start service
brew services start postgresql@15
```

### Windows
1. Download installer from https://www.postgresql.org/download/windows/
2. Run the installer
3. Follow the setup wizard
4. Remember the password you set for the postgres user

## Database Creation

### Using Docker
```bash
docker-compose exec postgres psql -U postgres -d hrms_db
```

### Using Manual Installation
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE hrms_db;

# List databases
\l

# Connect to hrms_db
\c hrms_db

# Exit
\q
```

## User Setup

### Create Application User
```sql
-- Connect as postgres
psql -U postgres

-- Create user
CREATE USER hrms_user WITH PASSWORD 'secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE hrms_db TO hrms_user;

-- Connect to hrms_db
\c hrms_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO hrms_user;

-- Grant table privileges (for existing tables)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hrms_user;

-- Grant sequence privileges
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hrms_user;

-- Exit
\q
```

### Update .env File
```env
DATABASE_URL=postgresql://hrms_user:secure_password_here@localhost:5432/hrms_db
```

## Connection Testing

### Using psql
```bash
# Test connection
psql -U postgres -d hrms_db -c "SELECT 1;"

# Test with connection string
psql "postgresql://postgres:password@localhost:5432/hrms_db"
```

### Using Python
```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="hrms_db",
        user="postgres",
        password="password"
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

### Using pg_isready
```bash
# Check if PostgreSQL is accepting connections
pg_isready -h localhost -p 5432
```

## Backup Basics

### Backup Database
```bash
# Using pg_dump
pg_dump -U postgres hrms_db > hrms_db_backup.sql

# Backup with timestamp
pg_dump -U postgres hrms_db > "hrms_db_$(date +%Y%m%d_%H%M%S).sql"
```

### Backup with Docker
```bash
# Backup
docker-compose exec postgres pg_dump -U postgres hrms_db > hrms_db_backup.sql

# Backup compressed
docker-compose exec postgres pg_dump -U postgres hrms_db | gzip > hrms_db_backup.sql.gz
```

### Backup Specific Tables
```bash
pg_dump -U postgres hrms_db -t employees -t departments > tables_backup.sql
```

## Restore Basics

### Restore Database
```bash
# Restore from SQL file
psql -U postgres hrms_db < hrms_db_backup.sql

# Restore compressed backup
gunzip < hrms_db_backup.sql.gz | psql -U postgres hrms_db
```

### Restore with Docker
```bash
# Restore
cat hrms_db_backup.sql | docker-compose exec -T postgres psql -U postgres -d hrms_db

# Restore compressed
gunzip < hrms_db_backup.sql.gz | docker-compose exec -T postgres psql -U postgres -d hrms_db
```

### Restore to New Database
```bash
# Create new database
createdb -U postgres hrms_db_restored

# Restore
psql -U postgres hrms_db_restored < hrms_db_backup.sql
```

## Common Issues

### Connection Refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if port is in use
sudo lsof -i :5432

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Authentication Failed
```bash
# Check pg_hba.conf location
sudo find / -name "pg_hba.conf" 2>/dev/null

# Edit pg_hba.conf to allow password authentication
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Change from peer to md5 for local connections
# local all all peer -> local all all md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Permission Denied
```bash
# Grant privileges to user
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE hrms_db TO hrms_user;"

# Grant schema privileges
psql -U postgres -d hrms_db -c "GRANT ALL ON SCHEMA public TO hrms_user;"
```

### Database Does Not Exist
```bash
# Create database
createdb -U postgres hrms_db

# Or using psql
psql -U postgres -c "CREATE DATABASE hrms_db;"
```
