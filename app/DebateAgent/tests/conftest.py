import os
from typing import Any

import pytest

os.environ["LANGSMITH_TRACING"] = "false"
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig


class ToolAwareFakeChatModel(FakeListChatModel):
    def bind_tools(
        self,
        tools: object,
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> "ToolAwareFakeChatModel":
        return self

    def invoke(
        self,
        input: LanguageModelInput,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        content = super().invoke(input, config, **kwargs)
        return AIMessage(content=str(content))


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "debate.agents.base.load_model",
        lambda: ToolAwareFakeChatModel(responses=["fake debater response"]),
    )
