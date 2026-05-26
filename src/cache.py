import json
import hashlib
import logging
import sqlite3
from typing import Dict, Any, Optional

logger = logging.getLogger("auto_curation.cache")


def make_cache_key(url: str, text: Optional[str] = None) -> str:
    """Generate cache key based on URL and text fingerprint; auto-invalidates when content changes."""
    key_data = url
    if text is not None:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        key_data += f":{len(text)}:{text_hash}"
    return hashlib.sha256(key_data.encode("utf-8")).hexdigest()


class LLMResponseCache:
    """Cache LLM structured parsing results by URL + content fingerprint to reduce duplicate calls."""

    def __init__(self, db_path: str = "exhibitions.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    source TEXT,
                    result_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_llm_cache_url ON llm_cache(url)")
            conn.commit()
        finally:
            conn.close()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Query cached result by cache_key."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT result_json FROM llm_cache WHERE cache_key = ?", (cache_key,))
            row = cursor.fetchone()
            if row:
                logger.debug(f"Cache hit for key {cache_key[:8]}...")
                return json.loads(row["result_json"])
            logger.debug(f"Cache miss for key {cache_key[:8]}...")
            return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.warning(f"Cache read error: {e}")
            return None
        finally:
            conn.close()

    def set(self, cache_key: str, url: str, source: str, result: Dict[str, Any]) -> None:
        """Write or update cached result."""
        conn = self._get_connection()
        try:
            result_json = json.dumps(result, ensure_ascii=False)
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (cache_key, url, source, result_json) VALUES (?, ?, ?, ?)",
                (cache_key, url, source, result_json)
            )
            conn.commit()
            logger.debug(f"Cache set for key {cache_key[:8]}...")
        except sqlite3.Error as e:
            logger.warning(f"Cache write error: {e}")
        finally:
            conn.close()

    def clear(self) -> int:
        """Clear all cache entries, return number of rows deleted."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("DELETE FROM llm_cache")
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.warning(f"Cache clear error: {e}")
            return 0
        finally:
            conn.close()
