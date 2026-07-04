# Ollama Setup Guide

## Docker Setup (Included in Compose)

Ollama is included in the Docker Compose configuration. When you run:

```bash
docker-compose up -d ollama
```

It automatically:
- Pulls the `ollama/ollama` image
- Exposes port `11434`
- Persists data in a Docker volume
- Supports GPU acceleration (if configured)

### Verify Docker Ollama
```bash
# Check if container is running
docker-compose ps ollama

# Check Ollama status
docker-compose exec ollama ollama list

# Test API
curl http://localhost:11434/api/tags
```

## Manual Installation

### Linux
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Or install as a service
sudo systemctl enable ollama
sudo systemctl start ollama
```

### macOS
```bash
# Install using Homebrew
brew install ollama

# Start Ollama
ollama serve
```

### Windows
1. Download installer from https://ollama.com/download
2. Run the installer
3. Follow the setup wizard
4. Ollama will start automatically

## Pulling Models

### List Available Models
```bash
# Using Docker
docker-compose exec ollama ollama list

# Using local Ollama
ollama list
```

### Pull Models
```bash
# Pull Llama 3
docker-compose exec ollama ollama pull llama3

# Pull Mistral
docker-compose exec ollama ollama pull mistral

# Pull other models
docker-compose exec ollama ollama pull codellama
docker-compose exec ollama ollama pull phi
docker-compose exec ollama ollama pull gemma
```

### Using Local Ollama
```bash
# Pull models locally
ollama pull llama3
ollama pull mistral
```

### Check Downloaded Models
```bash
# List all models
ollama list

# Show model details
ollama show llama3
ollama show mistral
```

## Testing with ollama CLI

### Interactive Chat
```bash
# Start interactive chat with Llama 3
docker-compose exec ollama ollama run llama3

# Start interactive chat with Mistral
docker-compose exec ollama ollama run mistral
```

### One-time Prompts
```bash
# Send a single prompt
docker-compose exec ollama ollama run llama3 "What is the capital of France?"

# Generate code
docker-compose exec ollama ollama run codellama "Write a Python function to sort a list"
```

### List Running Models
```bash
# Check which models are currently loaded
docker-compose exec ollama ollama ps
```

### Stop Running Models
```bash
# Stop all running models
docker-compose exec ollama ollama stop

# Stop specific model
docker-compose exec ollama ollama stop llama3
```

## API Usage

### Generate Text
```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3",
    "prompt": "What is the capital of France?",
    "stream": false
  }'
```

### Chat Endpoint
```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "llama3",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "stream": false
  }'
```

### List Models via API
```bash
curl http://localhost:11434/api/tags
```

### Python Example
```python
import requests

def generate_text(prompt: str, model: str = "llama3"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Usage
response = generate_text("What is the capital of France?")
print(response)
```

### Streaming Response
```python
import requests

def stream_text(prompt: str, model: str = "llama3"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            import json
            data = json.loads(line)
            if "response" in data:
                print(data["response"], end="", flush=True)

# Usage
stream_text("Write a poem about coding")
```

## GPU Configuration

### NVIDIA GPU (Linux)
```bash
# Install NVIDIA drivers
sudo apt update
sudo apt install -y nvidia-driver-535

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

### Docker Compose GPU Configuration
```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### Check GPU Status
```bash
# Check if GPU is available in container
docker-compose exec ollama nvidia-smi

# Check Ollama GPU usage
docker-compose exec ollama ollama ps
```

### CPU Only (No GPU)
If you don't have a GPU, Ollama will use CPU:
```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # No GPU configuration needed
```

## Common Issues

### Ollama Not Starting
```bash
# Check container logs
docker-compose logs ollama

# Check if port is in use
sudo lsof -i :11434

# Restart Ollama
docker-compose restart ollama
```

### Model Not Found
```bash
# List available models
docker-compose exec ollama ollama list

# Pull the model
docker-compose exec ollama ollama pull llama3

# Check model status
docker-compose exec ollama ollama show llama3
```

### GPU Not Detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Check NVIDIA Container Toolkit
docker info | grep -i nvidia

# Restart Docker
sudo systemctl restart docker
```

### Memory Issues
```bash
# Check available memory
free -h

# Stop running models
docker-compose exec ollama ollama stop

# Use smaller model
docker-compose exec ollama ollama pull phi
docker-compose exec ollama ollama run phi
```

### Slow Performance
```bash
# Check if GPU is being used
docker-compose exec ollama nvidia-smi

# Use smaller model
docker-compose exec ollama ollama pull mistral

# Check system resources
htop
```

### API Not Responding
```bash
# Check if Ollama is running
docker-compose ps ollama

# Test API
curl http://localhost:11434/api/tags

# Check container logs
docker-compose logs -f ollama
```

## Model Management

### Remove Models
```bash
# Remove specific model
docker-compose exec ollama ollama rm llama3

# Remove all models
docker-compose exec ollama ollama rm --all
```

### Copy Models Between Containers
```bash
# Export model
docker-compose exec ollama ollama export llama3 > llama3.tar

# Import model
docker-compose exec -T ollama ollama import llama3 < llama3.tar
```

### Model Storage
```bash
# Check model storage location
docker-compose exec ollama ls -la /root/.ollama/models

# Check disk usage
docker-compose exec ollama du -sh /root/.ollama/models
```

## Environment Variables

```env
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_GPU_ENABLED=true
```

## Useful Resources

- Ollama Documentation: https://ollama.com/docs
- Ollama Models: https://ollama.com/library
- Ollama GitHub: https://github.com/ollama/ollama
