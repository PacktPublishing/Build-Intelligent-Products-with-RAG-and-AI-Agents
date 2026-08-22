"""Read-only Python tools: the agent's physical hands.

Every public function follows the Chapter 5 text-error pattern: catch a
failure and return it as plain text, so the model receives an observation
and can fail conversationally instead of crashing the process.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from config import MAX_CHARS, MAX_TOOL_REDIRECTS, TOOL_TIMEOUT_SECONDS

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)
_SEARCH_URL = "https://lite.duckduckgo.com/lite/"
_SEARCH_USER_AGENT = "Mozilla/5.0"
_JOB_PAGE_WARNING_PREFIX = "Tool Warning: Job page detected"


def _plain_text(value: Any) -> str:
    """Normalize one structured-data value into safe, compact text."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(_plain_text(item) for item in value if item is not None)
    elif isinstance(value, dict):
        value = value.get("name") or value.get("value") or ""

    text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def _job_nodes(value: Any):
    """Yield Schema.org JobPosting dictionaries from nested JSON-LD."""
    if isinstance(value, dict):
        node_type = value.get("@type", "")
        types = node_type if isinstance(node_type, list) else [node_type]
        if any(str(item).lower() == "jobposting" for item in types):
            yield value
        for child in value.values():
            yield from _job_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _job_nodes(child)


def _format_location(value: Any) -> str:
    if isinstance(value, list):
        locations = [_format_location(item) for item in value]
        return "; ".join(dict.fromkeys(item for item in locations if item))
    if not isinstance(value, dict):
        return _plain_text(value)

    address = value.get("address") if isinstance(value.get("address"), dict) else value
    parts = [
        value.get("name"),
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
        address.get("city"),
        address.get("stateProvince"),
        address.get("countryName"),
    ]
    normalized = [_plain_text(part) for part in parts]
    return ", ".join(dict.fromkeys(part for part in normalized if part))


def _render_job_fields(fields: list[tuple[str, Any]]) -> str:
    lines = ["JOB POSTING (structured data extracted from the supplied page)"]
    for label, value in fields:
        text = _plain_text(value)
        if text:
            lines.append(f"{label}: {text}")
    return "\n".join(lines)[:MAX_CHARS] if len(lines) > 1 else ""


def _extract_json_ld_job(soup: BeautifulSoup) -> str:
    """Extract the first Schema.org JobPosting payload, when present."""
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            continue

        for job in _job_nodes(payload):
            organization = job.get("hiringOrganization")
            company = organization.get("name") if isinstance(organization, dict) else organization
            result = _render_job_fields(
                [
                    ("Title", job.get("title")),
                    ("Company", company),
                    ("Location", _format_location(job.get("jobLocation"))),
                    ("Employment type", job.get("employmentType")),
                    ("Date posted", job.get("datePosted")),
                    ("Description", job.get("description")),
                    ("Responsibilities", job.get("responsibilities")),
                    ("Qualifications", job.get("qualifications")),
                    ("Experience requirements", job.get("experienceRequirements")),
                    ("Education requirements", job.get("educationRequirements")),
                    ("Skills", job.get("skills")),
                ]
            )
            if result:
                return result
    return ""


def _decode_json_parse_argument(script_text: str, marker: str) -> Any:
    """Decode ``marker = JSON.parse(<JSON string>)`` without executing JS."""
    marker_at = script_text.find(marker)
    parse_at = script_text.find("JSON.parse(", marker_at)
    if marker_at < 0 or parse_at < 0:
        return None

    argument = script_text[parse_at + len("JSON.parse(") :].lstrip()
    try:
        serialized, _ = json.JSONDecoder().raw_decode(argument)
        return json.loads(serialized) if isinstance(serialized, str) else None
    except (TypeError, ValueError):
        return None


def _extract_apple_hydration_job(soup: BeautifulSoup) -> str:
    """Extract job fields from Apple's server-rendered router payload."""
    marker = "window.__staticRouterHydrationData"
    for script in soup.find_all("script"):
        script_text = script.string or script.get_text() or ""
        if marker not in script_text:
            continue

        payload = _decode_json_parse_argument(script_text, marker)
        try:
            job = payload["loaderData"]["jobDetails"]["jobsData"]
        except (KeyError, TypeError):
            continue
        if not isinstance(job, dict):
            continue

        # Apple's top-level fields are localized for the requested page.
        # Fall back to the first localized posting if that shape changes.
        localized = {}
        localizations = job.get("localizations")
        if isinstance(localizations, dict):
            for locale_data in localizations.values():
                if isinstance(locale_data, dict) and isinstance(locale_data.get("posting"), dict):
                    localized = locale_data["posting"]
                    break

        def field(name: str):
            return job.get(name) or localized.get(name)

        result = _render_job_fields(
            [
                ("Title", field("postingTitle")),
                ("Company", "Apple"),
                ("Role number", field("jobNumber")),
                ("Location", _format_location(job.get("selectedLocation") or job.get("localeLocation"))),
                ("Date posted", field("postingDate")),
                ("Summary", field("jobSummary")),
                ("Description", field("description")),
                ("Responsibilities", field("responsibilities")),
                ("Minimum qualifications", field("minimumQualifications")),
                ("Preferred qualifications", field("preferredQualifications")),
                ("Education and experience", field("educationAndExperience")),
                ("Additional requirements", field("additionalRequirements")),
            ]
        )
        if result:
            return result
    return ""


def _page_metadata(soup: BeautifulSoup) -> tuple[str, str]:
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    for attrs in (
        {"name": re.compile(r"^description$", re.I)},
        {"property": re.compile(r"^og:description$", re.I)},
    ):
        meta = soup.find("meta", attrs=attrs)
        if meta and meta.get("content"):
            description = _plain_text(meta["content"])
            break
    return title, description


def _looks_like_job_page(url: str, title: str, description: str) -> bool:
    parsed = urlsplit(url)
    url_text = f"{parsed.hostname or ''}{parsed.path}".lower()
    url_signal = bool(
        re.search(r"(^|[./_-])(jobs?|careers?|positions?|openings?|vacancies?)([./_-]|$)", url_text)
    )
    metadata = f"{title} {description}".lower()
    title_signal = "job" in title.lower() or "career" in title.lower()
    description_signal = bool(
        re.search(r"\b(apply|job|role|position|career|vacancy)\b", description.lower())
    )
    return (url_signal and (title_signal or description_signal)) or (
        title_signal and description_signal and bool(metadata.strip())
    )


def _contains_job_details(text: str) -> bool:
    lowered = text.lower()
    headings = (
        "job description",
        "about the role",
        "what you'll do",
        "what you will do",
        "responsibilities",
        "minimum qualifications",
        "preferred qualifications",
        "requirements",
    )
    return len(text) >= 300 and any(heading in lowered for heading in headings)


def _public_http_url(url: str) -> str:
    """Return a normalized public URL or raise ``ValueError``.

    A read-only scraper can still expose local services if it accepts
    localhost or cloud-metadata addresses. Resolve the host before every
    request (and after every redirect) so the tool stays on the public web.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("the URL is empty")

    normalized = url.strip()
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("only http:// and https:// URLs are allowed")
    if not parsed.hostname:
        raise ValueError("the URL has no hostname")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    except (OSError, ValueError) as exc:
        raise ValueError("the hostname could not be resolved") from exc

    for address in addresses:
        raw_ip = address[4][0].split("%", 1)[0]
        if not ipaddress.ip_address(raw_ip).is_global:
            raise ValueError("private, local, and reserved network addresses are blocked")

    return normalized


def fetch_webpage(url: str) -> str:
    """Fetch a public webpage and return bounded job or visible text."""
    try:
        current_url = _public_http_url(url)
        headers = {"User-Agent": _USER_AGENT}

        for _ in range(MAX_TOOL_REDIRECTS + 1):
            response = requests.get(
                current_url,
                headers=headers,
                timeout=TOOL_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("the webpage returned an empty redirect")
                current_url = _public_http_url(urljoin(current_url, location))
                continue
            break
        else:
            raise ValueError(f"the webpage exceeded {MAX_TOOL_REDIRECTS} redirects")

        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not any(
            allowed in content_type for allowed in ("text/html", "text/plain", "application/xhtml+xml")
        ):
            raise ValueError(f"unsupported content type: {content_type.split(';', 1)[0]}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Job boards commonly keep the useful content in structured script
        # payloads. Extract those data-only formats before removing scripts;
        # no JavaScript is executed.
        structured_job = _extract_json_ld_job(soup) or _extract_apple_hydration_job(soup)
        if structured_job:
            return structured_job

        title, description = _page_metadata(soup)
        is_job_page = _looks_like_job_page(current_url, title, description)
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if not text:
            if is_job_page:
                return (
                    f"{_JOB_PAGE_WARNING_PREFIX}, but its job description "
                    "could not be extracted."
                )
            raise ValueError("the webpage contained no readable text")

        if is_job_page and not _contains_job_details(text):
            details = [item for item in (title, description) if item]
            metadata = " | ".join(details)
            return (
                f"{_JOB_PAGE_WARNING_PREFIX}, but its job description "
                f"could not be extracted. Page metadata: {metadata}"
            )[:MAX_CHARS]

        if is_job_page:
            metadata = "\n".join(
                line
                for line in (f"Title: {title}" if title else "", f"Description: {description}" if description else "")
                if line
            )
            return f"JOB POSTING PAGE\n{metadata}\nPage text: {text}"[:MAX_CHARS]

        return text[:MAX_CHARS]
    except Exception as exc:
        return f"Tool Error: Could not fetch the webpage. Details: {exc}"


def search_company_culture(company_name: str) -> str:
    """Return bounded public search snippets about a company's culture."""
    try:
        if not isinstance(company_name, str) or not company_name.strip():
            raise ValueError("the company name is empty")

        company = " ".join(company_name.split())
        if len(company) > 100:
            raise ValueError("the company name is too long")

        response = requests.get(
            _SEARCH_URL,
            params={
                "q": (
                    f'"{company}" engineering culture careers values '
                    "software engineering"
                )
            },
            # The lightweight endpoint rejects some full browser headers
            # with a challenge page but accepts this deliberately minimal UA.
            headers={"User-Agent": _SEARCH_USER_AGENT},
            timeout=TOOL_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # DuckDuckGo Lite places each title in one table row and its
        # snippet in the immediately following row.
        for link in soup.select("a.result-link"):
            row = link.find_parent("tr")
            snippet_row = row.find_next_sibling("tr") if row else None
            title = link.get_text(" ", strip=True)
            summary = snippet_row.get_text(" ", strip=True) if snippet_row else ""
            results.append(f"- {title}: {summary}".strip())
            if len(results) == 5:
                break

        # Fallback for the richer HTML endpoint's historical markup.
        for result in soup.select(".result"):
            if len(results) == 5:
                break
            link = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if not link and not snippet:
                continue
            title = link.get_text(" ", strip=True) if link else "Untitled result"
            summary = snippet.get_text(" ", strip=True) if snippet else ""
            results.append(f"- {title}: {summary}".strip())

        if not results:
            raise ValueError("the search returned no readable results")

        return (f"Public search results for {company}:\n" + "\n".join(results))[:MAX_CHARS]
    except Exception as exc:
        return f"Tool Error: Could not search for company culture. Details: {exc}"


TOOL_HANDLERS = {
    "fetch_webpage": fetch_webpage,
    "search_company_culture": search_company_culture,
}
