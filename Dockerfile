# Dockerfile for Aether AI Engine API
# Multi-stage build for smaller image size

FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-api.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements-api.txt

# Final stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY inputs/ ./inputs/
COPY .env .env

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the API
CMD ["uvicorn", "src.aether_2.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

