# PakMind Backend — Hugging Face Space Dockerfile
# Free hosting on huggingface.co/spaces (no credit card required)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (lxml needs libxml2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Hugging Face Spaces exposes PORT=7860 by default
ENV PORT=7860

# Run with uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
