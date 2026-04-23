# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-alpine AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip --timeout=120 --retries=5 && \
    pip install --no-cache-dir --timeout=120 --retries=5 \
    --prefix=/install -r requirements.txt

# ── Stage 2: Production image ─────────────────────────────────────
FROM python:3.11-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appgroup . .

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c \
  "import redis, os; r=redis.Redis(host=os.environ.get('REDIS_HOST','redis')); r.ping()" \
  || exit 1

CMD ["python", "worker.py"]
