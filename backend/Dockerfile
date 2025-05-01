# Use slim Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (add ffmpeg)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY app ./app
COPY api ./api
COPY config ./config

# Optional: secrets mount path (won't be used at build time)
RUN mkdir -p /run/secrets

# Entrypoint
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
