#!/bin/sh
set -e

Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && /opt/venv/bin/python -m uvicorn getgather.api.main:app --host 0.0.0.0 --port 8000 --log-level debug