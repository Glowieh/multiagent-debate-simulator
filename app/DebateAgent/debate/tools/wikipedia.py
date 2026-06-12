import wikipediaapi
from langchain_core.tools import tool
from wikipediaapi import WikipediaException, WikiRateLimitError

from debate.settings import get_settings

MAX_SUMMARY_CHARS = 1500

_wiki_client: wikipediaapi.Wikipedia | None = None


def get_wikipedia_client() -> wikipediaapi.Wikipedia:
    global _wiki_client
    if _wiki_client is None:
        settings = get_settings()
        _wiki_client = wikipediaapi.Wikipedia(
            user_agent=settings.wikipedia_user_agent,
            language="en",
            max_retries=settings.wikipedia_max_retries,
            retry_wait=settings.wikipedia_retry_wait,
        )
    return _wiki_client


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for factual information about a topic."""
    try:
        wiki = get_wikipedia_client()
        results = wiki.search(query, limit=1)
        if not results.pages:
            return f"No Wikipedia page found for '{query}'."
        page = next(iter(results.pages.values()))
        if not page.exists():
            return f"No Wikipedia page found for '{query}'."
        summary = page.summary
        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[:MAX_SUMMARY_CHARS].rsplit(" ", 1)[0] + "…"
        return f"Title: {page.title}\n\n{summary}"
    except WikiRateLimitError:
        return "Wikipedia rate limit exceeded; try again later."
    except WikipediaException as exc:
        return f"Wikipedia lookup failed: {exc}"


WIKIPEDIA_TOOLS = [wikipedia_search]
