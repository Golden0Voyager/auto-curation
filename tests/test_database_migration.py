"""Tests for database migration paths, error handling, and edge cases."""

import os
import sqlite3

import pytest

from src.database import ExhibitionDatabase

TEST_DB = "tests/test_database_migration.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestMigrationPaths:
    """Test the ALTER TABLE migration paths in _init_db."""

    def test_migration_adds_columns_on_reopen(self):
        """Create DB with old schema, close it, reopen — ALTER TABLE migrations run."""
        # Step 1: Create database with old schema (missing the 'migration columns' like preface_en)
        conn = sqlite3.connect(TEST_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exhibitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                preface TEXT,
                concept TEXT,
                curators TEXT DEFAULT '[]',
                start_date TEXT,
                end_date TEXT,
                location TEXT,
                city TEXT,
                url TEXT UNIQUE NOT NULL,
                parser_key TEXT,
                institution_type TEXT DEFAULT 'museum',
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exhibition_id INTEGER NOT NULL,
                artist_name TEXT NOT NULL,
                work_title TEXT NOT NULL,
                work_year TEXT,
                medium TEXT,
                dimensions TEXT,
                caption TEXT,
                FOREIGN KEY (exhibition_id) REFERENCES exhibitions(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        conn.close()

        # Step 2: Reopen with ExhibitionDatabase — ALTER TABLE add column runs
        db = ExhibitionDatabase(TEST_DB)
        conn2 = db._get_connection()
        # Verify the new columns exist
        columns = [row[1] for row in conn2.execute("PRAGMA table_info(exhibitions)")]
        conn2.close()
        assert "preface_en" in columns
        assert "concept_en" in columns
        assert "biographies" in columns
        assert "biographies_cn" in columns
        assert "credits" in columns
        assert "images" in columns
        assert "tags" in columns
        assert "series_id" in columns

    def test_migration_does_not_fail_on_existing_columns(self):
        """When columns already exist, the try/except OperationalError handles it gracefully."""
        _ = ExhibitionDatabase(TEST_DB)  # First init (side effect: creates tables)
        db2 = ExhibitionDatabase(TEST_DB)  # Reopen — ALTER TABLE should silently pass
        conn = db2._get_connection()
        columns = [row[1] for row in conn.execute("PRAGMA table_info(exhibitions)")]
        conn.close()
        assert "preface_en" in columns
        assert "tags" in columns

    def test_get_connection_returns_usable_connection(self):
        db = ExhibitionDatabase(TEST_DB)
        conn = db._get_connection()
        assert conn is not None
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        conn.close()

    def test_count_exhibitions_empty(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.count_exhibitions() == 0

    def test_count_exhibitions_with_data(self):
        db = ExhibitionDatabase(TEST_DB)
        db.insert_exhibition(
            {
                "source": "Test",
                "title": "Test",
                "url": "http://test.com",
            }
        )
        assert db.count_exhibitions() == 1

    def test_count_artworks_empty(self):
        db = ExhibitionDatabase(TEST_DB)
        assert db.count_artworks() == 0

    def test_backfill_series_id_no_biennials(self):
        db = ExhibitionDatabase(TEST_DB)
        result = db.backfill_series_id()
        assert result == 0

    def test_backfill_matches_exhibition(self):
        db = ExhibitionDatabase(TEST_DB)
        db.insert_exhibition(
            {
                "source": "Test",
                "title": "Venice Show",
                "url": "http://venice.show",
                "parser_key": "venice_biennale",
            }
        )
        updated = db.backfill_series_id()
        assert updated >= 1
        retrieved = db.get_exhibition_by_url("http://venice.show")
        assert retrieved["series_id"] is not None

    def test_delete_returns_false_on_exception(self):
        """Test delete_exhibition_by_url when exception occurs."""
        db = ExhibitionDatabase(TEST_DB)
        # Drop the exhibitions table to trigger error
        conn = db._get_connection()
        conn.execute("DROP TABLE exhibitions")
        conn.commit()
        conn.close()
        result = db.delete_exhibition_by_url("http://test.com")
        assert result is False
