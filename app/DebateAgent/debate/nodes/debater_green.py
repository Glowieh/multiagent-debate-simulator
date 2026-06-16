from debate.agents import instances
from debate.nodes.debater import make_debater_nodes

debater_green_agent_node, debater_green_finish_node = make_debater_nodes(
    speaker="Green",
    get_agent=lambda: instances.get_debater_green(),
    turn_key="turn_green",
    wikipedia_key="wikipedia_turn_green",
)
