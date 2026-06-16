from collections.abc import Mapping
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, RemoveMessage
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


def final_turn_content(turn_messages: list[BaseMessage]) -> str:
    for message in reversed(turn_messages):
        if isinstance(message, AIMessage):
            text = final_text_from_message(message).strip()
            if text:
                return text
    if turn_messages:
        return final_text_from_message(turn_messages[-1])
    return ""


def extract_chunk_content(chunk: object) -> str:
    if chunk is None:
        return ""
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in cast(list[object], content):
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                item_dict = cast(dict[str, Any], item)
                text = item_dict.get("text")
                if text is not None:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)
