# Stage 1: Builder — compile dependencies with Python 3.12
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="/usr/local/bin" sh

COPY workers/requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Runtime — Python 3.12 slim (Playwright installed fresh)
FROM python:3.12-slim

WORKDIR /app

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder (same Python 3.12 ABI)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy worker code into /app/workers/ so `workers.celery_app` resolves
COPY workers/ /app/workers/

# Default command (overridden by docker-compose per service)
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info"]
