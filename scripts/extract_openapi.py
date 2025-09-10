#!/usr/bin/env python3
"""Extract OpenAPI schema from FastAPI app without running the server."""

import json
import logging
import os
import sys
import warnings
from pathlib import Path

# Suppress all warnings
warnings.filterwarnings("ignore")

# Add parent directory to path to import the app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set minimal required environment variables
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("GIT_REV", "unknown")
os.environ.setdefault("MULTI_USER_ENABLED", "false")

# Disable all logging to prevent output contamination
logging.disable(logging.CRITICAL)

# Redirect stderr to devnull temporarily during import
import io
old_stderr = sys.stderr
sys.stderr = io.StringIO()

try:
    from getgather.api.api import api_app
finally:
    # Restore stderr
    sys.stderr = old_stderr


def main():
    """Extract and save OpenAPI schema."""
    try:
        # Get the OpenAPI schema from the app
        openapi_schema = api_app.openapi()
        
        # Output to stdout so it can be redirected
        print(json.dumps(openapi_schema, indent=2))
    except Exception as e:
        print(f"Error generating OpenAPI schema: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()