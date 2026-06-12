from unittest.mock import MagicMock

import pytest

from debate.tools.wikipedia import wikipedia_search


def test_wikipedia_search_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "debate.tools.wikipedia.wikipedia.search",
        lambda query, results=1: ["Renewable energy"],
    )
    page = MagicMock()
    page.title = "Renewable energy"
    page.summary = "Renewable energy comes from natural sources."
    monkeypatch.setattr(
        "debate.tools.wikipedia.wikipedia.page",
        lambda title, auto_suggest=False: page,
    )

    result = wikipedia_search.invoke({"query": "renewable energy"})

    assert "Renewable energy" in result
    assert "natural sources" in result


def test_wikipedia_search_handles_missing_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "debate.tools.wikipedia.wikipedia.search",
        lambda query, results=1: [],
    )

    result = wikipedia_search.invoke({"query": "nonexistent topic xyz"})

    assert "No Wikipedia page found" in result


def test_wikipedia_search_truncates_long_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "debate.tools.wikipedia.wikipedia.search",
        lambda query, results=1: ["Long article"],
    )
    page = MagicMock()
    page.title = "Long article"
    page.summary = "word " * 500
    monkeypatch.setattr(
        "debate.tools.wikipedia.wikipedia.page",
        lambda title, auto_suggest=False: page,
    )

    result = wikipedia_search.invoke({"query": "long article"})

    assert len(result) < len(page.summary) + 20
    assert result.endswith("…")
