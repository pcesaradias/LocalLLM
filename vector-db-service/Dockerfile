FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create an unprivileged user and download the embedding model into its cache
RUN useradd --create-home --uid 10001 appuser
USER appuser
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
USER root
COPY . .

# Create data directory for ChromaDB (owned by the runtime user so the named
# volume mounted here inherits writable ownership on first creation)
RUN mkdir -p /app/data/chromadb && chown -R appuser:appuser /app

USER appuser
EXPOSE 8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
