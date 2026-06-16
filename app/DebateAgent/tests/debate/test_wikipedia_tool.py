from unittest.mock import MagicMock

import pytest
from wikipediaapi import WikiRateLimitError

from debate.tools import wikipedia as wikipedia_module
from debate.tools.wikipedia import wikipedia_search


def _mock_search_results(page: MagicMock | None) -> MagicMock:
    results = MagicMock()
    results.pages = {page.title: page} if page is not None else {}
    return results


def test_wikipedia_search_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    page = MagicMock()
    page.title = "Renewable energy"
    page.summary = "Renewable energy comes from natural sources."
    page.exists.return_value = True

    client = MagicMock()
    client.search.return_value = _mock_search_results(page)
    monkeypatch.setattr(wikipedia_module, "_wiki_client", None)
    monkeypatch.setattr(
        wikipedia_module,
        "get_wikipedia_client",
        lambda: client,
    )

    result = wikipedia_search.invoke({"query": "renewable energy"})  # pyright: ignore[reportUnknownMemberType]

    assert "Renewable energy" in result
    assert "natural sources" in result
    client.search.assert_called_once_with("renewable energy", limit=1)


def test_wikipedia_search_handles_missing_page(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.search.return_value = _mock_search_results(None)
    monkeypatch.setattr(wikipedia_module, "_wiki_client", None)
    monkeypatch.setattr(
        wikipedia_module,
        "get_wikipedia_client",
        lambda: client,
    )

    result = wikipedia_search.invoke({"query": "nonexistent topic xyz"})  # pyright: ignore[reportUnknownMemberType]

    assert "No Wikipedia page found" in result


def test_wikipedia_search_truncates_long_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = MagicMock()
    page.title = "Long article"
    page.summary = "word " * 500
    page.exists.return_value = True

    client = MagicMock()
    client.search.return_value = _mock_search_results(page)
    monkeypatch.setattr(wikipedia_module, "_wiki_client", None)
    monkeypatch.setattr(
        wikipedia_module,
        "get_wikipedia_client",
        lambda: client,
    )

    result = wikipedia_search.invoke({"query": "long article"})  # pyright: ignore[reportUnknownMemberType]

    assert len(result) < len(page.summary) + 20
    assert result.endswith("…")


def test_wikipedia_search_handles_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.search.side_effect = WikiRateLimitError("https://en.wikipedia.org/w/api.php")
    monkeypatch.setattr(wikipedia_module, "_wiki_client", None)
    monkeypatch.setattr(
        wikipedia_module,
        "get_wikipedia_client",
        lambda: client,
    )

    result = wikipedia_search.invoke({"query": "renewable energy"})  # pyright: ignore[reportUnknownMemberType]

    assert result == "Wikipedia rate limit exceeded; try again later."


def test_wikipedia_search_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import time
    from concurrent.futures import ThreadPoolExecutor

    def slow_search(query: str) -> str:
        time.sleep(0.2)
        return "too slow"

    monkeypatch.setattr(wikipedia_module, "_search_wikipedia", slow_search)
    monkeypatch.setattr(
        wikipedia_module,
        "_wiki_executor",
        ThreadPoolExecutor(max_workers=1),
    )
    monkeypatch.setattr(
        "debate.tools.wikipedia.get_settings",
        lambda: type(
            "Settings",
            (),
            {"wikipedia_request_timeout_seconds": 0.05},
        )(),
    )

    result = wikipedia_search.invoke({"query": "slow topic"})  # pyright: ignore[reportUnknownMemberType]

    assert "timed out" in result
