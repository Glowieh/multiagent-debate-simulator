import pytest
from pydantic import ValidationError

from debate.settings import DebateSettings


def test_max_turns_per_debater_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        DebateSettings(max_turns_per_debater=0)
