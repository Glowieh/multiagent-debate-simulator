"""Bootstrap runtime environment from Secrets Manager (production)."""

from __future__ import annotations

import json
import os
from typing import Any

import boto3

_client: Any | None = None


def _secrets_client() -> Any:
    global _client
    if _client is None:
        region = os.environ.get("AWS_REGION", "eu-west-1")
        _client = boto3.client("secretsmanager", region_name=region)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return _client  # pyright: ignore[reportUnknownVariableType]


def configure_runtime_env() -> None:
    if os.environ.get("LANGSMITH_API_KEY"):
        return

    secret_arn = os.environ.get("LANGSMITH_SECRET_ARN")
    if not secret_arn:
        return

    response = _secrets_client().get_secret_value(SecretId=secret_arn)
    raw = response.get("SecretString")
    if not raw:
        return

    data = json.loads(raw)
    api_key = data.get("api_key")
    if isinstance(api_key, str) and api_key:
        os.environ["LANGSMITH_API_KEY"] = api_key
