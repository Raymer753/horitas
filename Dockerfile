# ── Stage 1: Builder ─────────────────────────
FROM python:3.14-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────
FROM python:3.14-slim

# Install ffmpeg (required for discord.py voice)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd --create-home --shell /bin/bash horitas

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY audio/ ./audio/

# Create data directory (will be mounted as volume)
RUN mkdir -p /app/data && chown -R horitas:horitas /app

# Switch to non-root user
USER horitas

# Healthcheck: verify the bot is writing heartbeat file
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, time; f='/app/data/healthcheck'; exit(0 if os.path.exists(f) and time.time() - os.path.getmtime(f) < 120 else 1)"

# Entry point
CMD ["python", "-m", "src.main"]
