#!/bin/bash
# Script to test the LLM Gateway API in the Docker environment

# Check if curl is installed
if ! command -v curl &> /dev/null; then
  echo "Error: curl is not installed. Please install it first."
  exit 1
fi

# Default URL
API_URL="http://localhost:8000"

# Check if the LLM Gateway is running
if ! curl -s --head "$API_URL/health" | grep -q "200 OK"; then
  echo "Error: LLM Gateway is not running or not responding."
  echo "Please start the services with 'docker-compose up -d' first."
  exit 1
fi

# Function to test the health endpoint
test_health() {
  echo "Testing health endpoint..."
  curl -s "$API_URL/health" | jq || echo "Failed to parse JSON response"
  echo ""
}

# Function to test models list
test_models() {
  echo "Testing models endpoint..."
  curl -s "$API_URL/api/models" | jq || echo "Failed to parse JSON response"
  echo ""
}

# Function to test chat completion
test_chat_completion() {
  MODEL=${1:-"llama3.2:1b"}
  PROMPT=${2:-"Hello, how are you?"}
  
  echo "Testing chat completion with model '$MODEL'..."
  echo "Prompt: '$PROMPT'"
  
  RESPONSE=$(curl -s -X POST "$API_URL/api/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}]}")
  
  echo "Response:"
  echo "$RESPONSE" | jq || echo "$RESPONSE"
  echo ""
}

# Function to test embeddings
test_embeddings() {
  MODEL=${1:-"llama3.2:1b"}
  TEXT=${2:-"This is a test text for embeddings."}
  
  echo "Testing embeddings with model '$MODEL'..."
  echo "Text: '$TEXT'"
  
  RESPONSE=$(curl -s -X POST "$API_URL/api/embeddings" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"input\": \"$TEXT\"}")
  
  echo "Response (truncated):"
  echo "$RESPONSE" | jq 'del(.data[].embedding)' || echo "$RESPONSE"
  echo ""
}

# Run tests
echo "=== LLM Gateway API Tests ==="
echo "API URL: $API_URL"
echo ""

test_health
test_models

# Test chat completion with default model
test_chat_completion

# Test embeddings with default model
test_embeddings

echo "=== Tests Completed ===" 