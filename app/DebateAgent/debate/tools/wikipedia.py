import wikipedia
from langchain_core.tools import tool
from wikipedia.exceptions import DisambiguationError, PageError

MAX_SUMMARY_CHARS = 1500


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for factual information about a topic."""
    try:
        page_title = wikipedia.search(query, results=1)[0]
        page = wikipedia.page(page_title, auto_suggest=False)
        summary = page.summary
        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[:MAX_SUMMARY_CHARS].rsplit(" ", 1)[0] + "…"
        return f"Title: {page.title}\n\n{summary}"
    except DisambiguationError as exc:
        options = ", ".join(exc.options[:5])
        return f"Disambiguation needed for '{query}'. Options: {options}"
    except (PageError, IndexError):
        return f"No Wikipedia page found for '{query}'."
    except Exception as exc:
        return f"Wikipedia lookup failed: {exc}"


WIKIPEDIA_TOOLS = [wikipedia_search]
