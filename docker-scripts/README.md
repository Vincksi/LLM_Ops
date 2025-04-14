# Docker Scripts

This directory contains helper scripts for managing the LLM Gateway Docker deployment.

## Scripts

### `pull-models.sh`

Downloads models into the Ollama container.

Usage:
```bash
# Make script executable
chmod +x docker-scripts/pull-models.sh

# Pull the default model (llama3.2:1b)
./docker-scripts/pull-models.sh

# Pull specific models
./docker-scripts/pull-models.sh llama2 mistral codellama
```

### `test-api.sh`

Tests the LLM Gateway API endpoints.

Usage:
```bash
# Make script executable
chmod +x docker-scripts/test-api.sh

# Run the API tests
./docker-scripts/test-api.sh
```

Note: This script requires `jq` to be installed for parsing JSON responses. Install it with:
```bash
# For Debian/Ubuntu
sudo apt-get install jq

# For macOS
brew install jq

# For Windows (with Chocolatey)
choco install jq
```

## Common Operations

### Starting the Services

```bash
docker-compose up -d
```

### Checking Service Status

```bash
docker-compose ps
```

### Viewing Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs llm-gateway

# Follow logs
docker-compose logs -f
```

### Stopping the Services

```bash
docker-compose down
```

### Rebuilding the LLM Gateway

```bash
docker-compose build llm-gateway
docker-compose up -d llm-gateway
```

### Accessing Redis CLI

```bash
docker exec -it redis redis-cli
```

### Entering the LLM Gateway Container

```bash
docker exec -it llm-gateway bash
``` 