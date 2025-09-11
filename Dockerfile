# Stage 1: Combined Builder (Backend + Frontend)
FROM mirror.gcr.io/library/python:3.13-slim-bookworm AS builder

ARG MULTI_USER_ENABLED=false
ENV MULTI_USER_ENABLED=${MULTI_USER_ENABLED}

# Install build dependencies and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
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

# Copy Python dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install Python dependencies without workspace members
RUN uv sync --no-dev --no-install-workspace

# Install Playwright browsers
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN $VENV_PATH/bin/patchright install --with-deps chromium

# Copy Node.js dependency files
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY eslint.config.js ./

# Install Node.js dependencies
RUN npm ci

# Copy backend source code
COPY getgather /app/getgather
COPY tests /app/tests
COPY entrypoint.sh /app/entrypoint.sh
COPY extract_openapi.py /app/extract_openapi.py

# Install the workspace package
RUN uv sync --no-dev

# Generate OpenAPI schema and TypeScript types using the installed venv
RUN mkdir -p frontend/__generated__ && \
    $VENV_PATH/bin/python extract_openapi.py -o /tmp/openapi.json && \
    npx openapi-typescript /tmp/openapi.json -o frontend/__generated__/api.d.ts

# Copy frontend source code (excluding generated files that might exist)
COPY frontend/ ./frontend/

# Build frontend
RUN npm run build

# Stage 2: Final image
FROM mirror.gcr.io/library/python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -

RUN apt-get install -y \
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
    nodejs \
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
EXPOSE 23456
# port for VNC server
EXPOSE 5900
# port for MCP inspector server
EXPOSE 6277

ENTRYPOINT ["/app/entrypoint.sh"]
