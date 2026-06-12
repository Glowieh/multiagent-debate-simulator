"""Map LangGraph stream events to debate SSE events.

Message ``name`` fields use ``"Red"``, ``"Green"``, ``"Summarizer"``.
Stream events use lowercase ``"summarizer"`` to match the frontend Speaker type.
"""

from collections.abc import Mapping
from typing import Any, Literal, cast

from langchain_core.messages import AIMessage

from api.schemas.debate import (
    DebateCompletedEvent,
    DebateEvent,
    DebateStartedEvent,
    ErrorEvent,
    MessageChunkEvent,
    SummaryEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
    TurnCompletedEvent,
    TurnStartedEvent,
)

Speaker = Literal["Red", "Green", "summarizer"]
DEBATER_AGENT_NODES = frozenset({"debater_red_agent", "debater_green_agent"})
DEBATER_FINISH_NODES = frozenset({"debater_red_finish", "debater_green_finish"})
TRACKED_NODES = DEBATER_AGENT_NODES | DEBATER_FINISH_NODES | frozenset({"summarizer"})
WIKIPEDIA_TOOL_NODE = "wikipedia_tool"


def _speaker_for_node(node: str) -> Speaker | None:
    if node in {"debater_red", "debater_red_agent", "debater_red_finish"}:
        return "Red"
    if node in {"debater_green", "debater_green_agent", "debater_green_finish"}:
        return "Green"
    if node == "summarizer":
        return "summarizer"
    return None


def _debater_agent_node(
    node: str,
) -> Literal["debater_red_agent", "debater_green_agent"] | None:
    if node == "debater_red_agent":
        return "debater_red_agent"
    if node == "debater_green_agent":
        return "debater_green_agent"
    return None


def _extract_chunk_content(chunk: object) -> str:
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


def _extract_message_content(output: object) -> str:
    if output is None:
        return ""
    messages: object = output
    if isinstance(output, dict):
        output_dict = cast(dict[str, Any], output)
        raw_messages = output_dict.get("messages")
        if raw_messages is None:
            raw_messages = output_dict.get("output")
        messages = raw_messages
    if isinstance(messages, list) and messages:
        message_list = cast(list[object], messages)
        return _extract_chunk_content(message_list[-1])
    return _extract_chunk_content(cast(object, messages))


def _state_from_data(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("input", "output"):
        value = data.get(key)
        if isinstance(value, dict) and "turn_red" in value:
            return cast(dict[str, Any], value)
    return {}


def _extract_query_from_tool_call(tool_call: Mapping[str, Any]) -> str:
    args = tool_call.get("args", {})
    if isinstance(args, dict):
        args_dict = cast(dict[str, Any], args)
        query = args_dict.get("query")
        if query is not None:
            return str(query)
    return ""


def _extract_wikipedia_queries(state: dict[str, Any]) -> list[str]:
    turn_messages = state.get("turn_messages", [])
    if isinstance(turn_messages, list):
        message_list = cast(list[object], turn_messages)
        for message in reversed(message_list):
            if isinstance(message, AIMessage) and message.tool_calls:
                queries = [
                    _extract_query_from_tool_call(tool_call)
                    for tool_call in message.tool_calls
                ]
                if queries:
                    return queries
            if isinstance(message, dict):
                message_dict = cast(dict[str, Any], message)
                tool_calls = message_dict.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    tool_call_list = cast(list[object], tool_calls)
                    queries = [
                        _extract_query_from_tool_call(
                            cast(Mapping[str, Any], tool_call)
                        )
                        for tool_call in tool_call_list
                    ]
                    if queries:
                        return queries
    pending = state.get("pending_tool_query")
    if pending:
        return [str(pending)]
    return [""]


class DebateEventMapper:
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.debate_started_emitted = False
        self.active_turns: dict[str, int] = {}
        self.emitted_turn_starts: set[tuple[str, int]] = set()
        self.emitted_turn_completions: set[tuple[str, int]] = set()
        self.pending_tool_queries: dict[str, list[str]] = {}
        self.summary_emitted = False
        self.debate_completed_emitted = False

    def map_langgraph_event(self, event: dict[str, Any]) -> list[DebateEvent]:
        kind = str(event.get("event", ""))
        name = str(event.get("name", ""))
        metadata_obj = event.get("metadata", {})
        metadata: dict[str, Any] = (
            cast(dict[str, Any], metadata_obj)
            if isinstance(metadata_obj, dict)
            else {}
        )
        data_obj = event.get("data", {})
        data: dict[str, Any] = (
            cast(dict[str, Any], data_obj) if isinstance(data_obj, dict) else {}
        )

        results: list[DebateEvent] = []

        if kind == "on_chat_model_stream":
            stream_speaker = _speaker_for_node(str(metadata.get("langgraph_node", "")))
            if stream_speaker is None:
                return results
            chunk = data.get("chunk")
            content = _extract_chunk_content(chunk)
            if content:
                results.append(
                    MessageChunkEvent(speaker=stream_speaker, content=content)
                )
            return results

        if name == WIKIPEDIA_TOOL_NODE:
            return self._map_wikipedia_tool_event(kind, data)

        if name not in TRACKED_NODES:
            return results

        node = name
        agent_node = _debater_agent_node(node)

        if kind == "on_chain_start" and agent_node is not None:
            state = _state_from_data(data)
            turn_messages = state.get("turn_messages", [])
            if turn_messages:
                return results
            if not self.debate_started_emitted:
                self.debate_started_emitted = True
                results.append(DebateStartedEvent(topic=self.topic))
            turn_key = "turn_red" if agent_node == "debater_red_agent" else "turn_green"
            turn = int(state.get(turn_key, 0)) + 1
            turn_key_tuple = (agent_node, turn)
            if turn_key_tuple in self.emitted_turn_starts:
                return results
            self.emitted_turn_starts.add(turn_key_tuple)
            speaker: Literal["Red", "Green"] = (
                "Red" if agent_node == "debater_red_agent" else "Green"
            )
            self.active_turns[agent_node] = turn
            results.append(TurnStartedEvent(speaker=speaker, turn=turn))

        if kind == "on_chain_end" and node in DEBATER_FINISH_NODES:
            agent_node_key = node.replace("_finish", "_agent")
            turn = self.active_turns.get(agent_node_key)
            if turn is None:
                return results

            completion_key = (agent_node_key, turn)
            if completion_key not in self.emitted_turn_completions:
                self.emitted_turn_completions.add(completion_key)
                speaker = "Red" if node == "debater_red_finish" else "Green"
                results.append(TurnCompletedEvent(speaker=speaker, turn=turn))

        if kind == "on_chain_end" and node == "summarizer":
            if not self.summary_emitted:
                content = _extract_message_content(data.get("output"))
                if content:
                    results.append(SummaryEvent(content=content))
                    self.summary_emitted = True

        return results

    def _map_wikipedia_tool_event(
        self, kind: str, data: dict[str, Any]
    ) -> list[DebateEvent]:
        results: list[DebateEvent] = []
        state = _state_from_data(data)
        speaker_value = state.get("active_speaker")
        if speaker_value not in {"Red", "Green"}:
            return results
        speaker = cast(Literal["Red", "Green"], speaker_value)
        queries = _extract_wikipedia_queries(state)

        if kind == "on_chain_start":
            self.pending_tool_queries[speaker] = queries
            for query in queries:
                results.append(
                    ToolCallStartedEvent(speaker=speaker, query=query)
                )
        elif kind == "on_chain_end":
            completed_queries = self.pending_tool_queries.pop(speaker, queries)
            for query in completed_queries:
                results.append(
                    ToolCallCompletedEvent(speaker=speaker, query=query)
                )

        return results

    def completion_events(self) -> list[DebateEvent]:
        if self.debate_completed_emitted:
            return []
        self.debate_completed_emitted = True
        return [DebateCompletedEvent()]

    def error_events(self, message: str) -> list[DebateEvent]:
        events: list[DebateEvent] = [ErrorEvent(message=message)]
        events.extend(self.completion_events())
        return events
