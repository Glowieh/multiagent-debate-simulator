"""Secrets Manager access with in-process TTL cache."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import boto3

_CACHE_TTL_SECONDS = 300


@dataclass(frozen=True)
class AuthSecrets:
    demo_password: str
    jwt_secret: str


_cache: AuthSecrets | None = None
_cache_expires_at: float = 0.0
_client: Any | None = None


def _secrets_client() -> Any:
    global _client
    if _client is None:
        region = os.environ.get("AWS_REGION", "eu-west-1")
        _client = boto3.client("secretsmanager", region_name=region)
    return _client


def get_auth_secrets() -> AuthSecrets:
    global _cache, _cache_expires_at

    now = time.monotonic()
    if _cache is not None and now < _cache_expires_at:
        return _cache

    secret_arn = os.environ.get("AUTH_SECRET_ARN")
    if not secret_arn:
        raise RuntimeError("AUTH_SECRET_ARN is not set")

    response = _secrets_client().get_secret_value(SecretId=secret_arn)
    raw = response.get("SecretString")
    if not raw:
        raise RuntimeError("Auth secret has no SecretString")

    data = json.loads(raw)
    demo_password = data.get("demo_password")
    jwt_secret = data.get("jwt_secret")
    if not isinstance(demo_password, str) or not isinstance(jwt_secret, str):
        raise RuntimeError("Auth secret JSON missing demo_password or jwt_secret")

    _cache = AuthSecrets(demo_password=demo_password, jwt_secret=jwt_secret)
    _cache_expires_at = now + _CACHE_TTL_SECONDS
    return _cache
