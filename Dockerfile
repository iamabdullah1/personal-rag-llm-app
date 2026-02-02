FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY personal-rag-app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY personal-rag-app/backend/ .

# Create data directory
RUN mkdir -p data/chroma_db

# Expose port (HF Spaces uses port 7860)
EXPOSE 7860

# Create startup script that runs ingestion then starts server
RUN echo '#!/bin/bash\npython ingest_data.py\nuvicorn app.main:app --host 0.0.0.0 --port 7860' > /app/start.sh && chmod +x /app/start.sh

# Start server (run ingestion at startup, not during build)
CMD ["/bin/bash", "/app/start.sh"]
