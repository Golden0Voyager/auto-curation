"""Comprehensive tests for src/database.py — ExhibitionDatabase class."""

import json
import os
import sqlite3

import pytest

from src.database import ExhibitionDatabase

TEST_DB = "tests/test_database.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def _sample_exhibition(url="http://test.com/ex1", title="Test Exhibition"):
    return {
        "source": "Test Museum",
        "title": title,
        "preface": "A test exhibition.",
        "concept": "Testing concept.",
        "curators": ["Alice", "Bob"],
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "location": "Gallery 1",
        "city": "TestCity",
        "url": url,
        "parser_key": "test",
        "institution_type": "museum",
        "artworks": [
            {
                "artist_name": "Artist A",
                "work_title": "Work 1",
                "work_year": "2024",
                "medium": "Oil",
                "dimensions": "100x100",
                "caption": "A's work",
            },
            {"artist_name": "Artist B", "work_title": "Work 2", "caption": "B's work"},
        ],
    }


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_creates_tables(self):
        ExhibitionDatabase(TEST_DB)
        conn = sqlite3.connect(TEST_DB)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {row[0] for row in tables}
        assert "exhibitions" in table_names
        assert "artworks" in table_names
        assert "biennial_series" in table_names
        assert "scraper_runs" in table_names
        conn.close()

    def test_creates_indexes(self):
        _ = ExhibitionDatabase(TEST_DB)
        conn = sqlite3.connect(TEST_DB)
        indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        index_names = {row[0] for row in indexes}
        assert "idx_exhibitions_url" in index_names
        assert "idx_exhibitions_source" in index_names
        assert "idx_artworks_exhibition" in index_names
        conn.close()

    def test_seeds_biennial_series(self):
        db = ExhibitionDatabase(TEST_DB)
        series = db.get_biennial_series()
        assert len(series) >= 13  # 13 biennial series seeded
        names = {s["series_name"] for s in series}
        assert "Venice Biennale" in names
        assert "Documenta" in names


# ---------------------------------------------------------------------------
# insert_exhibition
# ---------------------------------------------------------------------------


class TestInsertExhibition:
    def test_inserts_basic_exhibition(self):
        db = ExhibitionDatabase(TEST_DB)
        ex_id = db.insert_exhibition(_sample_exhibition())
        assert ex_id is not None
        assert isinstance(ex_id, int)

    def test_duplicate_url_returns_existing_id(self):
        db = ExhibitionDatabase(TEST_DB)
        ex_id1 = db.insert_exhibition(_sample_exhibition())
        ex_id2 = db.insert_exhibition(_sample_exhibition())
        assert ex_id1 == ex_id2  # Same ID returned

    def test_different_urls_both_inserted(self):
        db = ExhibitionDatabase(TEST_DB)
        ex1 = _sample_exhibition(url="http://test.com/a")
        ex2 = _sample_exhibition(url="http://test.com/b", title="Second")
        id1 = db.insert_exhibition(ex1)
        id2 = db.insert_exhibition(ex2)
        assert id1 != id2
        assert db.count_exhibitions() == 2

    def test_insert_without_artworks(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["artworks"] = []
        ex_id = db.insert_exhibition(ex)
        assert ex_id is not None

    def test_insert_without_curators(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["curators"] = []
        ex_id = db.insert_exhibition(ex)
        assert ex_id is not None

    def test_insert_with_tags_and_images(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["tags"] = ["modern", "sculpture"]
        ex["images"] = ["http://img.com/1.jpg", "http://img.com/2.jpg"]
        ex_id = db.insert_exhibition(ex)
        assert ex_id is not None

    def test_duplicate_artworks_ignored(self):
        """Duplicate artworks (same artist_name + work_title) are ignored."""
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        # Add duplicate artwork
        ex["artworks"].append({"artist_name": "Artist A", "work_title": "Work 1", "caption": "Dup"})
        ex_id = db.insert_exhibition(ex)
        assert ex_id is not None
        # Only 2 artworks should be stored (duplicates ignored)
        retrieved = db.get_exhibition_by_url(ex["url"])
        assert len(retrieved["artworks"]) == 2


# ---------------------------------------------------------------------------
# get_exhibition_by_url
# ---------------------------------------------------------------------------


class TestGetExhibitionByUrl:
    def test_returns_none_for_missing(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.get_exhibition_by_url("http://nope.com") is None

    def test_retrieves_exhibition_with_artworks(self):
        db = ExhibitionDatabase(TEST_DB)
        original = _sample_exhibition()
        db.insert_exhibition(original)
        retrieved = db.get_exhibition_by_url(original["url"])
        assert retrieved is not None
        assert retrieved["title"] == original["title"]
        assert retrieved["source"] == original["source"]
        assert len(retrieved["artworks"]) == 2
        assert retrieved["artworks"][0]["artist_name"] == "Artist A"

    def test_curators_deserialized(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["curators"] = ["Alice", "Bob"]
        db.insert_exhibition(ex)
        retrieved = db.get_exhibition_by_url(ex["url"])
        assert retrieved["curators"] == ["Alice", "Bob"]

    def test_empty_curators_returns_empty_list(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["curators"] = []
        db.insert_exhibition(ex)
        retrieved = db.get_exhibition_by_url(ex["url"])
        assert retrieved["curators"] == []

    def test_handles_null_curators(self):
        db = ExhibitionDatabase(TEST_DB)
        # Insert exhibition with NULL curators by raw SQL
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO exhibitions (source, title, url) VALUES (?, ?, ?)",
            ("Test", "No Curators", "http://nocu.rate"),
        )
        conn.commit()
        conn.close()
        retrieved = db.get_exhibition_by_url("http://nocu.rate")
        assert retrieved["curators"] == []


# ---------------------------------------------------------------------------
# get_all_exhibitions
# ---------------------------------------------------------------------------


class TestGetAllExhibitions:
    def test_empty_db(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.get_all_exhibitions() == []

    def test_returns_multiple_exhibitions(self):
        db = ExhibitionDatabase(TEST_DB)
        db.insert_exhibition(_sample_exhibition(url="http://a.com", title="A"))
        db.insert_exhibition(_sample_exhibition(url="http://b.com", title="B"))
        all_ex = db.get_all_exhibitions()
        assert len(all_ex) == 2

    def test_pagination(self):
        db = ExhibitionDatabase(TEST_DB)
        for i in range(5):
            db.insert_exhibition(_sample_exhibition(url=f"http://x.com/{i}", title=f"Ex{i}"))
        first_page = db.get_all_exhibitions(limit=2, offset=0)
        assert len(first_page) == 2


# ---------------------------------------------------------------------------
# count methods
# ---------------------------------------------------------------------------


class TestCounts:
    def test_count_exhibitions(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.count_exhibitions() == 0
        db.insert_exhibition(_sample_exhibition())
        assert db.count_exhibitions() == 1

    def test_count_artworks(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.count_artworks() == 0
        db.insert_exhibition(_sample_exhibition())
        assert db.count_artworks() == 2


# ---------------------------------------------------------------------------
# delete_exhibition_by_url
# ---------------------------------------------------------------------------


class TestDelete:
    def test_deletes_by_url(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        db.insert_exhibition(ex)
        assert db.delete_exhibition_by_url(ex["url"]) is True
        assert db.get_exhibition_by_url(ex["url"]) is None

    def test_delete_nonexistent(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.delete_exhibition_by_url("http://ghost.com") is False

    def test_cascade_deletes_artworks(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex_id = db.insert_exhibition(ex)
        db.delete_exhibition_by_url(ex["url"])
        conn = db._get_connection()
        artworks_left = conn.execute(
            "SELECT count(*) FROM artworks WHERE exhibition_id = ?", (ex_id,)
        ).fetchone()[0]
        conn.close()
        assert artworks_left == 0


# ---------------------------------------------------------------------------
# scraper_runs
# ---------------------------------------------------------------------------


class TestScraperRuns:
    def test_start_scraper_run(self):
        db = ExhibitionDatabase(TEST_DB)
        run_id = db.start_scraper_run("test_parser")
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_start_scraper_run_with_type(self):
        db = ExhibitionDatabase(TEST_DB)
        run_id = db.start_scraper_run("test_parser", run_type="partial")
        assert run_id > 0

    def test_finish_scraper_run(self):
        db = ExhibitionDatabase(TEST_DB)
        run_id = db.start_scraper_run("test_parser")
        db.finish_scraper_run(run_id, urls_discovered=10, urls_parsed=5, exhibitions_saved=3)
        run = db.get_last_scraper_run("test_parser")
        assert run is not None
        assert run["urls_discovered"] == 10
        assert run["urls_parsed"] == 5
        assert run["exhibitions_saved"] == 3

    def test_finish_scraper_run_with_error(self):
        db = ExhibitionDatabase(TEST_DB)
        run_id = db.start_scraper_run("test_parser")
        db.finish_scraper_run(run_id, error_message="Something broke")
        run = db.get_last_scraper_run("test_parser")
        assert run["error_message"] == "Something broke"

    def test_get_last_scraper_run_none(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.get_last_scraper_run("nonexistent") is None

    def test_multiple_runs_returns_latest(self):
        db = ExhibitionDatabase(TEST_DB)
        id1 = db.start_scraper_run("multi")
        db.finish_scraper_run(id1, exhibitions_saved=1)
        id2 = db.start_scraper_run("multi")
        db.finish_scraper_run(id2, exhibitions_saved=2)
        latest = db.get_last_scraper_run("multi")
        assert latest["exhibitions_saved"] == 2


# ---------------------------------------------------------------------------
# biennial_series
# ---------------------------------------------------------------------------


class TestBiennialSeries:
    def test_get_biennial_series(self):
        db = ExhibitionDatabase(TEST_DB)
        series = db.get_biennial_series()
        assert len(series) > 0
        assert "series_name" in series[0]
        assert "series_key" in series[0]

    def test_series_contains_expected_data(self):
        db = ExhibitionDatabase(TEST_DB)
        series = db.get_biennial_series()
        # Find Venice Biennale
        venice = [s for s in series if s["series_key"] == "venice_biennale"]
        assert len(venice) == 1
        assert venice[0]["city"] == "Venice"
        assert venice[0]["country"] == "Italy"

    def test_backfill_series_id(self):
        db = ExhibitionDatabase(TEST_DB)
        # Insert an exhibition without series_id
        ex = _sample_exhibition()
        ex["parser_key"] = "venice_biennale"
        ex["url"] = "http://venice.test"
        db.insert_exhibition(ex)
        updated = db.backfill_series_id()
        assert updated >= 1
        # Verify the exhibition now has a series_id
        retrieved = db.get_exhibition_by_url("http://venice.test")
        assert retrieved["series_id"] is not None


# ---------------------------------------------------------------------------
# Insert with various field types
# ---------------------------------------------------------------------------


class TestFieldVariants:
    def test_curators_as_json_string(self):
        """curators provided as a JSON string should be stored as-is."""
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["curators"] = json.dumps(["X", "Y"], ensure_ascii=False)
        db.insert_exhibition(ex)
        retrieved = db.get_exhibition_by_url(ex["url"])
        assert retrieved["curators"] == ["X", "Y"]

    def test_empty_artworks_list(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["artworks"] = []
        db.insert_exhibition(ex)
        retrieved = db.get_exhibition_by_url(ex["url"])
        assert retrieved["artworks"] == []

    def test_null_fields_allowed(self):
        db = ExhibitionDatabase(TEST_DB)
        ex = _sample_exhibition()
        ex["preface"] = None
        ex["concept"] = None
        ex["start_date"] = None
        ex["end_date"] = None
        ex["location"] = None
        ex_id = db.insert_exhibition(ex)
        assert ex_id is not None


# ---------------------------------------------------------------------------
# Edge: raw exception handling
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_insert_exception_returns_none(self):
        """If an exception occurs during insert, None should be returned."""
        db = ExhibitionDatabase(TEST_DB)
        # Provoke an error by corrupting the DB
        conn = db._get_connection()
        conn.execute("DROP TABLE exhibitions")
        conn.commit()
        conn.close()
        result = db.insert_exhibition(_sample_exhibition())
        assert result is None

    def test_get_all_empty_db(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.get_all_exhibitions() == []
