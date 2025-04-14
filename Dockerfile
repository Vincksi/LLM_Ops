FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY llm_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY llm_gateway/ ./llm_gateway/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV AUTH_ENABLED=false

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "llm_gateway.main"] 