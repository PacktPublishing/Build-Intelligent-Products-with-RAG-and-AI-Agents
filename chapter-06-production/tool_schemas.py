"""The tool menu shown to the model.

These are JSON schemas, not executable functions. The model can request
one of these names; ``roast.py`` decides whether that request maps to a
real Python function in ``tools.py``.
"""

SCRAPE_TOOL_SCHEMA = {
    "type": "function",
    "name": "fetch_webpage",
    "description": (
        "Fetch the visible text of a public HTTP or HTTPS job-posting URL. "
        "Use this when the user supplies a URL. This tool is read-only."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The exact public job-posting URL to fetch.",
            }
        },
        "required": ["url"],
        "additionalProperties": False,
    },
    "strict": True,
}

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "name": "search_company_culture",
    "description": (
        "Search the public web for concise evidence about a named company's "
        "engineering culture, hiring values, and careers. Use this only when "
        "the user names a company but supplies no URL. This tool is read-only."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "The company name exactly as the user supplied it.",
            }
        },
        "required": ["company_name"],
        "additionalProperties": False,
    },
    "strict": True,
}

AGENT_TOOLS = [SCRAPE_TOOL_SCHEMA, SEARCH_TOOL_SCHEMA]

# Lower-case aliases match the names used in the Chapter 5 manuscript.
scrape_tool_schema = SCRAPE_TOOL_SCHEMA
search_tool_schema = SEARCH_TOOL_SCHEMA
