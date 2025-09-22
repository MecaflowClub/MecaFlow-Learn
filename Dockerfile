FROM continuumio/miniconda3:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create conda environment and install dependencies
RUN conda create -n app-env python=3.11 && \
    conda install -n app-env -c conda-forge pythonocc-core && \
    conda init bash && \
    echo "conda activate app-env" > ~/.bashrc

# Create a modified requirements file without OCC-Core
RUN grep -v "OCC-Core" requirements.txt > requirements_docker.txt

# Install Python dependencies
SHELL ["/bin/bash", "-c"]
RUN source ~/.bashrc && pip install --no-cache-dir -r requirements_docker.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV LD_LIBRARY_PATH=/usr/local/lib

# Start FastAPI application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT