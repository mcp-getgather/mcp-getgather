# Stage 1: Builder
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
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

# Stage 2: Final image
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv /opt/venv
COPY --from=builder /app/getgather /app/getgather
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]