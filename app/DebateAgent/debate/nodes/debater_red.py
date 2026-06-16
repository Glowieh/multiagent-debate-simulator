from debate.agents import instances
from debate.nodes.debater import make_debater_nodes

debater_red_agent_node, debater_red_finish_node = make_debater_nodes(
    speaker="Red",
    get_agent=lambda: instances.get_debater_red(),
    turn_key="turn_red",
    wikipedia_key="wikipedia_turn_red",
)
