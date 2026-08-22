"""Offline tests for read-only network tools and schemas."""

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tool_schemas import AGENT_TOOLS
from tools import fetch_webpage, search_company_culture


class ToolTests(unittest.TestCase):
    def test_schemas_are_strict_and_closed(self):
        self.assertEqual({tool["name"] for tool in AGENT_TOOLS}, {
            "fetch_webpage",
            "search_company_culture",
        })
        for tool in AGENT_TOOLS:
            self.assertTrue(tool["strict"])
            self.assertFalse(tool["parameters"]["additionalProperties"])

    def test_private_url_returns_text_error_without_request(self):
        with patch("tools.requests.get") as get:
            result = fetch_webpage("http://127.0.0.1/admin")
        self.assertTrue(result.startswith("Tool Error:"))
        get.assert_not_called()

    @patch(
        "tools.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    @patch("tools.requests.get")
    def test_fetch_returns_visible_text_without_scripts(self, get, _dns):
        reply = Mock()
        reply.is_redirect = False
        reply.is_permanent_redirect = False
        reply.headers = {"Content-Type": "text/html; charset=utf-8"}
        reply.text = "<html><script>ignore()</script><body><h1>Data Engineer</h1></body></html>"
        reply.raise_for_status.return_value = None
        get.return_value = reply

        result = fetch_webpage("https://example.com/job")
        self.assertEqual(result, "Data Engineer")

    @patch(
        "tools.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    @patch("tools.requests.get")
    def test_fetch_extracts_schema_org_job_posting(self, get, _dns):
        payload = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "JobPosting",
                    "title": "Data Engineer",
                    "hiringOrganization": {"name": "Example Co"},
                    "jobLocation": {
                        "address": {
                            "addressLocality": "Chennai",
                            "addressCountry": "India",
                        }
                    },
                    "description": "<p>Build reliable <strong>pipelines</strong>.</p>",
                    "qualifications": "Python and SQL",
                }
            ],
        }
        reply = Mock()
        reply.is_redirect = False
        reply.is_permanent_redirect = False
        reply.headers = {"Content-Type": "text/html"}
        reply.text = (
            '<html><script type="application/ld+json">'
            f"{json.dumps(payload)}"
            "</script><body>Sign in to continue</body></html>"
        )
        reply.raise_for_status.return_value = None
        get.return_value = reply

        result = fetch_webpage("https://example.com/jobs/data-engineer")

        self.assertTrue(result.startswith("JOB POSTING"))
        self.assertIn("Title: Data Engineer", result)
        self.assertIn("Company: Example Co", result)
        self.assertIn("Location: Chennai, India", result)
        self.assertIn("Description: Build reliable pipelines .", result)
        self.assertNotIn("Sign in to continue", result)

    @patch(
        "tools.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("17.0.0.1", 443))],
    )
    @patch("tools.requests.get")
    def test_fetch_extracts_apple_router_hydration_job(self, get, _dns):
        payload = {
            "loaderData": {
                "jobDetails": {
                    "jobsData": {
                        "jobNumber": "200657330-3543",
                        "postingTitle": "Data Engineer",
                        "jobSummary": "Build Apple's next generation systems.",
                        "description": "Develop and maintain data software.",
                        "responsibilities": "Design scalable data pipelines.",
                        "minimumQualifications": "Python and SQL experience.",
                        "preferredQualifications": "Database design experience.",
                        "selectedLocation": {
                            "city": "Austin",
                            "stateProvince": "Texas",
                            "countryName": "United States",
                        },
                    }
                }
            }
        }
        serialized_payload = json.dumps(payload)
        hydration_script = (
            "window.__staticRouterHydrationData = JSON.parse("
            f"{json.dumps(serialized_payload)});"
        )
        reply = Mock()
        reply.is_redirect = False
        reply.is_permanent_redirect = False
        reply.headers = {"Content-Type": "text/html"}
        reply.text = (
            "<html><head><title>Data Engineer - Jobs - Careers at Apple</title></head>"
            f"<body><script>{hydration_script}</script>Apple footer</body></html>"
        )
        reply.raise_for_status.return_value = None
        get.return_value = reply

        result = fetch_webpage(
            "https://jobs.apple.com/en-us/details/200657330-3543/data-engineer"
        )

        self.assertTrue(result.startswith("JOB POSTING"))
        self.assertIn("Title: Data Engineer", result)
        self.assertIn("Company: Apple", result)
        self.assertIn("Role number: 200657330-3543", result)
        self.assertIn("Location: Austin, Texas, United States", result)
        self.assertIn("Responsibilities: Design scalable data pipelines.", result)
        self.assertIn("Minimum qualifications: Python and SQL experience.", result)
        self.assertNotIn("Apple footer", result)

    @patch(
        "tools.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    @patch("tools.requests.get")
    def test_job_metadata_without_description_returns_distinct_warning(self, get, _dns):
        reply = Mock()
        reply.is_redirect = False
        reply.is_permanent_redirect = False
        reply.headers = {"Content-Type": "text/html"}
        reply.text = (
            "<html><head><title>Data Engineer - Careers</title>"
            '<meta name="description" content="Apply for this Data Engineer job.">'
            "</head><body>Enable JavaScript to continue.</body></html>"
        )
        reply.raise_for_status.return_value = None
        get.return_value = reply

        result = fetch_webpage("https://example.com/jobs/data-engineer")

        self.assertTrue(result.startswith("Tool Warning: Job page detected"))
        self.assertIn("Data Engineer - Careers", result)
        self.assertNotIn("doesn't look like a job board", result)

    @patch("tools.requests.get")
    def test_company_search_returns_bounded_snippets(self, get):
        reply = Mock()
        reply.text = (
            '<div class="result"><a class="result__a">Careers</a>'
            '<span class="result__snippet">Ownership and impact.</span></div>'
        )
        reply.raise_for_status.return_value = None
        get.return_value = reply

        result = search_company_culture("Example Co")
        self.assertIn("Public search results for Example Co", result)
        self.assertIn("Ownership and impact", result)

    def test_empty_company_returns_text_error(self):
        self.assertTrue(search_company_culture(" ").startswith("Tool Error:"))


if __name__ == "__main__":
    unittest.main()
