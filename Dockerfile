# Use a modern Python base
FROM python:3.12.2-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # default: don't crash on missing deps (set to "1" to fail-fast)
    FAIL_FAST=0 \
    # common tessdata location on Debian/Ubuntu
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# System dependencies: Tesseract OCR + Poppler (for PDFs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application code
COPY . /app

EXPOSE 8000
# Use --reload only for local/dev; remove it for production
CMD ["uvicorn", "main:app", "--host","0.0.0.0","--port","8000", "--reload"]
