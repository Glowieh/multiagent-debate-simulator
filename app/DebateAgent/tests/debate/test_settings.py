import pytest
from pydantic import ValidationError

from debate.settings import DebateSettings


def test_max_turns_per_debater_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        DebateSettings(max_turns_per_debater=0)


def test_llm_request_timeout_defaults_to_120() -> None:
    settings = DebateSettings()
    assert settings.llm_request_timeout_seconds == 120.0


def test_wikipedia_request_timeout_defaults_to_10() -> None:
    settings = DebateSettings()
    assert settings.wikipedia_request_timeout_seconds == 10.0
