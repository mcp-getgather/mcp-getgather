#!/usr/bin/env python3
"""Extract OpenAPI schema from FastAPI app without running the server."""

import argparse
import json
import sys

from getgather.api.api import api_app


def main():
    parser = argparse.ArgumentParser(description="Extract OpenAPI schema from FastAPI app")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path for the OpenAPI schema (defaults to stdout)",
    )

    args = parser.parse_args()

    # Generate the OpenAPI schema
    openapi_schema = api_app.openapi()
    schema_json = json.dumps(openapi_schema, indent=2)

    if args.output:
        # Write to file
        with open(args.output, "w") as f:
            f.write(schema_json)
        print(f"OpenAPI schema written to {args.output}", file=sys.stderr)
    else:
        # Write to stdout
        print(schema_json)


if __name__ == "__main__":
    main()
