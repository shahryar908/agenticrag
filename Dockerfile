# Production Dockerfile for Advanced RAG System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY pyproject.toml ./

# Install Python dependencies using pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    groq \
    chromadb \
    sentence-transformers \
    pypdf \
    python-dotenv

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
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]