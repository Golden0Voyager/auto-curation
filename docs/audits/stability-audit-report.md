# Stability Audit Report — Auto Curation Pipeline

**Date**: 2026-05-27
**Scope**: `src/scraper.py`, `src/llm_parser.py`, `src/cache.py`, `src/database.py`, `src/sites/base.py`, `run_collector.py`
**Auditor**: Claude Code Stability Auditor

---

## 1. Error Handling Robustness

### 1.1 CRITICAL — Unhandled `KeyError` / `IndexError` in LLM Response Parsing
- **Location**: `src/llm_parser.py:212`, `src/llm_parser.py:265`
- **Issue**: After `response.json()`, the code directly accesses `result["choices"][0]["message"]["content"]` without checking whether `choices` exists or is non-empty. A malformed or rate-limit response from any provider (e.g. empty `choices`, missing `message`) will raise an unhandled `KeyError` or `IndexError`, bypassing the existing `except` blocks and crashing the provider loop.
- **Recommended Fix**: Add defensive extraction before indexing:
  ```python
  choices = result.get("choices", [])
  if not choices or not isinstance(choices[0], dict):
      logger.warning(f"[{provider_name}] Unexpected response structure: {result.keys()}")
      return None
  content = choices[0].get("message", {}).get("content", "").strip()
  if not content:
      return None
  ```

### 1.2 HIGH — `json.loads` in `_parse_response` Can Crash on Non-JSON Content
- **Location**: `src/llm_parser.py:161`
- **Issue**: `_parse_response` calls `json.loads(content)` without a `try/except`. If the LLM returns plain text, a truncated stream, or an empty string, a `json.JSONDecodeError` propagates uncaught to the caller (`_call_provider` / `_call_provider_async`). Although the caller has a broad `except Exception`, the traceback is still generated and the provider loop exits for that provider instead of gracefully returning `None`.
- **Recommended Fix**: Wrap `json.loads` in a dedicated `try/except json.JSONDecodeError` inside `_parse_response` and return `None` on failure.

### 1.3 HIGH — `curl_cffi` Import Failure Not Handled Gracefully
- **Location**: `src/scraper.py:172`, `src/scraper.py:182`, `src/sites/base.py:106`
- **Issue**: `from curl_cffi import requests as curl_requests` is imported inline inside `if` blocks. If `curl_cffi` is not installed, an `ImportError` will be raised and caught by the outer `except Exception` (in `scraper.py`) or crash the listing fetch (in `base.py`). In `scraper.py` it is caught, but the error message is generic and the whole URL is marked failed, which is acceptable; in `base.py` there is no fallback — the listing page simply fails.
- **Recommended Fix**: Move the import to module level with a `HAS_CURL_CFFI` flag (like Playwright in `base.py`), and provide a clear log message when the optional dependency is missing.

### 1.4 MEDIUM — `scrapling` Import Failure Not Guarded
- **Location**: `src/scraper.py:194`
- **Issue**: `from scrapling import Fetcher` is imported inline inside a nested `try/except`. If `scrapling` is not installed, the `ImportError` is caught by the inner `except Exception as se` and re-raised, then caught by the outer `except Exception`. While not a crash, it wastes a nested exception chain and produces a confusing log.
- **Recommended Fix**: Use a module-level `HAS_SCRAPLING` flag and skip the fallback block entirely if unavailable.

### 1.5 MEDIUM — `parser.parse_exhibition_page` Native Parser Exceptions Not Isolated
- **Location**: `src/scraper.py:165`, `src/scraper.py:325`
- **Issue**: Native parser calls (`parser.parse_exhibition_page`) are inside the broad `try/except Exception` of the URL processing loop. A buggy native parser can fail the entire URL instead of just the native extraction step, and the error log is generic.
- **Recommended Fix**: Wrap the native parser call in its own `try/except` with a specific log message (e.g. "Native extraction failed, falling back to LLM"), then continue to the LLM fallback instead of failing the URL.

---

## 2. Concurrency Safety

### 2.1 CRITICAL — `stats` Dict Is a Shared Mutable State Across Async Tasks Without Synchronization
- **Location**: `src/scraper.py:291-298`, `src/scraper.py:360-370`
- **Issue**: `_scrape_html_async` uses a plain `dict` (`stats`) that is mutated by multiple concurrent `_process_one` coroutines (e.g. `stats["parsed"] += 1`, `stats["failed"] += 1`). CPython's GIL makes single-op increments "mostly safe" in practice, but this is an implementation detail, not a guarantee. Under high concurrency or non-CPython runtimes, race conditions can cause lost updates.
- **Recommended Fix**: Use `asyncio.Lock` around all `stats` mutations, or switch to `collections.Counter` wrapped with a lock, or aggregate per-task return values after `asyncio.gather` instead of shared mutable state.

### 2.2 HIGH — `httpx.AsyncClient` Created Per-URL Instead of Being Shared
- **Location**: `src/scraper.py:330-336`
- **Issue**: Inside `_process_one`, a new `httpx.AsyncClient` is instantiated for every single URL (`async with httpx.AsyncClient(...) as async_client:`). This defeats connection pooling, creates significant overhead (TCP handshake + TLS negotiation per URL), and can exhaust ephemeral ports under high concurrency.
- **Recommended Fix**: Instantiate one `httpx.AsyncClient` at the `ExhibitionScraper` level (or pass it into `_scrape_html_async`) and reuse it across all tasks. Ensure it is closed in `close()` or via `async with` at the scraper level.

### 2.3 HIGH — `asyncio.to_thread` on SQLite Writes Without Connection Pool or Write Serialization
- **Location**: `src/scraper.py:313-320`, `src/scraper.py:366`
- **Issue**: Each async task calls `asyncio.to_thread(self.db.insert_exhibition, ...)` (or `delete_exhibition_by_url`). `ExhibitionDatabase` opens a **new** `sqlite3.Connection` per call (`_get_connection`). SQLite handles multiple readers well, but with WAL mode disabled (default), writes are serialized at the file level. Concurrent writes from multiple threads can trigger `SQLITE_BUSY` errors or timeouts, especially under high concurrency.
- **Recommended Fix**:
  1. Enable WAL mode in `_init_db`: `conn.execute("PRAGMA journal_mode=WAL;")`.
  2. Use a single dedicated connection for writes, or serialize all write operations through an `asyncio.Lock`.
  3. Add `timeout` to `sqlite3.connect(..., timeout=30.0)` to reduce `SQLITE_BUSY` failures.

### 2.4 MEDIUM — `asyncio.gather` Without `return_exceptions=True` Can Cancel Remaining Tasks on First Failure
- **Location**: `src/scraper.py:376`, `src/scraper.py:590`
- **Issue**: `await asyncio.gather(*[asyncio.create_task(_process_one(url)) for url in target_urls])` does not pass `return_exceptions=True`. If one task raises an unhandled exception (e.g. `KeyboardInterrupt`, `SystemExit`, or a bug), all other pending tasks are immediately cancelled. While the current code wraps each task body in `try/except Exception`, this is fragile.
- **Recommended Fix**: Pass `return_exceptions=True` to `asyncio.gather`, then iterate results to log any exceptions without cancelling siblings.

### 2.5 MEDIUM — Playwright Browser Not Closed on Exception
- **Location**: `src/sites/base.py:166-172`
- **Issue**: In `_get_exhibition_urls_playwright`, `browser.close()` is called only on the success path. If `page.goto` or `page.content()` raises, the browser remains open (leaked process/memory leak).
- **Recommended Fix**: Use a `try/finally` block or context manager:
  ```python
  browser = p.chromium.launch(headless=True)
  try:
      page = browser.new_page()
      ...
  finally:
      browser.close()
  ```

---

## 3. Resource Management

### 3.1 HIGH — `ExhibitionScraper` Lacks Async Client Cleanup
- **Location**: `src/scraper.py:605-608`
- **Issue**: `close()` only closes the synchronous `httpx.Client`. If `ascrape_site` or `ascrape_all_sites` is used, there is no async `aclose()` method to clean up any `httpx.AsyncClient` (once refactored to be shared per 2.2).
- **Recommended Fix**: Add an `async def aclose(self)` method that closes both sync and async clients, and call it in `run_collector.py` when using `--concurrent`.

### 3.2 MEDIUM — `ExhibitionDatabase` Connections Not Closed on `_get_connection` Failure
- **Location**: `src/database.py:16-22`
- **Issue**: `_get_connection` itself cannot fail to return a connection in normal circumstances, but if `sqlite3.connect` raises (e.g. disk full, read-only filesystem), the exception propagates without any cleanup. This is acceptable because no connection was opened, but callers do not handle `sqlite3.Error` explicitly.
- **Recommended Fix**: Ensure all callers of `_get_connection` have a `try/except sqlite3.Error` block, or add a wrapper method that logs and re-raises with context.

### 3.3 MEDIUM — `run_collector.py` Creates a Second `ExhibitionDatabase` Instance in `finally` Without Closing It
- **Location**: `run_collector.py:175-178`
- **Issue**: After `scraper.close()`, a new `ExhibitionDatabase(args.db)` is instantiated to print counts. This opens a new connection that is never explicitly closed. While Python GC will eventually close it, this is poor hygiene and can leave WAL files locked briefly.
- **Recommended Fix**: Use a context manager or explicitly call `db.count_exhibitions(); db.count_artworks();` then `del db` (or add a `close()` method to `ExhibitionDatabase`).

---

## 4. Data Integrity

### 4.1 HIGH — `INSERT OR IGNORE` Silently Drops Duplicate Data Without Notifying Caller
- **Location**: `src/database.py:130-153`
- **Issue**: `insert_exhibition` uses `INSERT OR IGNORE`. If a duplicate `url` is inserted, SQLite silently ignores the row. The method then queries `SELECT id FROM exhibitions WHERE url = ?` to return the existing ID. This is functional, but it means that **updates** to an existing exhibition (e.g. new artworks, corrected dates) are silently discarded unless `--force` is used. More critically, if the `url` is the same but the exhibition metadata has changed, the caller has no way to know the data was not updated.
- **Recommended Fix**: Consider `INSERT OR REPLACE` (with caution for cascading deletes on artworks) or implement an explicit `upsert_exhibition` that updates fields and re-syncs artworks when `force=True`.

### 4.2 HIGH — Artworks Are Inserted Without Deduplication, Causing Duplicates on Re-runs
- **Location**: `src/database.py:163-177`
- **Issue**: When `insert_exhibition` succeeds, it unconditionally inserts all artworks in `ex_data["artworks"]` into the `artworks` table. There is no `UNIQUE` constraint on `(exhibition_id, artist_name, work_title)`, and no check for existing artworks. Re-running the scraper with `--force` (which deletes the exhibition by URL) will clear the old artworks via `ON DELETE CASCADE`, but re-running *without* `--force` will append duplicate artworks if the exhibition was previously inserted with a different synthetic URL or if the URL changed.
- **Recommended Fix**: Add a `UNIQUE` constraint on `(exhibition_id, artist_name, work_title)` in the `artworks` table, or clear existing artworks before re-inserting when updating an exhibition.

### 4.3 MEDIUM — `delete_exhibition_by_url` Deletes Exhibition but Does Not Handle Orphaned Artworks If FK Is Disabled
- **Location**: `src/database.py:198-211`
- **Issue**: The method relies on `ON DELETE CASCADE` to remove artworks. However, SQLite foreign keys are **not** enforced by default; they are only enabled because `_get_connection` runs `PRAGMA foreign_keys = ON`. If a connection is ever opened without that pragma (e.g. by an external tool or a future refactor), artworks will become orphaned.
- **Recommended Fix**: Document this dependency prominently, or explicitly delete artworks in a transaction before deleting the exhibition:
  ```python
  cursor.execute("DELETE FROM artworks WHERE exhibition_id = (SELECT id FROM exhibitions WHERE url = ?)", (url,))
  cursor.execute("DELETE FROM exhibitions WHERE url = ?", (url,))
  ```

### 4.4 MEDIUM — `curators` Field Serialization Is Inconsistent
- **Location**: `src/database.py:125-127`
- **Issue**: `curators` is serialized to JSON on insert, but deserialized from JSON only in `get_exhibition_by_url` and `get_all_exhibitions`. Other consumers (e.g. direct SQL queries, cache layer) receive a raw JSON string. This is a design smell, not an immediate bug, but it can lead to double-encoding or type mismatches.
- **Recommended Fix**: Store curators in a separate `exhibition_curators` junction table, or use SQLite's native JSON functions and document the convention.

---

## 5. Timeout and Retry Logic

### 5.1 CRITICAL — No Retry Logic for Transient Network Failures
- **Location**: `src/scraper.py` (throughout), `src/llm_parser.py:207`, `src/llm_parser.py:261`
- **Issue**: There is **zero** retry logic for any network call. `httpx` requests, LLM API calls, and CSV/API parsers all fail permanently on the first transient error (e.g. `ConnectTimeout`, `ReadTimeout`, `503 Service Unavailable`, rate limit). For a long-running pipeline processing 65 sites, this is a major reliability gap.
- **Recommended Fix**: Implement a unified retry decorator (or use `tenacity`) with exponential backoff for:
  - `httpx.ConnectError`, `httpx.TimeoutException`, `httpx.HTTPStatusError` (5xx, 429)
  - LLM provider `HTTPStatusError` (429, 502, 503, 504)
  - Apply a maximum of 3 retries with jitter.

### 5.2 HIGH — `httpx.Client` Timeout Is Hard-Coded to 60s Without Per-URL Override
- **Location**: `src/scraper.py:42`
- **Issue**: A single 60-second timeout is used for all synchronous operations. For large HTML pages or slow SPAs, this may be insufficient; for simple API health checks, it is excessive. There is no way for individual parsers to specify a custom timeout.
- **Recommended Fix**: Add an optional `request_timeout` class attribute to `BaseSiteParser` (default 60s) and pass it through to `client.get(..., timeout=parser.request_timeout)`.

### 5.3 MEDIUM — Playwright `page.goto` Timeout Is Hard-Coded to 60s
- **Location**: `src/sites/base.py:169`
- **Issue**: The Playwright navigation timeout is fixed at 60 seconds. Some SPAs may need more time, and there is no parser-level override.
- **Recommended Fix**: Add `playwright_timeout` class attribute to `BaseSiteParser` and use it in `page.goto(..., timeout=self.playwright_timeout)`.

---

## 6. Logging and Observability

### 6.1 HIGH — API Keys Are Not Logged Directly, but Could Leak in Exception Tracebacks
- **Location**: `src/llm_parser.py:185-186`, `src/llm_parser.py:238-239`
- **Issue**: The `Authorization: Bearer <api_key>` header is constructed and passed to `httpx`. While the code does not `logger.info` the key, if an unhandled exception occurs inside `httpx` (e.g. a proxy error, SSL error), the `httpx` library may include the full request headers in the exception message or traceback. This could leak keys into logs.
- **Recommended Fix**: Use `httpx` with a custom `event_hooks` or `logging.Filter` to redact `Authorization` headers from any log output. Alternatively, set `logger.propagate = False` for sensitive sub-loggers and sanitize exception messages before logging.

### 6.2 MEDIUM — `exc_info=True` Used Inconsistently, Reducing Debuggability
- **Location**: `src/scraper.py:270` (has `exc_info=True`), `src/llm_parser.py:222` (has `exc_info=False`)
- **Issue**: In `scraper.py`, URL-level failures log full tracebacks (good). In `llm_parser.py`, provider-level failures suppress tracebacks (`exc_info=False`), making it hard to distinguish between a network timeout, a JSON parse error, or a provider-side failure.
- **Recommended Fix**: Use `exc_info=True` for all unexpected exceptions in the LLM parser, or at least for `Exception` catch-all blocks. Reserve `exc_info=False` only for known, expected failure modes (e.g. HTTP 429).

### 6.3 LOW — Cache Hit/Miss Logs Use Shortened Keys That May Collide
- **Location**: `src/cache.py:55`, `src/cache.py:58`, `src/llm_parser.py:303`, `src/llm_parser.py:332`
- **Issue**: Cache logs show only the first 8 characters of the SHA-256 key. While unlikely, SHA-256 truncated to 8 hex chars has a non-zero collision probability and makes it impossible to correlate logs with actual cache entries for deep debugging.
- **Recommended Fix**: Log the full cache key at `DEBUG` level, or include the source + URL in the log message for correlation.

---

## Summary Table

| Severity | Count | Top Categories |
|:---------|:------|:---------------|
| CRITICAL | 3     | Unhandled response parsing, shared mutable state in async, no retry logic |
| HIGH     | 7     | Per-URL AsyncClient, SQLite write serialization, API key leak risk, data deduplication, hard-coded timeouts |
| MEDIUM   | 9     | Import guards, Playwright cleanup, `gather` cancellation, DB connection hygiene, FK orphan risk, inconsistent deserialization, log collision |
| LOW      | 1     | Cache key log truncation |

---

## Immediate Action Items (Priority Order)

1. **Defensive LLM response parsing** (`llm_parser.py:212,265`) — Add `get("choices", [])` guards.
2. **Serialize async `stats` mutations** (`scraper.py`) — Use `asyncio.Lock` or per-task aggregation.
3. **Reuse `httpx.AsyncClient`** (`scraper.py:330`) — Move to instance-level and add `aclose()`.
4. **Enable SQLite WAL mode + write lock** (`database.py`) — Prevent `SQLITE_BUSY` under concurrency.
5. **Add retry decorator** (`scraper.py`, `llm_parser.py`) — Use `tenacity` for 3 retries with backoff.
6. **Guard API keys in logs** (`llm_parser.py`) — Redact `Authorization` headers from exception tracebacks.
7. **Fix Playwright browser leak** (`base.py:166`) — Use `try/finally` for `browser.close()`.
8. **Deduplicate artworks** (`database.py:163`) — Add `UNIQUE` constraint or pre-clear on update.
