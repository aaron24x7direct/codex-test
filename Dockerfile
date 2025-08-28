# Use a modern Python base
FROM python:3.12.2-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FAIL_FAST=0 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# System dependencies: Tesseract OCR + Poppler (for PDFs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy code
COPY . /app

# EB's Nginx commonly proxies to 127.0.0.1:5000 by default
EXPOSE 5000

# No --reload in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
