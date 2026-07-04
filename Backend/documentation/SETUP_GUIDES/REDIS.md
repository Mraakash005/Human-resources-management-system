# Redis Setup Guide

## Docker Setup (Included in Compose)

Redis is included in the Docker Compose configuration. When you run:

```bash
docker-compose up -d redis
```

It automatically:
- Pulls the `redis:7-alpine` image
- Exposes port `6379`
- Persists data in a Docker volume

### Verify Docker Redis
```bash
# Check if container is running
docker-compose ps redis

# Access Redis CLI
docker-compose exec redis redis-cli

# Test connection
PING
# Should return: PONG
```

## Manual Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y redis-server

# Start and enable service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### macOS (Homebrew)
```bash
brew install redis

# Start service
brew services start redis
```

### Windows
1. Download from https://github.com/tporadowski/redis/releases
2. Extract the ZIP file
3. Run `redis-server.exe`
4. Or install as a Windows service

## Connection Testing

### Using redis-cli
```bash
# Test connection
redis-cli ping

# Should return: PONG

# Test with host and port
redis-cli -h localhost -p 6379 ping
```

### Using Docker
```bash
# Test connection through Docker
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Using Python
```python
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Using Telnet
```bash
telnet localhost 6379
PING
# Should return: +PONG
```

## redis-cli Basics

### Basic Commands
```bash
# Connect to Redis
redis-cli

# Ping server
PING

# Set a key
SET mykey "Hello World"

# Get a key
GET mykey

# Delete a key
DEL mykey

# Check if key exists
EXISTS mykey

# Set key with expiration (seconds)
SETEX mykey 60 "Hello World"

# Get TTL of key
TTL mykey

# List all keys
KEYS *

# Flush all keys
FLUSHALL
```

### Working with Different Data Types
```bash
# Strings
SET user:1:name "John Doe"
GET user:1:name
INCR counter

# Lists
LPUSH mylist "item1"
RPUSH mylist "item2"
LRANGE mylist 0 -1

# Sets
SADD myset "member1"
SADD myset "member2"
SMEMBERS myset

# Hashes
HSET user:1 name "John Doe"
HSET user:1 email "john@example.com"
HGETALL user:1

# Sorted Sets
ZADD leaderboard 100 "player1"
ZADD leaderboard 200 "player2"
ZREVRANGE leaderboard 0 -1 WITHSCORES
```

### Useful Commands
```bash
# Check server info
INFO

# Check memory usage
INFO memory

# Check connected clients
INFO clients

# Monitor commands in real-time
MONITOR

# Clear screen
CLEAR

# Exit
EXIT
```

## Memory Monitoring

### Check Memory Usage
```bash
# Using redis-cli
redis-cli INFO memory

# Check specific memory metric
redis-cli INFO memory | grep used_memory_human

# Check memory usage percentage
redis-cli INFO memory | grep mem_fragmentation_ratio
```

### Monitor Memory in Real-time
```bash
# Watch memory usage
watch -n 1 'redis-cli INFO memory | grep used_memory_human'

# Or in redis-cli
redis-cli
> INFO memory
```

### Memory Optimization
```bash
# Set memory limit
redis-cli CONFIG SET maxmemory 256mb

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Check current settings
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy
```

### Memory Analysis
```bash
# Analyze memory usage by key
redis-cli --bigkeys

# Analyze memory usage by pattern
redis-cli --memkeys

# Get memory usage of specific key
redis-cli MEMORY USAGE mykey
```

## Common Issues

### Connection Refused
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Check if port is in use
sudo lsof -i :6379

# Restart Redis
sudo systemctl restart redis-server
```

### Authentication Required
```bash
# Check if authentication is required
redis-cli

# If authentication is required, you'll see:
# (error) NOAUTH Authentication required.

# Authenticate
redis-cli AUTH your_password

# Or set password in redis.conf
sudo nano /etc/redis/redis.conf
# Uncomment: requirepass your_password
# Restart Redis
```

### Memory Issues
```bash
# Check memory usage
redis-cli INFO memory

# Clear all data
redis-cli FLUSHALL

# Or clear specific database
redis-cli FLUSHDB
```

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :6379

# Stop the process
sudo kill <PID>

# Or change Redis port in redis.conf
sudo nano /etc/redis/redis.conf
# Change: port 6379 to port 6380
```

### Slow Performance
```bash
# Check slow log
redis-cli SLOWLOG GET 10

# Clear slow log
redis-cli SLOWLOG RESET

# Monitor commands
redis-cli MONITOR
```

## Configuration

### Redis Configuration File
```bash
# Find configuration file
sudo find / -name "redis.conf" 2>/dev/null

# Edit configuration
sudo nano /etc/redis/redis.conf
```

### Common Configuration Options
```bash
# Set port
port 6379

# Set bind address
bind 127.0.0.1

# Set password
requirepass your_password

# Set max memory
maxmemory 256mb

# Set eviction policy
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

### Apply Configuration Changes
```bash
# Restart Redis
sudo systemctl restart redis-server

# Or reload configuration
redis-cli CONFIG REWRITE
```
