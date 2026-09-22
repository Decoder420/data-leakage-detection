# Multi-stage Python FastAPI Dockerfile — DecodeX Security Technologies Private Limited
# Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.

FROM python:3.11-slim

WORKDIR /app

# Install build essentials and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code and static frontend files
COPY backend /app/backend
COPY data /app/data

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
