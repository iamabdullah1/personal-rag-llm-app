FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Create data directory
RUN mkdir -p data/chroma_db

# Run data ingestion at build time
RUN python ingest_data.py

# Expose port (HF Spaces uses port 7860)
EXPOSE 7860

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
