# Stage 1: Backend Builder
FROM mirror.gcr.io/library/python:3.13-slim-bookworm AS backend-builder

COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
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

# Copy only dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies without workspace members
RUN uv sync --no-dev --no-install-workspace

# Install Playwright browsers only for full deployment
# so it can be copied to the final stage easily.
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN $VENV_PATH/bin/patchright install --with-deps chromium

# Now copy the actual source code
COPY getgather /app/getgather
COPY tests /app/tests
COPY entrypoint.sh /app/entrypoint.sh

# Install the workspace package
RUN uv sync --no-dev

# Generate OpenAPI schema
RUN $VENV_PATH/bin/python -m getgather.generate_openapi -o /tmp/openapi.json

# Stage 2: Frontend Builder
FROM mirror.gcr.io/library/node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY eslint.config.js ./

# Install Node.js dependencies
RUN npm ci

# Copy OpenAPI schema from backend builder
COPY --from=backend-builder /tmp/openapi.json /tmp/openapi.json

# Generate TypeScript types from OpenAPI
RUN mkdir -p frontend/__generated__ && \
    npx openapi-typescript /tmp/openapi.json -o frontend/__generated__/api.d.ts

# Copy frontend source code
COPY frontend/ ./frontend/

# Build frontend
RUN npm run build:ci

# Stage 3: Final image
FROM mirror.gcr.io/library/python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server \
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
COPY --from=frontend-builder /app/getgather/frontend /app/getgather/frontend

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

# Set Playwright-specific environment variables only for full deployment
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
ENV DISPLAY=:99

ARG PORT=23456
ENV PORT=${PORT}

# port for FastAPI server
EXPOSE ${PORT}
# port for VNC server
EXPOSE 5900

ENTRYPOINT ["/app/entrypoint.sh"]
