# ── Stage 1: Build dependencies ────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Production image ─────────────────────────────
FROM python:3.12-slim AS production

# Security: run as non-root user with no shell
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code (excluding files via .dockerignore)
COPY . .

# Remove files that should never be in the production image
RUN rm -f .env .env.local .env.production .env.example && \
    rm -rf tests/ docs/ *.md

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Drop to non-root user — all subsequent commands run as appuser
USER appuser

# Expose the API port
EXPOSE 8000

# Health check — verify the app is serving responses
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run with gunicorn + uvicorn workers for production
# --limit-request-line and --limit-request-fields prevent header-based attacks
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--limit-request-line", "8190", \
     "--limit-request-fields", "100", \
     "--limit-request-field_size", "8190", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
