from collections.abc import Mapping
from typing import Any, cast

from langchain_core.messages import BaseMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES


def extract_query_from_tool_call(tool_call: Mapping[str, Any]) -> str:
    args = tool_call.get("args", {})
    if isinstance(args, dict):
        args_dict = cast(dict[str, Any], args)
        query = args_dict.get("query")
        if query is not None:
            return str(query)
    return ""


def message_text(message: BaseMessage) -> str:
    return final_text_from_message(message)


def final_text_from_message(message: BaseMessage) -> str:
    content = cast(object, getattr(message, "content", ""))
    if isinstance(content, str):
        return content
    return str(content)


def clear_turn_messages() -> list[RemoveMessage]:
    return [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
