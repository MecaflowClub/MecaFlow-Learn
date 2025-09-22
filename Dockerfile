FROM continuumio/miniconda3:latest AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create conda environment and install dependencies
RUN conda create -n app-env python=3.11 && \
    conda install -n app-env -c conda-forge pythonocc-core && \
    conda clean -afy && \
    conda init bash && \
    echo "conda activate app-env" >> ~/.bashrc

# Create a modified requirements file without OCC-Core
RUN grep -v "OCC-Core" requirements.txt > requirements_docker.txt

# Install Python dependencies
SHELL ["/bin/bash", "-c"]
RUN /opt/conda/envs/app-env/bin/pip install --no-cache-dir -r requirements_docker.txt

# Second stage
FROM python:3.11-slim

# Install required runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglu1-mesa \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy conda environment from builder
COPY --from=builder /opt/conda/envs/app-env /opt/conda/envs/app-env
ENV PATH=/opt/conda/envs/app-env/bin:$PATH

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Add healthcheck
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--workers", "1"]

# Set environment variables
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV LD_LIBRARY_PATH=/usr/local/lib

# Start FastAPI application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT