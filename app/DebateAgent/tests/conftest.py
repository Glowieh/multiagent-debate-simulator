import os

import pytest

os.environ["LANGSMITH_TRACING"] = "false"
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage


class ToolAwareFakeChatModel(FakeListChatModel):
    def bind_tools(
        self,
        tools: object,
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> "ToolAwareFakeChatModel":
        return self

    def invoke(self, input: object, config: object | None = None, **kwargs: object) -> AIMessage:
        content = super().invoke(input, config, **kwargs)
        if isinstance(content, AIMessage):
            return content
        return AIMessage(content=str(content))


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "debate.agents.base.load_model",
        lambda: ToolAwareFakeChatModel(responses=["fake debater response"]),
    )
