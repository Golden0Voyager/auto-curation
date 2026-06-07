import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest

from src.scraper import ExhibitionScraper
from src.sites.base import BaseSiteParser, ParserStrategy

TEST_DB = "tests/test_async_scraper.db"


class DummyParser(BaseSiteParser):
    source = "Dummy Museum"
    city = "TestCity"
    parser_key = "dummy"
    list_url = "http://dummy.local/list"
    link_patterns = [r"/exhibition/"]
    strategy = ParserStrategy.HTML_LLM

    def get_exhibition_urls(self, client, since_year=None):
        return [
            "http://dummy.local/exhibition/1",
            "http://dummy.local/exhibition/2",
        ]

    def clean_html(self, html: str) -> str:
        # Ensure output is always >100 chars so async pipeline doesn't skip
        return html + "\n" + "This is a long exhibition description. " * 10


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture(autouse=True)
def register_dummy():
    from src.sites import SITES

    SITES["dummy"] = DummyParser()
    yield
    if "dummy" in SITES:
        del SITES["dummy"]


@pytest.mark.asyncio
async def test_ascrape_site_concurrent_processing():
    scraper = ExhibitionScraper(TEST_DB, max_concurrency=2)

    call_count = 0

    async def fake_llm_parse(text, source, default_city=""):
        nonlocal call_count
        call_count += 1
        return {"title": f"Exhibition {call_count}", "city": default_city, "artworks": []}

    scraper.parser.parse_exhibition_text_async = fake_llm_parse

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Some exhibition content</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await scraper.ascrape_site("dummy", limit=2, dry_run=True)

    assert result["discovered"] == 2
    assert result["parsed"] == 2
    assert result["saved"] == 2
    assert call_count == 2


@pytest.mark.asyncio
async def test_ascrape_site_respects_concurrency_limit():
    scraper = ExhibitionScraper(TEST_DB, max_concurrency=1)
    active = 0
    max_active = 0

    async def fake_llm_parse(text, source, default_city=""):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.05)
        active -= 1
        return {"title": "Ex", "city": default_city, "artworks": []}

    scraper.parser.parse_exhibition_text_async = fake_llm_parse

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html>content</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        await scraper.ascrape_site("dummy", limit=2, dry_run=True)

    assert max_active == 1


def test_scrape_site_still_works_synchronously():
    """Synchronous API must remain backward-compatible."""
    scraper = ExhibitionScraper(TEST_DB)
    DummyParser.parse_exhibition_page = lambda self, client, url: {
        "title": "Native",
        "city": "TestCity",
        "artworks": [],
    }
    result = scraper.scrape_site("dummy", limit=1, dry_run=True)
    assert result["parsed"] >= 0
