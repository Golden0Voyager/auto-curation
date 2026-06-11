"""Tests for src/sites/nga.py — NGA CSV artwork parser edge cases."""

import io
from unittest.mock import MagicMock, patch

from src.sites.nga import (
    NGA_CONSTITUENTS_PATH,
    NGA_OBJECTS_CONSTITUENTS_PATH,
    NGA_OBJECTS_PATH,
    NGAParser,
)

SAMPLE_OBJECTS = (
    "objectid,title,beginyear,displaydate,medium,dimensions,classification\n"
    "1,Mona Lisa,1503,1503-1506,Oil on panel,77x53,Painting\n"
    "2,The Thinker,1902,1902,Bronze,180x98,Sculpture\n"
)

SAMPLE_CONSTITUENTS = (
    "constituentid,displayname,nationality,beginyear,endyear\n"
    "10,Leonardo da Vinci,Italian,1452,1519\n"
    "20,Auguste Rodin,French,1840,1917\n"
)

SAMPLE_LINKS = "objectid,constituentid,role\n1,10,artist\n2,20,artist\n"


class TestNGAParser:
    def test_parser_attributes(self):
        p = NGAParser()
        assert p.source == "National Gallery of Art"
        assert p.city == "Washington D.C."
        assert p.parser_key == "nga"
        assert p.strategy.value == "artwork_only"

    def test_get_list_urls(self):
        p = NGAParser()
        urls = p.get_list_urls()
        assert len(urls) == 1
        assert "objects.csv" in urls[0]

    def test_get_exhibition_urls_empty(self):
        p = NGAParser()
        assert p.get_exhibition_urls(None) == []

    def test_no_local_files_returns_empty(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=False):
            result = p.get_csv_artworks()
            assert result == []

    def test_parse_artworks_full_flow(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: SAMPLE_OBJECTS,
                        NGA_CONSTITUENTS_PATH: SAMPLE_CONSTITUENTS,
                        NGA_OBJECTS_CONSTITUENTS_PATH: SAMPLE_LINKS,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks()
            assert len(result) == 2
            # Check first artwork joined with constituent data
            assert result[0]["artist_name"] == "Leonardo da Vinci"
            assert result[0]["work_title"] == "Mona Lisa"
            assert "Italian" in result[0]["caption"]

    def test_since_year_filter(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: SAMPLE_OBJECTS,
                        NGA_CONSTITUENTS_PATH: SAMPLE_CONSTITUENTS,
                        NGA_OBJECTS_CONSTITUENTS_PATH: SAMPLE_LINKS,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            # Only artworks with beginyear >= 1900
            result = p.get_csv_artworks(since_year=1900)
            assert len(result) == 1
            assert result[0]["work_title"] == "The Thinker"

    def test_limit(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: SAMPLE_OBJECTS,
                        NGA_CONSTITUENTS_PATH: SAMPLE_CONSTITUENTS,
                        NGA_OBJECTS_CONSTITUENTS_PATH: SAMPLE_LINKS,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks(limit=1)
            assert len(result) == 1

    def test_classification_filter(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: SAMPLE_OBJECTS,
                        NGA_CONSTITUENTS_PATH: SAMPLE_CONSTITUENTS,
                        NGA_OBJECTS_CONSTITUENTS_PATH: SAMPLE_LINKS,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks(classification="Sculpture")
            assert len(result) == 1
            assert result[0]["work_title"] == "The Thinker"

    def test_empty_title_skipped(self):
        objects = "objectid,title\n1,\n2,Valid Work\n"
        constituents = "constituentid,displayname\n10,Artist A\n"
        links = "objectid,constituentid,role\n1,10,artist\n2,10,artist\n"

        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: objects,
                        NGA_CONSTITUENTS_PATH: constituents,
                        NGA_OBJECTS_CONSTITUENTS_PATH: links,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks()
            assert len(result) == 1
            assert result[0]["work_title"] == "Valid Work"

    def test_no_artist_fallback_to_unknown(self):
        """When no matching constituent, fallback to 'Unknown'."""
        objects = "objectid,title\n1,Orphan Artwork\n"
        constituents = "constituentid,displayname\n10,Artist A\n"
        # No link for object 1
        links = "objectid,constituentid,role\n"

        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:

            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: objects,
                        NGA_CONSTITUENTS_PATH: constituents,
                        NGA_OBJECTS_CONSTITUENTS_PATH: links,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks()
            assert len(result) == 1
            assert result[0]["artist_name"] == "Unknown"

    def test_clean_html_passthrough(self):
        p = NGAParser()
        assert p.clean_html("<html/>") == "<html/>"

    def test_ensure_local_files_false(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=False):
            assert p._ensure_local_files() is False

    def test_invalid_begin_year_value_error(self):
        objects = "objectid,title,beginyear,classification\n1,Mona Lisa,abcd,Painting\n"
        constituents = "constituentid,displayname\n10,Leonardo da Vinci\n"
        links = "objectid,constituentid,role\n1,10,artist\n"

        p = NGAParser()
        with patch("os.path.exists", return_value=True), patch("builtins.open") as mock_open:
            def side_effect(path, *args, **kwargs):
                file = MagicMock()
                file.__enter__.return_value = io.StringIO(
                    {
                        NGA_OBJECTS_PATH: objects,
                        NGA_CONSTITUENTS_PATH: constituents,
                        NGA_OBJECTS_CONSTITUENTS_PATH: links,
                    }[path]
                )
                return file

            mock_open.side_effect = side_effect

            result = p.get_csv_artworks(since_year=1500)
            assert len(result) == 1
            assert result[0]["work_title"] == "Mona Lisa"

