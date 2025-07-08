#!/bin/sh
set -e

exec /opt/venv/bin/python -m uvicorn getgather.api.main:app --host 0.0.0.0 --port 8000