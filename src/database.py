import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("auto_curation.database")

class ExhibitionDatabase:
    """Manages the SQLite database for structured art exhibition and artwork storage."""
    
    def __init__(self, db_path: str = "exhibitions.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a thread-safe connection to the SQLite database with row factory enabled."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable Foreign Key support
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for better concurrent write performance
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self):
        """Initializes database schema if tables do not exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Create exhibitions table
        cursor.execute("""
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

        # 2. Create artworks table
        cursor.execute("""
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

        # Create indexes for speed and uniqueness
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_url ON exhibitions(url);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_source ON exhibitions(source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_city ON exhibitions(city);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_start_date ON exhibitions(start_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exhibitions_parser_key ON exhibitions(parser_key);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_artworks_exhibition ON artworks(exhibition_id);")
        # Deduplicate existing artworks before creating UNIQUE index
        cursor.execute("""
            DELETE FROM artworks
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM artworks
                GROUP BY exhibition_id, artist_name, work_title
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_artworks_unique ON artworks(exhibition_id, artist_name, work_title);")
        # Check and migrate exhibitions schema for preface_en and concept_en (Bilingual Curation)
        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN preface_en TEXT;")
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN concept_en TEXT;")
        except sqlite3.OperationalError:
            pass

        # Check and migrate exhibitions schema for biographies, biographies_cn, and credits (Literature Curation)
        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN biographies TEXT;")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN biographies_cn TEXT;")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN credits TEXT;")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN images TEXT;")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE exhibitions ADD COLUMN tags TEXT DEFAULT '[]';")
        except sqlite3.OperationalError:
            pass

        # Create scraper_runs table for operational tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraper_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parser_key TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                urls_discovered INTEGER DEFAULT 0,
                urls_parsed INTEGER DEFAULT 0,
                exhibitions_saved INTEGER DEFAULT 0,
                exhibitions_failed INTEGER DEFAULT 0,
                error_message TEXT,
                run_type TEXT DEFAULT 'full'
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraper_runs_parser_key ON scraper_runs(parser_key);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraper_runs_started_at ON scraper_runs(started_at);")

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_exhibition(self, ex_data: Dict[str, Any]) -> Optional[int]:
        """Inserts an exhibition and its associated artworks into the database.
        
        Args:
            ex_data: Dictionary containing exhibition fields and a list of artworks.
                     Expected keys: source, title, preface, concept, start_date, 
                     end_date, location, city, url, artworks.
                     artworks is a list of dicts with: artist_name, work_title,
                     work_year, medium, dimensions, caption.
        
        Returns:
            The ID of the inserted or existing exhibition, or None if failed.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            curators = ex_data.get("curators", [])
            if isinstance(curators, list):
                curators = json.dumps(curators, ensure_ascii=False)

            # 1. Insert into exhibitions table using INSERT OR IGNORE
            cursor.execute("""
                INSERT OR IGNORE INTO exhibitions (
                    source, title, preface, concept, curators, start_date, end_date, location, city, url, parser_key, institution_type, preface_en, concept_en, biographies, biographies_cn, credits, images, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ex_data.get("source"),
                ex_data.get("title"),
                ex_data.get("preface"),
                ex_data.get("concept"),
                curators,
                ex_data.get("start_date"),
                ex_data.get("end_date"),
                ex_data.get("location"),
                ex_data.get("city"),
                ex_data.get("url"),
                ex_data.get("parser_key"),
                ex_data.get("institution_type", "museum"),
                ex_data.get("preface_en"),
                ex_data.get("concept_en"),
                ex_data.get("biographies"),
                ex_data.get("biographies_cn"),
                ex_data.get("credits"),
                ex_data.get("images", "[]"),
                ex_data.get("tags", "[]")
            ))

            
            ex_id = None
            if cursor.rowcount > 0:
                ex_id = cursor.lastrowid
                logger.info(f"Successfully inserted exhibition: '{ex_data.get('title')}' (ID: {ex_id})")
                
                # 2. Insert associated artworks (ignore duplicates)
                artworks = ex_data.get("artworks", [])
                for art in artworks:
                    cursor.execute("""
                        INSERT OR IGNORE INTO artworks (
                            exhibition_id, artist_name, work_title, work_year, medium, dimensions, caption
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ex_id,
                        art.get("artist_name"),
                        art.get("work_title"),
                        art.get("work_year"),
                        art.get("medium"),
                        art.get("dimensions"),
                        art.get("caption")
                    ))
                if artworks:
                    logger.info(f"Inserted {len(artworks)} artworks for exhibition ID: {ex_id}")
            else:
                # Exhibition URL already exists in database, skip or return existing ID
                cursor.execute("SELECT id FROM exhibitions WHERE url = ?", (ex_data.get("url"),))
                row = cursor.fetchone()
                if row:
                    ex_id = row["id"]
                    logger.debug(f"Exhibition URL already exists. ID: {ex_id}")
            
            conn.commit()
            return ex_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert exhibition data: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def delete_exhibition_by_url(self, url: str) -> bool:
        """Deletes an exhibition and its cascading artworks by URL."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM exhibitions WHERE url = ?", (url,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete exhibition by url '{url}': {e}")
            return False
        finally:
            conn.close()

    def get_exhibition_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single exhibition and its artworks by URL."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM exhibitions WHERE url = ?", (url,))
            ex_row = cursor.fetchone()
            if not ex_row:
                return None
                
            ex_data = dict(ex_row)
            if ex_data.get("curators"):
                try:
                    ex_data["curators"] = json.loads(ex_data["curators"])
                except json.JSONDecodeError:
                    ex_data["curators"] = []
            else:
                ex_data["curators"] = []

            cursor.execute("SELECT * FROM artworks WHERE exhibition_id = ?", (ex_data["id"],))
            art_rows = cursor.fetchall()
            ex_data["artworks"] = [dict(row) for row in art_rows]

            return ex_data
        finally:
            conn.close()

    def get_all_exhibitions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieves list of all exhibitions, optionally with pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM exhibitions ORDER BY scraped_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            
            exhibitions = []
            for row in rows:
                ex_data = dict(row)
                if ex_data.get("curators"):
                    try:
                        ex_data["curators"] = json.loads(ex_data["curators"])
                    except json.JSONDecodeError:
                        ex_data["curators"] = []
                else:
                    ex_data["curators"] = []
                cursor.execute("SELECT * FROM artworks WHERE exhibition_id = ?", (ex_data["id"],))
                art_rows = cursor.fetchall()
                ex_data["artworks"] = [dict(r) for r in art_rows]
                exhibitions.append(ex_data)

            return exhibitions
        finally:
            conn.close()
            
    def count_exhibitions(self) -> int:
        """Returns the total number of exhibitions in the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM exhibitions")
            row = cursor.fetchone()
            return row["count"] if row else 0
        finally:
            conn.close()
            
    def count_artworks(self) -> int:
        """Returns the total number of artworks in the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM artworks")
            row = cursor.fetchone()
            return row["count"] if row else 0
        finally:
            conn.close()

    # --- scraper_runs operational tracking ---

    def start_scraper_run(self, parser_key: str, run_type: str = "full") -> int:
        """Insert a new scraper run record and return its ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO scraper_runs (parser_key, run_type)
                VALUES (?, ?)
            """, (parser_key, run_type))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def finish_scraper_run(
        self,
        run_id: int,
        urls_discovered: int = 0,
        urls_parsed: int = 0,
        exhibitions_saved: int = 0,
        exhibitions_failed: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update a scraper run record with completion stats."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE scraper_runs
                SET finished_at = CURRENT_TIMESTAMP,
                    urls_discovered = ?,
                    urls_parsed = ?,
                    exhibitions_saved = ?,
                    exhibitions_failed = ?,
                    error_message = ?
                WHERE id = ?
            """, (urls_discovered, urls_parsed, exhibitions_saved, exhibitions_failed, error_message, run_id))
            conn.commit()
        finally:
            conn.close()

    def get_last_scraper_run(self, parser_key: str) -> Optional[Dict[str, Any]]:
        """Return the most recent scraper run for a parser."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM scraper_runs
                WHERE parser_key = ?
                ORDER BY started_at DESC
                LIMIT 1
            """, (parser_key,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
