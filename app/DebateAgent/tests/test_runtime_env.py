import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

import runtime_env


@pytest.fixture(autouse=True)
def reset_runtime_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_SECRET_ARN", raising=False)
    monkeypatch.setattr(runtime_env, "_client", None)


def test_skips_fetch_when_api_key_already_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_API_KEY", "existing-key")
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")

    with patch.object(runtime_env, "_secrets_client") as mock_client:
        runtime_env.configure_runtime_env()

    mock_client.assert_not_called()


def test_sets_api_key_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {
        "SecretString": json.dumps({"api_key": "real-key"})
    }

    with patch.object(runtime_env, "_secrets_client", return_value=mock_sm):
        runtime_env.configure_runtime_env()

    assert runtime_env.os.environ["LANGSMITH_API_KEY"] == "real-key"


def test_fail_open_on_secrets_manager_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")
    mock_sm = MagicMock()
    mock_sm.get_secret_value.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "GetSecretValue",
    )

    with patch.object(runtime_env, "_secrets_client", return_value=mock_sm):
        runtime_env.configure_runtime_env()

    assert "LANGSMITH_API_KEY" not in runtime_env.os.environ


def test_fail_open_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": "not-json"}

    with patch.object(runtime_env, "_secrets_client", return_value=mock_sm):
        runtime_env.configure_runtime_env()

    assert "LANGSMITH_API_KEY" not in runtime_env.os.environ


def test_warns_and_skips_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": json.dumps({})}

    with patch.object(runtime_env, "_secrets_client", return_value=mock_sm):
        runtime_env.configure_runtime_env()

    assert "LANGSMITH_API_KEY" not in runtime_env.os.environ


def test_warns_and_skips_replace_me_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_SECRET_ARN", "arn:aws:secretsmanager:secret")
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {
        "SecretString": json.dumps({"api_key": "REPLACE_ME"})
    }

    with patch.object(runtime_env, "_secrets_client", return_value=mock_sm):
        runtime_env.configure_runtime_env()

    assert "LANGSMITH_API_KEY" not in runtime_env.os.environ
