"""Tests for src/sites/moma.py — MoMA CSV parser."""

import io
from unittest.mock import MagicMock, patch

from src.sites.base import ParserStrategy
from src.sites.moma import (
    MOMA_EXHIBITIONS_CSV_URL,
    MoMAParser,
)

SAMPLE_CSV = """ExhibitionID,ExhibitionTitle,ExhibitionBeginDate,ExhibitionEndDate,ExhibitionURL,DisplayName,ExhibitionRole,Nationality,ConstituentBeginDate,ConstituentEndDate
1,Picasso in Paris,1/15/2024,4/30/2024,,Pablo Picasso,Artist,Spanish,1881,1973
1,Picasso in Paris,1/15/2024,4/30/2024,,Marie Curator,Curator,French,,
2,Modern Masters,6/1/2024,9/30/2024,https://moma.org/ex/2,Andy Warhol,Artist,American,1928,1987
2,Modern Masters,6/1/2024,9/30/2024,https://moma.org/ex/2,John Director,Director,American,,
"""


class TestMoMAParser:
    def test_parser_attributes(self):
        p = MoMAParser()
        assert p.source == "MoMA"
        assert p.city == "New York"
        assert p.parser_key == "moma"
        assert p.strategy == ParserStrategy.CSV_REMOTE

    def test_get_list_urls(self):
        p = MoMAParser()
        urls = p.get_list_urls()
        assert len(urls) == 1
        assert urls[0] == MOMA_EXHIBITIONS_CSV_URL

    def test_get_exhibition_urls_empty(self):
        p = MoMAParser()
        assert p.get_exhibition_urls(None) == []

    def test_get_csv_exhibitions_parses_csv(self):
        """Parse CSV string and verify correct structure."""
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(SAMPLE_CSV)
            mock_open.return_value = mock_file

            p = MoMAParser()
            result = p.get_csv_exhibitions()

            # Should parse 2 exhibitions
            assert len(result) == 2

            # First exhibition: Picasso
            ex1 = result[0]
            assert ex1["title"] == "Picasso in Paris"
            assert ex1["start_date"] == "1/15/2024"
            assert "Picasso" in ex1["artworks"][0]["artist_name"]

            # Second exhibition: Modern Masters
            ex2 = result[1]
            assert ex2["title"] == "Modern Masters"
            assert ex2["url"] == "https://moma.org/ex/2"

    def test_get_csv_exhibitions_since_year_filter(self):
        """Test year filtering."""
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(SAMPLE_CSV)
            mock_open.return_value = mock_file

            p = MoMAParser()
            # Both exhibitions are in 2024, so filtering by 2025 should return 0
            # Actually our sample data is 2024, so since_year=2025 should filter them out
            # But the year is parsed from "1/15/2024" -> 2024, and 2024 < 2025, so they're filtered
            result = p.get_csv_exhibitions(since_year=2025)
            assert len(result) == 0

    def test_get_csv_exhibitions_missing_id_skipped(self):
        """Rows without ExhibitionID should be skipped."""
        bad_csv = "ExhibitionID,ExhibitionTitle\n,\n,Test"
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(bad_csv)
            mock_open.return_value = mock_file

            p = MoMAParser()
            result = p.get_csv_exhibitions()
            assert len(result) == 0

    def test_get_csv_exhibitions_url_normalization(self):
        """URL without http prefix should get https://www. prepended."""
        csv_with_url = "ExhibitionID,ExhibitionTitle,ExhibitionURL,DisplayName\n1,Test Show,moma.org/ex/1,Artist A"
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(csv_with_url)
            mock_open.return_value = mock_file

            p = MoMAParser()
            result = p.get_csv_exhibitions()
            assert result[0]["url"] == "https://www.moma.org/ex/1"

    def test_get_csv_exhibitions_no_local_file_downloads(self):
        """When local file doesn't exist, should attempt to download from GitHub."""
        with (
            patch("os.path.exists", return_value=False),
            patch("src.sites.moma.httpx.Client") as mock_client_class,
        ):
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.content = SAMPLE_CSV.encode("latin-1")
            mock_instance.get.return_value = mock_response

            with patch("builtins.open") as mock_open:
                mock_file = MagicMock()
                mock_file.__enter__.return_value = io.StringIO("")
                mock_open.return_value = mock_file

                with patch("os.makedirs"):
                    p = MoMAParser()
                    result = p.get_csv_exhibitions()
                    assert len(result) > 0

    def test_get_csv_exhibitions_download_failure(self):
        """When download fails, return empty list."""
        with (
            patch("os.path.exists", return_value=False),
            patch("src.sites.moma.httpx.Client") as mock_client_class,
        ):
            mock_instance = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_instance
            mock_instance.get.side_effect = Exception("Download failed")

            p = MoMAParser()
            result = p.get_csv_exhibitions()
            assert result == []

    def test_clean_html_passthrough(self):
        p = MoMAParser()
        assert p.clean_html("test") == "test"

    def test_get_csv_exhibitions_invalid_begin_date(self):
        csv_data = "ExhibitionID,ExhibitionTitle,ExhibitionBeginDate,DisplayName\n1,Test Show,abcd/ef/gh,Artist A"
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(csv_data)
            mock_open.return_value = mock_file

            p = MoMAParser()
            result = p.get_csv_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "Test Show"

    def test_get_csv_exhibitions_filtered_and_missing_name(self):
        csv_data = (
            "ExhibitionID,ExhibitionTitle,ExhibitionBeginDate,DisplayName,ExhibitionRole\n"
            "1,Old Show,2010,Artist A,Artist\n"
            "1,Old Show,2010,Artist B,Artist\n"
            "2,New Show,2025,,Artist\n"
        )
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = io.StringIO(csv_data)
            mock_open.return_value = mock_file

            p = MoMAParser()
            result = p.get_csv_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "New Show"
            assert len(result[0]["artworks"]) == 0

