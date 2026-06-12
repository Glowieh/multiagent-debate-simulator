from langgraph.prebuilt import ToolNode

from debate.tools.wikipedia import WIKIPEDIA_TOOLS

wikipedia_tool_node = ToolNode(WIKIPEDIA_TOOLS, messages_key="turn_messages")
