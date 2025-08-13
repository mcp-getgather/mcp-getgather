# Stage 1: Frontend Builder
FROM mirror.gcr.io/library/node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY eslint.config.js ./

# Install Node.js dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./frontend/

# Build frontend
RUN npm run build

# Stage 2: Backend Builder  
FROM python:3.13-bookworm AS backend-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/


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

# Copy only dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies without workspace members
RUN uv sync --no-dev --no-install-workspace

# Install Playwright browsers with dependencies (Ubuntu supports this properly)
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN $VENV_PATH/bin/patchright install --with-deps chromium

# Now copy the actual source code
COPY getgather /app/getgather
COPY tests /app/tests
COPY entrypoint.sh /app/entrypoint.sh

# Install the workspace package
RUN uv sync --no-dev

# Stage 2: Final image
FROM python:3.13-slim-bookworm

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
    x11vnc \
    jwm \
    x11-apps \
    dbus \
    dbus-x11 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=backend-builder /app/.venv /opt/venv
COPY --from=backend-builder /app/getgather /app/getgather
COPY --from=backend-builder /app/tests /app/tests
COPY --from=backend-builder /app/entrypoint.sh /app/entrypoint.sh
COPY --from=backend-builder /opt/ms-playwright /opt/ms-playwright
COPY --from=frontend-builder /app/getgather/api/frontend /app/getgather/api/frontend

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
