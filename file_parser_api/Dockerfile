FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# --- Install only runtime dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Office & OCR
    libreoffice \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    # PDF utilities (convert_from_path cần poppler)
    poppler-utils \
    # Ảnh (pillow, pdf2image)
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    libharfbuzz0b \
    libfribidi0 \
    libglib2.0-0 \
    # Font cơ bản (tránh lỗi render khi OCR tiếng Việt)
    fonts-dejavu \
    fonts-liberation \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Install Python dependencies ---
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Copy source code ---
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
