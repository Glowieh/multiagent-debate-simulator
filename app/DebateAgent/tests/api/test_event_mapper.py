from api.streaming.event_mapper import DebateEventMapper


def test_maps_turn_lifecycle_for_debater_red_agent() -> None:
    mapper = DebateEventMapper(topic="AI in schools")

    started = mapper.map_langgraph_event(
        {
            "event": "on_chain_start",
            "name": "debater_red_agent",
            "metadata": {"langgraph_node": "debater_red_agent"},
            "data": {"input": {"turn_red": 0, "turn_green": 0, "turn_messages": []}},
        }
    )
    assert [event.type for event in started] == ["debate_started", "turn_started"]
    assert started[1].type == "turn_started"
    assert started[1].speaker == "Red"  # pyright: ignore[reportAttributeAccessIssue]
    assert started[1].turn == 1  # pyright: ignore[reportAttributeAccessIssue]

    completed = mapper.map_langgraph_event(
        {
            "event": "on_chain_end",
            "name": "debater_red_finish",
            "metadata": {"langgraph_node": "debater_red_finish"},
            "data": {
                "output": {
                    "messages": [{"type": "ai", "content": "Debater Red response"}],
                    "turn_red": 1,
                }
            },
        }
    )
    assert [event.type for event in completed] == ["turn_completed"]


def test_skips_turn_started_when_turn_messages_not_empty() -> None:
    mapper = DebateEventMapper(topic="Topic")
    events = mapper.map_langgraph_event(
        {
            "event": "on_chain_start",
            "name": "debater_red_agent",
            "metadata": {"langgraph_node": "debater_red_agent"},
            "data": {
                "input": {
                    "turn_red": 1,
                    "turn_green": 0,
                    "turn_messages": [{"type": "tool", "content": "result"}],
                }
            },
        }
    )
    assert events == []


def test_maps_wikipedia_tool_events() -> None:
    mapper = DebateEventMapper(topic="Topic")

    started = mapper.map_langgraph_event(
        {
            "event": "on_chain_start",
            "name": "wikipedia_tool",
            "metadata": {"langgraph_node": "wikipedia_tool"},
            "data": {
                "input": {
                    "turn_red": 1,
                    "turn_green": 0,
                    "active_speaker": "Red",
                    "pending_tool_query": "renewable energy",
                }
            },
        }
    )
    assert len(started) == 1
    assert started[0].type == "tool_call_started"
    assert started[0].speaker == "Red"  # pyright: ignore[reportAttributeAccessIssue]
    assert started[0].query == "renewable energy"  # pyright: ignore[reportAttributeAccessIssue]

    completed = mapper.map_langgraph_event(
        {
            "event": "on_chain_end",
            "name": "wikipedia_tool",
            "metadata": {"langgraph_node": "wikipedia_tool"},
            "data": {
                "output": {
                    "turn_red": 1,
                    "turn_green": 0,
                    "active_speaker": "Red",
                    "pending_tool_query": "renewable energy",
                }
            },
        }
    )
    assert len(completed) == 1
    assert completed[0].type == "tool_call_completed"
    assert completed[0].speaker == "Red"  # pyright: ignore[reportAttributeAccessIssue]
    assert completed[0].query == "renewable energy"  # pyright: ignore[reportAttributeAccessIssue]


def test_maps_wikipedia_tool_events_for_multiple_queries() -> None:
    mapper = DebateEventMapper(topic="Topic")
    ai_with_tools = {
        "type": "ai",
        "content": "",
        "tool_calls": [
            {"name": "wikipedia_search", "args": {"query": "solar power"}, "id": "1"},
            {"name": "wikipedia_search", "args": {"query": "wind energy"}, "id": "2"},
        ],
    }

    started = mapper.map_langgraph_event(
        {
            "event": "on_chain_start",
            "name": "wikipedia_tool",
            "metadata": {"langgraph_node": "wikipedia_tool"},
            "data": {
                "input": {
                    "turn_red": 1,
                    "turn_green": 0,
                    "active_speaker": "Green",
                    "turn_messages": [ai_with_tools],
                    "pending_tool_query": "solar power",
                }
            },
        }
    )
    assert len(started) == 2
    assert started[0].type == "tool_call_started"
    assert started[0].speaker == "Green"  # pyright: ignore[reportAttributeAccessIssue]
    assert started[0].query == "solar power"  # pyright: ignore[reportAttributeAccessIssue]
    assert started[1].type == "tool_call_started"
    assert started[1].query == "wind energy"  # pyright: ignore[reportAttributeAccessIssue]

    completed = mapper.map_langgraph_event(
        {
            "event": "on_chain_end",
            "name": "wikipedia_tool",
            "metadata": {"langgraph_node": "wikipedia_tool"},
            "data": {
                "output": {
                    "turn_red": 1,
                    "turn_green": 0,
                    "active_speaker": "Green",
                }
            },
        }
    )
    assert len(completed) == 2
    assert completed[0].type == "tool_call_completed"
    assert completed[0].query == "solar power"  # pyright: ignore[reportAttributeAccessIssue]
    assert completed[1].type == "tool_call_completed"
    assert completed[1].query == "wind energy"  # pyright: ignore[reportAttributeAccessIssue]


def test_maps_chat_model_stream_to_message_chunk() -> None:
    mapper = DebateEventMapper(topic="Topic")
    events = mapper.map_langgraph_event(
        {
            "event": "on_chat_model_stream",
            "name": "ChatBedrock",
            "metadata": {"langgraph_node": "debater_green_agent"},
            "data": {"chunk": type("Chunk", (), {"content": "Hello"})()},
        }
    )
    assert len(events) == 1
    assert events[0].type == "message_chunk"
    assert events[0].speaker == "Green"  # pyright: ignore[reportAttributeAccessIssue]
    assert events[0].content == "Hello"  # pyright: ignore[reportAttributeAccessIssue]


def test_error_events_include_completion() -> None:
    mapper = DebateEventMapper(topic="Topic")
    events = mapper.error_events("boom")
    assert [event.type for event in events] == ["error", "debate_completed"]
