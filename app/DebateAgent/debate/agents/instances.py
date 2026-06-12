from debate.agents.debater_green import DebaterGreen
from debate.agents.debater_red import DebaterRed
from debate.agents.summarizer import Summarizer

_debater_red: DebaterRed | None = None
_debater_green: DebaterGreen | None = None
_summarizer: Summarizer | None = None


def get_debater_red() -> DebaterRed:
    global _debater_red
    if _debater_red is None:
        _debater_red = DebaterRed()
    return _debater_red


def get_debater_green() -> DebaterGreen:
    global _debater_green
    if _debater_green is None:
        _debater_green = DebaterGreen()
    return _debater_green


def get_summarizer() -> Summarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = Summarizer()
    return _summarizer
