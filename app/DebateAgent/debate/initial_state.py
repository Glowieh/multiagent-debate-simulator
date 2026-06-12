from debate.state import DebateState


def build_initial_state(topic: str) -> DebateState:
    return {
        "topic": topic,
        "messages": [],
        "turn_red": 0,
        "turn_green": 0,
        "phase": "debating",
        "turn_messages": [],
        "active_speaker": None,
        "pending_tool_query": None,
        "tool_loop_count": 0,
        "wikipedia_turn_red": None,
        "wikipedia_turn_green": None,
    }
