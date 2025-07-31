# Stage 1: Builder
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYPI="0.0.0" \
    VENV_PATH="/app/.venv" \
    UV_FROZEN=1

WORKDIR /app

COPY pyproject.toml uv.lock* ./
COPY getgather /app/getgather
COPY tests /app/tests
COPY entrypoint.sh /app/entrypoint.sh

RUN uv sync --no-dev

# Install Playwright browsers only for full deployment
# so it can be copied to the final stage easily.
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN $VENV_PATH/bin/patchright install --with-deps chromium

# Stage 2: Final image
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    xauth \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libxshmfence1 \
    fonts-liberation \
    libu2f-udev \
    libvulkan1 \
    xfce4 \
    xfce4-goodies \
    x11vnc \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /opt/venv
COPY --from=builder /app/getgather /app/getgather
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh
COPY --from=builder /opt/ms-playwright /opt/ms-playwright

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

# Set Playwright-specific environment variables only for full deployment
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright

# port for FastAPI server
EXPOSE 8000
# port for VNC server
EXPOSE 5900

ENTRYPOINT ["/app/entrypoint.sh"]