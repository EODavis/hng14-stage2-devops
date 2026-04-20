# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

# --timeout=120 prevents pip from giving up on slow Lagos connections
# --retries=5 retries failed downloads automatically
RUN pip install --upgrade pip --timeout=120 --retries=5 && \
    pip install --no-cache-dir --timeout=120 --retries=5 \
    --prefix=/install -r requirements.txt

# ── Stage 2: Production image ─────────────────────────────────────
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c \
  "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
  || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
