"""Bootstrap runtime environment from Secrets Manager (production)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

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

    try:
        response = _secrets_client().get_secret_value(SecretId=secret_arn)
    except ClientError:
        logger.warning(
            "Failed to fetch LangSmith secret from Secrets Manager",
            exc_info=True,
        )
        return
    except Exception:
        logger.warning(
            "Unexpected error fetching LangSmith secret",
            exc_info=True,
        )
        return

    raw = response.get("SecretString")
    if not raw:
        logger.warning("LangSmith secret has no SecretString payload")
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LangSmith secret payload is not valid JSON", exc_info=True)
        return

    api_key = data.get("api_key")
    if not isinstance(api_key, str) or not api_key:
        logger.warning("LangSmith secret is missing api_key")
        return

    if api_key == "REPLACE_ME":
        logger.warning(
            "LangSmith secret still contains placeholder api_key; "
            "replace REPLACE_ME in Secrets Manager before tracing works"
        )
        return

    os.environ["LANGSMITH_API_KEY"] = api_key
