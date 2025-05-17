# Use pinned, stable base with fewer vulnerabilities
FROM python:3.11.9-slim-bullseye

# Set working directory
WORKDIR /app

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (minimal and required for aeneas + ffmpeg)
RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg \
    espeak \
    libespeak-dev \
    libmagic-dev \
    build-essential \
    git && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Pre-install compatible versions for aeneas build
RUN pip install --no-cache-dir "numpy<2" setuptools wheel

# Install aeneas separately (build isolation disabled)
RUN pip install --no-cache-dir --no-build-isolation aeneas==1.7.3.0

# Copy requirements and install remaining packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual application code
COPY app ./app
COPY api ./api
COPY config ./config
COPY emotion_model/ ./emotion_model/

# Create secrets dir (used at runtime, not build time)
RUN mkdir -p /run/secrets
RUN mkdir -p /app/assets/audio/tts

EXPOSE 8080

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
