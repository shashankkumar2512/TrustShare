FROM python:3.12-slim

# ── Set working directory ──────────────────────────────────────────────────
WORKDIR /app

# ── Install system dependencies ────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies ────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ──────────────────────────────────────────────────
COPY . .

# ── Create uploads directory ───────────────────────────────────────────────
RUN mkdir -p uploads keys

# ── Expose port ────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ───────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ── Production startup command ─────────────────────────────────────────────
# workers=2 for production — adjust based on CPU
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]