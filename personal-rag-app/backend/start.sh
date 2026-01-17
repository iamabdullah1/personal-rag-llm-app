#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run data ingestion to populate ChromaDB
python ingest_data.py

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
