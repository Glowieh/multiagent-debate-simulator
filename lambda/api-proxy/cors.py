"""CORS headers for API Gateway proxy responses."""

from __future__ import annotations

import os


def cors_headers() -> dict[str, str]:
    origin = os.environ.get("CORS_ALLOWED_ORIGIN")
    if not origin:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Vary": "Origin",
    }
