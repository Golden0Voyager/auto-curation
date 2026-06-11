"""Tests for scraper.py _scrape_html complex paths and edge cases."""

import json
import tempfile
from unittest.mock import MagicMock, patch

from src.scraper import MAX_HTML_SIZE, ExhibitionScraper
from src.sites.base import ParserStrategy


def _make_parser(**kwargs):
    """Helper to create a mocked parser with sensible defaults."""
    p = MagicMock()
    p.source = kwargs.get("source", "Test")
    p.city = kwargs.get("city", "City")
    p.parser_key = kwargs.get("parser_key", "test")
    p.institution_type = kwargs.get("institution_type", "museum")
    p.strategy = kwargs.get("strategy", ParserStrategy.HTML_LLM)
    p.link_patterns = kwargs.get("link_patterns", [])
    p.get_exhibition_urls.return_value = kwargs.get("urls", ["http://test.ex/show"])
    p.parse_exhibition_page = kwargs.get("parse_exhibition_page")
    p.clean_html.return_value = kwargs.get(
        "clean_text",
        "Clean exhibition text with enough content for LLM parsing. "
        "More than 100 characters of content to pass the minimum threshold. "
        "This is the description of the exhibition and its contents.",
    )
    p.request_timeout = kwargs.get("request_timeout", 60.0)
    p.use_curl_cffi = kwargs.get("use_curl_cffi", False)
    p._url_tags = kwargs.get("url_tags", {})
    return p


class TestScrapeHtmlBasic:
    def test_standard_flow_native_parser(self):
        """When parser has parse_exhibition_page, use it and skip LLM."""
        mock_parser = _make_parser(
            parse_exhibition_page=MagicMock(
                return_value={"title": "Native Parsed", "city": "TestCity", "artworks": []}
            )
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["saved"] == 1
            scraper.close()

    def test_standard_flow_llm_pipeline(self):
        """When no native parser, fall through to LLM pipeline."""
        mock_parser = _make_parser()
        mock_parser.parse_exhibition_page = None

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            # Mock the HTTP response and LLM parser
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Content</p></body></html>"
            scraper.client.get = MagicMock(return_value=mock_response)
            # Mock the LLM parser result
            scraper.parser.parse_exhibition_text = MagicMock(
                return_value={"title": "LLM Parsed", "city": "TestCity", "artworks": []}
            )
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()


class TestScrapeHtmlRetry:
    def test_retry_on_429(self):
        """HTTP 429 should trigger retry logic."""
        mock_parser = _make_parser()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)

            # Mock with 429 first, then success
            fail_response = MagicMock()
            fail_response.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
                "429 Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
            )
            success_response = MagicMock()
            success_response.text = "<html><body><p>Content</p></body></html>"

            # Use side_effect to simulate retry
            scraper.client.get = MagicMock()
            scraper.client.get.side_effect = [fail_response, fail_response, success_response]
            scraper.parser.parse_exhibition_text = MagicMock(
                return_value={"title": "Retry OK", "city": "TestCity", "artworks": []}
            )

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()

    def test_503_retryable(self):
        """HTTP 503 should trigger retry."""
        from httpx import HTTPStatusError

        mock_parser = _make_parser()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            fail_resp = MagicMock()
            fail_resp.status_code = 503
            fail_resp.raise_for_status.side_effect = HTTPStatusError(
                "503", request=MagicMock(), response=fail_resp
            )
            success_resp = MagicMock()
            success_resp.text = "<html><body>Content</body></html>"

            scraper.client.get = MagicMock()
            scraper.client.get.side_effect = [fail_resp, success_resp]
            scraper.parser.parse_exhibition_text = MagicMock(
                return_value={"title": "503 Retry OK", "artworks": []}
            )

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()

    def test_403_triggers_scrapling_fallback(self):
        """HTTP 403 should trigger Scrapling fallback."""
        from httpx import HTTPStatusError

        mock_parser = _make_parser()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            fail_resp = MagicMock()
            fail_resp.status_code = 403
            fail_resp.raise_for_status.side_effect = HTTPStatusError(
                "403", request=MagicMock(), response=fail_resp
            )

            scraper.client.get = MagicMock(return_value=fail_resp)

            # Mock Scrapling fallback via sys.modules
            mock_scrapling = MagicMock()
            mock_fetcher_instance = MagicMock()
            mock_scrapling_resp = MagicMock()
            mock_scrapling_resp.html_content = "<html><body>Scrapling content</body></html>"
            mock_fetcher_instance.get.return_value = mock_scrapling_resp
            mock_scrapling.Fetcher.return_value = mock_fetcher_instance

            with patch.dict("sys.modules", {"scrapling": mock_scrapling}):
                scraper.parser.parse_exhibition_text = MagicMock(
                    return_value={"title": "Scrapling OK", "artworks": []}
                )

                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["parsed"] == 1
            scraper.close()


class TestScrapeHtmlEdge:
    def test_curl_cffi_path(self):
        """When parser has use_curl_cffi=True, use curl_cffi library."""
        mock_parser = _make_parser(use_curl_cffi=True)

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)

            mock_response = MagicMock()
            mock_response.text = "<html><body><p>curl content</p></body></html>"

            mock_curl = MagicMock()
            mock_curl.get.return_value = mock_response

            with patch.dict(
                "sys.modules", {"curl_cffi": mock_curl, "curl_cffi.requests": mock_curl}
            ):
                scraper.parser.parse_exhibition_text = MagicMock(
                    return_value={"title": "Curl OK", "artworks": []}
                )
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["parsed"] == 1
            scraper.close()

    def test_html_too_large_skipped(self):
        """HTML exceeding MAX_HTML_SIZE should be skipped."""
        mock_parser = _make_parser()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            mock_response = MagicMock()
            mock_response.text = "X" * (MAX_HTML_SIZE + 1)
            scraper.client.get = MagicMock(return_value=mock_response)

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["failed"] == 1
            scraper.close()

    def test_clean_text_too_short_skipped(self):
        """Clean text under 100 chars should be skipped."""
        mock_parser = _make_parser(clean_text="Short.")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Short</p></body></html>"
            scraper.client.get = MagicMock(return_value=mock_response)

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["failed"] == 1
            scraper.close()

    def test_llm_parsing_fails(self):
        """When LLM returns None, the exhibition should be marked as failed."""
        mock_parser = _make_parser()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Content</p></body></html>"
            scraper.client.get = MagicMock(return_value=mock_response)
            scraper.parser.parse_exhibition_text = MagicMock(return_value=None)

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["failed"] == 1
            scraper.close()

    def test_url_already_exists_skipped(self):
        """When URL already exists in DB (not force, not dry_run), skip it."""
        mock_parser = _make_parser(urls=["http://test.ex/existing"])

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            # Pre-insert the URL
            scraper.db.insert_exhibition(
                {
                    "source": "Test",
                    "title": "Existing",
                    "url": "http://test.ex/existing",
                }
            )
            result = scraper._scrape_html(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            scraper.close()

    def test_force_mode_removes_existing(self):
        """Force mode should delete and reprocess."""
        mock_parser = _make_parser(urls=["http://test.ex/existing"])
        mock_parser.parse_exhibition_page = None

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition(
                {
                    "source": "Test",
                    "title": "Existing",
                    "url": "http://test.ex/existing",
                }
            )
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Content</p></body></html>"
            scraper.client.get = MagicMock(return_value=mock_response)
            scraper.parser.parse_exhibition_text = MagicMock(
                return_value={"title": "Force OK", "artworks": []}
            )

            result = scraper._scrape_html(mock_parser, force=True, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()

    def test_limit_stops_early(self):
        """When limit is set, stop after processing that many URLs."""
        mock_parser = _make_parser(
            urls=["http://test.ex/1", "http://test.ex/2", "http://test.ex/3"]
        )
        mock_parser.parse_exhibition_page = MagicMock(
            return_value={"title": "Show", "city": "City", "artworks": []}
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, limit=2, dry_run=True)
            assert result["saved"] == 2
            scraper.close()

    def test_native_parser_returns_none_falls_to_llm(self):
        """Native parser returning None should trigger LLM fallback."""
        mock_parser = _make_parser(parse_exhibition_page=MagicMock(return_value=None))

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Content</p></body></html>"
            scraper.client.get = MagicMock(return_value=mock_response)
            scraper.parser.parse_exhibition_text = MagicMock(
                return_value={"title": "Fallback OK", "artworks": []}
            )

            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()


class TestScrapeHtmlTags:
    def test_parser_url_tags_attached(self):
        """When parser has _url_tags, they should be attached to parsed_data."""
        mock_parser = _make_parser(
            urls=["http://test.ex/show"],
            url_tags={"http://test.ex/show": json.dumps(["Exhibitions"])},
        )
        mock_parser.parse_exhibition_page = MagicMock(
            return_value={"title": "Tagged Show", "city": "City", "artworks": []}
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            scraper.close()


class TestScrapeHtmlError:
    def test_url_processing_error(self):
        """Error during URL processing should be caught and counted."""
        mock_parser = _make_parser(
            parse_exhibition_page=MagicMock(side_effect=Exception("Processing error"))
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["failed"] == 1
            scraper.close()
