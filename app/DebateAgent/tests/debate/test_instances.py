from collections.abc import Iterator

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

import model.load as load_module
from debate.agents import instances
from debate.agents.debater_red import DebaterRed


class ToolAwareFakeListChatModel(FakeListChatModel):
    def bind_tools(
        self,
        tools: object,
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> "ToolAwareFakeListChatModel":
        return self


@pytest.fixture(autouse=True)
def reset_instances() -> Iterator[None]:
    instances.reset_cached_instances()
    load_module.reset_model_cache()
    yield
    instances.reset_cached_instances()
    load_module.reset_model_cache()


def test_get_debater_red_returns_same_instance() -> None:
    first = instances.get_debater_red()
    second = instances.get_debater_red()
    assert first is second


def test_invoke_turn_reuses_cached_model(monkeypatch: pytest.MonkeyPatch) -> None:
    create_count = 0

    def counting_create_model(settings: object) -> ToolAwareFakeListChatModel:
        nonlocal create_count
        create_count += 1
        return ToolAwareFakeListChatModel(responses=["fake"])

    monkeypatch.setattr(load_module, "_create_model", counting_create_model)
    monkeypatch.setattr("debate.agents.base.load_model", load_module.load_model)
    agent = DebaterRed()
    agent.invoke_turn(
        [],
        topic="Topic",
        context="Context",
        turn=1,
        is_debate_opening=True,
        first_call=True,
    )
    agent.invoke_turn(
        [],
        topic="Topic",
        context="Context",
        turn=2,
        is_debate_opening=False,
        first_call=True,
    )

    assert create_count == 1
