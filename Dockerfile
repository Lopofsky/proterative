# Pull official base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Create and activate virtual environment
RUN python -m venv /opt/venv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY src/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Don't copy source code - will be mounted in docker-compose
# The container will use the source code from the host

# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Expose port
EXPOSE 8512


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8512", "--reload"]
