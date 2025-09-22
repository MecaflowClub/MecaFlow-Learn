FROM python:3.11-slim

# Install system dependencies for OpenCascade
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV LD_LIBRARY_PATH=/usr/local/lib

# Start FastAPI application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT