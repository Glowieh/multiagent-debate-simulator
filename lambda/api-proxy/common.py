"""Shared helpers for API proxy Lambdas."""

from __future__ import annotations

import json
import os
import secrets as py_secrets
import time
from typing import Any

import jwt

from secrets_module import get_auth_secrets


JWT_ALGORITHM = "HS256"
JWT_SUBJECT = "demo"
JWT_TTL_SECONDS = 86_400


def cors_headers() -> dict[str, str]:
    origin = os.environ.get("CORS_ALLOWED_ORIGIN")
    if not origin:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Vary": "Origin",
    }


def _json_headers() -> dict[str, str]:
    return {"Content-Type": "application/json", **cors_headers()}


def _unauthorized() -> dict[str, Any]:
    return {
        "statusCode": 401,
        "headers": _json_headers(),
        "body": json.dumps({"error": "Invalid credentials"}),
    }


def login_response(body: str) -> dict[str, Any]:
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        return _unauthorized()

    password = payload.get("password")
    if not isinstance(password, str):
        return _unauthorized()

    secrets = get_auth_secrets()

    if not py_secrets.compare_digest(password, secrets.demo_password):
        return _unauthorized()

    now = int(time.time())
    token = jwt.encode(
        {"sub": JWT_SUBJECT, "iat": now, "exp": now + JWT_TTL_SECONDS},
        secrets.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "statusCode": 200,
        "headers": _json_headers(),
        "body": json.dumps({"accessToken": token, "expiresIn": JWT_TTL_SECONDS}),
    }


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def verify_access_token(token: str | None) -> bool:
    if not token:
        return False
    secrets = get_auth_secrets()
    try:
        jwt.decode(
            token,
            secrets.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError:
        return False
    return True


def api_gateway_json_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": _json_headers(),
        "body": json.dumps(body),
    }


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
