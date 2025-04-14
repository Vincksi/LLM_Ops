#!/bin/bash
# Script to pull models into Ollama in the Docker environment

# Check if the Ollama container is running
if ! docker ps | grep -q ollama; then
  echo "Error: Ollama container is not running."
  echo "Please start the services with 'docker-compose up -d' first."
  exit 1
fi

# Default models to pull if no arguments provided
MODELS=("llama3.2:1b")

# If models were provided as arguments, use those instead
if [ "$#" -gt 0 ]; then
  MODELS=("$@")
fi

echo "Pulling models into Ollama:"
for MODEL in "${MODELS[@]}"; do
  echo "- Pulling $MODEL..."
  docker exec ollama ollama pull "$MODEL"
  
  if [ $? -eq 0 ]; then
    echo "  ✓ Successfully pulled $MODEL"
  else
    echo "  ✗ Failed to pull $MODEL"
  fi
done

echo ""
echo "Available models:"
docker exec ollama ollama list

echo ""
echo "To test the API, run:"
echo "curl -X POST http://localhost:8000/api/chat/completions \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"model\": \"llama3.2:1b\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello, how are you?\"}]}'" 