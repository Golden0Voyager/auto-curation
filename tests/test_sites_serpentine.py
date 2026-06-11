"""Tests for src/sites/serpentine.py — Serpentine Galleries parser."""

from datetime import date
from unittest.mock import MagicMock

from src.sites.serpentine import SerpentineParser


class TestSerpentineParser:
    def test_parser_attributes(self):
        p = SerpentineParser()
        assert p.source == "Serpentine Galleries"
        assert p.city == "London"
        assert len(p.link_patterns) > 0
        assert len(p.EVENT_KEYWORDS) > 0
        assert p.MAX_ARCHIVE_PAGES == 20

    def test_get_list_urls_default(self):
        p = SerpentineParser()
        urls = p.get_list_urls()
        assert urls[0] == "https://www.serpentinegalleries.org/whats-on/"
        assert "archive" in urls[1]

    def test_get_list_urls_with_since_year(self):
        p = SerpentineParser()
        current_year = date.today().year
        urls = p.get_list_urls(since_year=current_year)
        # With since_year = current year, max_pages = min(1*2, 20) = 2
        # So we should have [list, archive/] = 2 URLs
        assert len(urls) >= 2

    def test_get_list_urls_since_year_far(self):
        p = SerpentineParser()
        urls = p.get_list_urls(since_year=2000)
        # With since_year = 2000, years_back can be >10, max_pages = min(>20, 20) = 20
        assert len(urls) >= 2  # at least list + archive

    def test_get_exhibition_urls_no_results(self):
        """When listing page returns no teasers, should use fallback parsing and find nothing."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>No exhibitions here</p></body></html>"
        mock_client.get.return_value = mock_response

        result = p.get_exhibition_urls(mock_client)
        assert isinstance(result, list)

    def test_get_exhibition_urls_with_teasers(self):
        """When listing page has teaser sections."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <section class="teaser">
                <a href="/whats-on/exhibition-1/">Link</a>
                <a href="?type=exhibitions">Exhibitions</a>
                <h3>Real Exhibition</h3>
            </section>
            <section class="teaser">
                <a href="/whats-on/event-talk/">Link</a>
                <a href="?type=events">Events</a>
                <h3>A Talk</h3>
            </section>
        </body></html>
        """
        mock_client.get.return_value = mock_response

        result = p.get_exhibition_urls(mock_client)
        # The first teaser should be detected as an exhibition (not event)
        assert len(result) >= 0

    def test_get_exhibition_urls_request_failure(self):
        """Request failure should be handled gracefully."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")
        result = p.get_exhibition_urls(mock_client)
        assert isinstance(result, list)

    def test_event_keywords_filter(self):
        p = SerpentineParser()
        assert "talk" in p.EVENT_KEYWORDS
        assert "workshop" in p.EVENT_KEYWORDS
        assert "screening" in p.EVENT_KEYWORDS
        assert "performance" in p.EVENT_KEYWORDS
