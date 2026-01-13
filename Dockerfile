# Production Dockerfile for Advanced RAG System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv package manager
RUN pip install --no-cache-dir uv

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY api_server.py complete_rag.py agentic_rag.py ./

# Note: .env is NOT copied - environment variables come from Kubernetes Secret
# In K8s, GROQ_API_KEY is injected via secretRef

# Create directories
RUN mkdir -p /app/chroma_db /app/uploads

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]