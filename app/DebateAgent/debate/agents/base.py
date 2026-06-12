from abc import ABC
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from debate.tools.wikipedia import WIKIPEDIA_TOOLS
from model.load import load_model


class BaseAgent(ABC):
    name: str
    system_prompt: str
    human_template: str = "Topic: {topic}\n\nPrior debate:\n{context}\n\nYour response:"

    @staticmethod
    def _build_chain(
        system_prompt: str, human_template: str
    ) -> Runnable[dict[str, str | int], str]:
        prompt = ChatPromptTemplate.from_messages(  # pyright: ignore[reportUnknownMemberType]
            [
                ("system", system_prompt),
                ("human", human_template),
            ]
        )
        return prompt | load_model() | StrOutputParser()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    def _human_templates(self) -> dict[str, str]:
        return {"default": self.human_template}

    def _init_chains(self) -> dict[str, Runnable[dict[str, str | int], str]]:
        return {
            name: type(self)._build_chain(self.system_prompt, template)
            for name, template in self._human_templates().items()
        }

    def __init__(self) -> None:
        self._chains = self._init_chains()

    def respond(self, topic: str, context: str, turn: int = 0) -> str:
        result = self._chains["default"].invoke(
            {"topic": topic, "context": context, "turn": turn}
        )
        return str(result)


class DebaterAgent(BaseAgent):
    position: Literal["for", "against"]
    opening_human_template: str = (
        "Topic: {topic}\n\n"
        "Debate so far:\n{context}\n\n"
        "This is your opening statement (turn {turn}). "
        "Argue {position} the proposition. "
        "Present your strongest case. "
        "Reply in exactly 3 brief paragraphs."
    )
    rebuttal_human_template: str = (
        "Topic: {topic}\n\n"
        "Debate so far:\n{context}\n\n"
        "This is turn {turn}. "
        "Argue {position} the proposition. "
        "Respond directly to your opponent's latest argument. "
        "Do not repeat your opening verbatim. "
        "Reply in exactly 3 brief paragraphs."
    )
    _wikipedia_available_instruction: str = (
        "\n\nYou may call wikipedia_search up to 3 times this turn, "
        "or save your Wikipedia lookup for a later turn."
    )
    _wikipedia_exhausted_instruction: str = (
        "\n\nYou have already used your Wikipedia lookup. "
        "Do not call wikipedia_search; argue from the transcript."
    )

    def __init__(self) -> None:
        return

    def _human_templates(self) -> dict[str, str]:
        return {
            "opening": self.opening_human_template,
            "rebuttal": self.rebuttal_human_template,
        }

    def _select_human_template(self, turn: int, *, is_opening: bool) -> str:
        if is_opening:
            return self.opening_human_template
        return self.rebuttal_human_template

    def _wikipedia_instruction(
        self, turn: int, wikipedia_turn: int | None
    ) -> str:
        if wikipedia_turn is None:
            return self._wikipedia_available_instruction
        if wikipedia_turn < turn:
            return self._wikipedia_exhausted_instruction
        return ""

    def build_turn_messages(
        self,
        topic: str,
        context: str,
        turn: int,
        *,
        is_opening: bool,
        wikipedia_turn: int | None = None,
    ) -> list[BaseMessage]:
        template = self._select_human_template(turn, is_opening=is_opening)
        human_content = template.format(
            topic=topic,
            context=context,
            turn=turn,
            position=self.position,
        )
        human_content += self._wikipedia_instruction(turn, wikipedia_turn)
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_content),
        ]

    @staticmethod
    def _has_tool_message(messages: list[BaseMessage]) -> bool:
        return any(isinstance(message, ToolMessage) for message in messages)

    @staticmethod
    def _coerce_ai_message(response: BaseMessage) -> AIMessage:
        if isinstance(response, AIMessage):
            return response
        return AIMessage(content=str(response.content))

    def _ensure_prompt_messages(
        self,
        messages: list[BaseMessage],
        *,
        topic: str,
        context: str,
        turn: int,
        is_opening: bool,
        wikipedia_turn: int | None,
    ) -> list[BaseMessage]:
        if any(isinstance(message, SystemMessage) for message in messages):
            return messages
        return self.build_turn_messages(
            topic, context, turn, is_opening=is_opening, wikipedia_turn=wikipedia_turn
        ) + messages

    def invoke_turn(
        self,
        turn_messages: list[BaseMessage],
        *,
        topic: str,
        context: str,
        turn: int,
        is_opening: bool,
        first_call: bool,
        wikipedia_turn: int | None = None,
    ) -> tuple[list[BaseMessage], AIMessage]:
        model = load_model()
        if wikipedia_turn is None or wikipedia_turn == turn:
            model = model.bind_tools(WIKIPEDIA_TOOLS)
        if first_call:
            messages = self.build_turn_messages(
                topic,
                context,
                turn,
                is_opening=is_opening,
                wikipedia_turn=wikipedia_turn,
            )
        else:
            messages = self._ensure_prompt_messages(
                list(turn_messages),
                topic=topic,
                context=context,
                turn=turn,
                is_opening=is_opening,
                wikipedia_turn=wikipedia_turn,
            )

        response = self._coerce_ai_message(model.invoke(messages))

        if first_call:
            return messages + [response], response
        return [response], response


class SummarizerAgent(BaseAgent):
    human_template: str = (
        "Topic: {topic}\n\n"
        "Full debate transcript:\n{context}\n\n"
        "Write your summary with these sections:\n"
        "1. Brief recap of both sides' main claims\n"
        "2. Red's strongest points\n"
        "3. Green's strongest points\n"
        "4. Verdict — explicitly state whether Red (against) or Green (for) "
        "presented stronger arguments, with 2–3 sentences of justification"
    )
