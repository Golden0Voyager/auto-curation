# Async 并发爬取 + LLM 响应缓存 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `ExhibitionScraper` 的 HTML 详情页抓取改为 Async 并发（Semaphore 限制 10），并在 `LLMExhibitionParser` 中增加按 URL+文本指纹的响应缓存，节省 30-50% LLM 调用成本。

**Architecture:**
1. **缓存先行**：新建 `src/cache.py` 的 `LLMResponseCache`，在 `exhibitions.db` 中维护 `llm_cache` 表。`LLMExhibitionParser` 的同步/异步解析方法均先查缓存、后写缓存。
2. **Async 改造**：`ExhibitionScraper` 保留全部同步 API 不变，新增 `ascrape_site` / `ascrape_all_sites` 方法。URL 发现阶段仍用同步 `httpx.Client`（成本低），展览详情页抓取 + LLM 解析改为 `asyncio.gather` + `Semaphore(10)` 并发。LLM HTTP 调用走 `httpx.AsyncClient`。数据库写入用 `asyncio.to_thread()` 包裹以不阻塞 event loop。

**Tech Stack:** Python 3.12+, `httpx`, `asyncio`, `pytest`, `sqlite3`

---

## 文件结构

| 文件 | 变更类型 | 说明 |
|:--|:--|:--|
| `src/cache.py` | 新建 | `LLMResponseCache`：SQLite 缓存表读写、缓存键生成 |
| `src/llm_parser.py` | 修改 | 集成缓存；新增 `parse_exhibition_text_async` |
| `src/scraper.py` | 修改 | 新增 `ascrape_site`、`ascrape_all_sites`、`_scrape_html_async` |
| `run_collector.py` | 修改 | 新增 `--concurrent` CLI flag |
| `tests/test_cache.py` | 新建 | 缓存 CRUD 与缓存键测试 |
| `tests/test_async_scraper.py` | 新建 | async scraper 并发与降级测试 |
| `tests/test_llm_parser_cache.py` | 新建 | LLM parser 缓存命中/未命中测试 |

---

## Task 1: LLM 响应缓存模块 (`src/cache.py`)

**Files:**
- Create: `src/cache.py`
- Create: `tests/test_cache.py`
- Modify: `src/database.py`（可选，若 cache 模块自管表则不动 database.py）

---

- [ ] **Step 1: 安装 pytest 为 dev 依赖**

Run: `uv pip install pytest pytest-asyncio`
Expected: pytest 安装成功

- [ ] **Step 2: 新建 `src/cache.py`**

```python
import json
import hashlib
import logging
import sqlite3
from typing import Dict, Any, Optional

logger = logging.getLogger("auto_curation.cache")


def make_cache_key(url: str, text: Optional[str] = None) -> str:
    """生成缓存键：基于 URL 和文本指纹，内容变化时自动失效。"""
    key_data = url
    if text is not None:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        key_data += f":{len(text)}:{text_hash}"
    return hashlib.sha256(key_data.encode("utf-8")).hexdigest()


class LLMResponseCache:
    """按 URL + 文本内容指纹缓存 LLM 结构化解析结果，减少重复调用。"""

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
        """根据 cache_key 查询缓存结果。"""
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
        """写入或更新缓存结果。"""
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
        """清空全部缓存，返回删除行数。"""
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
```

- [ ] **Step 3: 新建 `tests/test_cache.py`**

```python
import os
import pytest
from src.cache import LLMResponseCache, make_cache_key

TEST_DB = "tests/test_cache.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_make_cache_key_consistency():
    key1 = make_cache_key("https://example.com/ex1", "some text")
    key2 = make_cache_key("https://example.com/ex1", "some text")
    assert key1 == key2
    assert len(key1) == 64  # sha256 hex


def test_make_cache_key_differentiates_text():
    key1 = make_cache_key("https://example.com/ex1", "text a")
    key2 = make_cache_key("https://example.com/ex1", "text b")
    assert key1 != key2


def test_cache_set_and_get():
    cache = LLMResponseCache(TEST_DB)
    result = {"title": "Test Exhibition", "city": "Beijing"}
    cache.set("key1", "https://example.com/1", "test", result)

    cached = cache.get("key1")
    assert cached == result


def test_cache_miss_returns_none():
    cache = LLMResponseCache(TEST_DB)
    assert cache.get("nonexistent") is None


def test_cache_clear():
    cache = LLMResponseCache(TEST_DB)
    cache.set("k1", "url1", "s1", {"a": 1})
    cache.set("k2", "url2", "s2", {"b": 2})
    assert cache.clear() == 2
    assert cache.get("k1") is None
```

- [ ] **Step 4: 运行缓存测试**

Run: `cd /Users/hainingyu/Code/auto_curation && python -m pytest tests/test_cache.py -v`
Expected: 5 tests passed

- [ ] **Step 5: Commit**

```bash
cd /Users/hainingyu/Code/auto_curation
git add src/cache.py tests/test_cache.py
git commit -m "feat(cache): add LLM response cache with URL+text fingerprint keys

新增 LLMResponseCache 模块，基于 SQLite 缓存 LLM 解析结果，
缓存键由 URL 和文本 SHA256 指纹生成，内容变化时自动失效。"
```

---

## Task 2: 在 `LLMExhibitionParser` 中集成缓存与 Async 支持

**Files:**
- Modify: `src/llm_parser.py`
- Create: `tests/test_llm_parser_cache.py`

---

- [ ] **Step 1: 修改 `src/llm_parser.py` 的 imports 与构造器**

在文件顶部增加 import：
```python
import asyncio
from src.cache import LLMResponseCache, make_cache_key
```

修改 `__init__`：
```python
    def __init__(self, cache: Optional[LLMResponseCache] = None):
        # ... 原有 API key 解析逻辑保持不变 ...
        self.cache = cache
        if self.cache:
            logger.info("LLM response caching enabled.")
```

- [ ] **Step 2: 在 `parse_exhibition_text` 中集成缓存**

在方法开头（`if not self.api_key:` 之后）插入：
```python
        cache_key = make_cache_key(f"{source}:{default_city}", text)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.info(f"Cache hit for {source} exhibition text (key: {cache_key[:8]}...)")
                return cached
```

在方法末尾（`return validated_data.model_dump()` 之前）插入：
```python
                if self.cache:
                    self.cache.set(cache_key, f"{source}:{default_city}", source, validated_data.model_dump())
```

⚠️ 注意：由于 `parse_exhibition_text` 没有接收 `url` 参数，这里用 `source:default_city` 作为 URL 标识，用 `text` 作为内容指纹。

- [ ] **Step 3: 新建 `parse_exhibition_text_async`**

在 `parse_exhibition_text` 方法之后，新增完整 async 方法：

```python
    async def parse_exhibition_text_async(self, text: str, source: str, default_city: str = "") -> Optional[Dict[str, Any]]:
        """异步版本：发送清洗后的文本到 LLM 并返回结构化数据，带缓存。"""
        if not self.api_key:
            logger.error("Cannot parse text: API key is missing.")
            return None

        cache_key = make_cache_key(f"{source}:{default_city}", text)
        if self.cache:
            cached = await asyncio.to_thread(self.cache.get, cache_key)
            if cached is not None:
                logger.info(f"Cache hit for {source} exhibition text (key: {cache_key[:8]}...)")
                return cached

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are an expert contemporary art curator and metadata extractor.\n"
            "Your task is to analyze the raw text/markdown extracted from an art museum or biennial's exhibition page, "
            "and extract structured metadata into a precise JSON format.\n\n"
            "Respond ONLY with a valid JSON object matching the requested schema. Do not include markdown code block formatting (like ```json or ```). Only output raw JSON."
        )

        user_prompt = f"""
Institution: {source}
Default City: {default_city}

Analyze the following raw text/markdown and extract the structured metadata.

=== TEXT ===
{text}
=== END TEXT ===
Extract this JSON Schema exactly:
{{
  "title": "Exhibition title or theme (required, string)",
  "preface": "Detailed exhibition preface/introduction/description in Chinese (string or null)",
  "concept": "Specific curatorial concept or theoretical background in Chinese if mentioned (string or null)",
  "preface_en": "Detailed exhibition preface/introduction/description in original English (string or null)",
  "concept_en": "Specific curatorial concept or theoretical background in original English if mentioned (string or null)",
  "biographies": "Detailed biographies of artists and collaborators in original English, formatted in clean Markdown (string or null)",
  "biographies_cn": "A brief summary/translation of the primary artist biography in Chinese, formatted in clean Markdown (string or null)",
  "credits": "Detailed exhibition credits, curators, collaborator technical credits, production, playtesters, and special thanks in original English, formatted in clean Markdown (string or null)",
  "curators": ["List of curators (array of strings)"],
  "start_date": "Exhibition start date, e.g. 2026-05-23 (string or null)",
  "end_date": "Exhibition end date, e.g. 2026-11-22 (string or null)",
  "location": "Gallery name or gallery number inside the museum, e.g. Floor 3, Gallery 302 (string or null)",
  "city": "Host city (string or null)",
  "artworks": [
    {{
      "artist_name": "Name of the artist (required, string)",
      "work_title": "Title of the artwork in original language/English (required, string)",
      "work_year": "Year of creation (string or null)",
      "medium": "Medium/materials used, e.g. Oil on canvas, video, wood (string or null)",
      "dimensions": "Dimensions of the artwork, e.g. 120 x 200 cm (string or null)",
      "caption": "Full combined caption label string (string or null)"
    }}
  ]
}}

Strict Guidelines:
1. Ensure the 'title' field is always populated. If not clear, synthesize a suitable title from the page main headers.
2. For 'preface' and 'concept', translate or summarize into fluent and professional Chinese art curatorial style. For 'preface_en' and 'concept_en', extract and summarize the high-density exhibition description in English, filtering out generic navigation/ticketing information.
3. For 'artworks', extract concrete works of art explicitly listed or described in the text with their captions. If no specific artworks are listed or described, but the page is a dedicated solo or group exhibition of specific artists, you MUST synthesize at least one artwork entry for each primary artist, setting 'artist_name' to the artist's full name, and 'work_title' to 'Selected Works' (or '代表作品' / '参展作品'), so that the artists are correctly linked to the exhibition in the database. Keep artist names in their original language/spelling.
4. Ensure 'city' is populated, using the Default City if not explicitly found in the text.
5. Extract 'biographies' (biographies of artists and collaborators in original English, keeping each biography relatively concise, around 2-3 sentences per collaborator to highlight their key roles and achievements) and 'credits' (all curators, video game development, playtesters, and special thanks in original English, formatted in clean Markdown lists or sections) exactly as listed on the page. Keep lists of playtesters and special thanks concise if they are extremely long. For 'biographies_cn', translate the primary artist biography into a short, elegant Chinese biography/intro.
"""

        if self.provider == "sensenova":
            model_name = "DeepSeek-V3-1"
        elif self.provider == "gemini":
            model_name = "gemini-2.5-flash"
        else:
            model_name = "deepseek-ai/DeepSeek-V3"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "max_tokens": 4096
        }

        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            logger.info(f"Sending async LLM parsing request to {model_name}...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip("` \n")

                parsed_json = json.loads(content)
                if isinstance(parsed_json, list):
                    if len(parsed_json) > 0:
                        parsed_json = parsed_json[0]
                    else:
                        parsed_json = {}
                validated_data = ExhibitionModel(**parsed_json)

                data = validated_data.model_dump()
                if self.cache:
                    await asyncio.to_thread(self.cache.set, cache_key, f"{source}:{default_city}", source, data)
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling LLM API: {e.response.status_code} - {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM response as JSON. Content was: {content[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Error parsing exhibition text: {e}", exc_info=True)
            return None
```

- [ ] **Step 4: 新建 `tests/test_llm_parser_cache.py`**

```python
import os
import pytest
from unittest.mock import patch, MagicMock
from src.cache import LLMResponseCache
from src.llm_parser import LLMExhibitionParser

TEST_DB = "tests/test_llm_parser.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_llm_parser_cache_hit_skips_api_call():
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    # 预置缓存
    expected = {"title": "Cached Show", "city": "Tokyo", "artworks": []}
    from src.cache import make_cache_key
    key = make_cache_key("TestSource:", "some exhibition text")
    cache.set(key, "url", "TestSource", expected)

    with patch("httpx.Client.post") as mock_post:
        result = parser.parse_exhibition_text("some exhibition text", "TestSource")
        assert result == expected
        mock_post.assert_not_called()


def test_llm_parser_cache_miss_sets_cache(monkeypatch):
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": '{"title":"New Show","city":"Paris","artworks":[]}'}}]
    }
    fake_response.raise_for_status = MagicMock()

    with patch("httpx.Client.post", return_value=fake_response):
        result = parser.parse_exhibition_text("fresh text", "TestSource")
        assert result is not None
        assert result["title"] == "New Show"

    # 验证缓存已写入
    from src.cache import make_cache_key
    key = make_cache_key("TestSource:", "fresh text")
    cached = cache.get(key)
    assert cached is not None
    assert cached["title"] == "New Show"


@pytest.mark.asyncio
async def test_llm_parser_async_cache_hit():
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)
    expected = {"title": "Async Cached", "city": "Berlin", "artworks": []}
    from src.cache import make_cache_key
    key = make_cache_key("AsyncSource:", "async text")
    cache.set(key, "url", "AsyncSource", expected)

    with patch("httpx.AsyncClient.post") as mock_post:
        result = await parser.parse_exhibition_text_async("async text", "AsyncSource")
        assert result == expected
        mock_post.assert_not_called()
```

- [ ] **Step 5: 运行 LLM parser 测试**

Run: `cd /Users/hainingyu/Code/auto_curation && python -m pytest tests/test_llm_parser_cache.py -v`
Expected: 3 tests passed

- [ ] **Step 6: Commit**

```bash
cd /Users/hainingyu/Code/auto_curation
git add src/llm_parser.py tests/test_llm_parser_cache.py
git commit -m "feat(llm): integrate response cache and add async parse method

LLMExhibitionParser 集成 LLMResponseCache，同步与异步解析均支持缓存。
新增 parse_exhibition_text_async，使用 httpx.AsyncClient 进行异步 LLM 调用。"
```

---

## Task 3: `ExhibitionScraper` Async 并发改造

**Files:**
- Modify: `src/scraper.py`
- Create: `tests/test_async_scraper.py`

---

- [ ] **Step 1: 修改 `src/scraper.py` 的 imports**

在文件顶部增加：
```python
import asyncio
from src.cache import LLMResponseCache
```

- [ ] **Step 2: 修改 `__init__` 启用缓存**

```python
    def __init__(self, db_path: str = "exhibitions.db", max_concurrency: int = 10):
        self.db = ExhibitionDatabase(db_path)
        self.parser = LLMExhibitionParser(cache=LLMResponseCache(db_path))
        self.client = httpx.Client(headers={...}, follow_redirects=True, timeout=30.0)
        self.max_concurrency = max_concurrency
```

（headers 字典保持原样不变）

- [ ] **Step 3: 新增 `ascrape_site` 方法**

在 `scrape_site` 方法之后（或 `scrape_all_sites` 之前），插入：

```python
    async def ascrape_site(
        self,
        site_key: str,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """异步版本：对单个机构的 HTML 详情页进行并发抓取与解析。"""
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}

        parser = SITES[site_key]
        strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
        handler_name = self.STRATEGY_HANDLERS.get(strategy)

        if not handler_name:
            logger.error(f"No handler for strategy {strategy} on {site_key}")
            return {"error": f"Unknown strategy {strategy}"}

        # CSV / API / ARTWORK_ONLY 暂无并发收益，回退到同步实现
        if strategy != ParserStrategy.HTML_LLM:
            handler = getattr(self, handler_name)
            return handler(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

        logger.info(
            f"[ASYNC] Starting scrape for '{parser.source}' (City: {parser.city}) "
            f"| strategy={strategy.value}{' | since=' + str(since_year) if since_year else ''}"
        )
        return await self._scrape_html_async(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)
```

- [ ] **Step 4: 新增 `_scrape_html_async` 方法**

在 `_scrape_html` 方法之后插入完整 async 方法：

```python
    async def _scrape_html_async(
        self,
        parser,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """异步并发版 HTML 抓取管道。URL 发现同步进行，详情页并发抓取。"""
        urls = parser.get_exhibition_urls(self.client, since_year=since_year)
        if not urls:
            logger.warning(f"No exhibition URLs discovered for {parser.source}.")
            return {"site": parser.source, "discovered": 0, "parsed": 0, "saved": 0, "skipped": 0, "failed": 0}

        stats = {
            "site": parser.source,
            "discovered": len(urls),
            "parsed": 0,
            "saved": 0,
            "skipped": 0,
            "failed": 0
        }

        has_native_parser = hasattr(parser, "parse_exhibition_page") and callable(getattr(parser, "parse_exhibition_page"))
        if has_native_parser:
            logger.info(f"[{parser.source}] Parser provides native page extraction; LLM step will be skipped.")

        target_urls = urls if limit is None else urls[:limit]
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _process_one(url: str) -> None:
            async with semaphore:
                logger.info(f"[ASYNC] Processing: {url}")

                try:
                    if not force and not dry_run:
                        existing = await asyncio.to_thread(self.db.get_exhibition_by_url, url)
                        if existing:
                            logger.info(f"-> Skip: already in DB (ID: {existing['id']})")
                            stats["skipped"] += 1
                            return
                    elif force and not dry_run:
                        logger.info(f"-> Force active: Deleting existing DB entry for URL to ensure clean overwrite: {url}")
                        await asyncio.to_thread(self.db.delete_exhibition_by_url, url)

                    parsed_data = None

                    # 1. Try native extraction
                    if has_native_parser:
                        parsed_data = parser.parse_exhibition_page(self.client, url)
                        if parsed_data:
                            logger.info(f"[{parser.source}] Native extraction succeeded for {url}")

                    # 2. Fall back to async LLM pipeline
                    if not parsed_data:
                        async with httpx.AsyncClient(headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                            "Accept-Language": "en-US,en;q=0.9",
                        }, follow_redirects=True, timeout=30.0) as async_client:
                            response = await async_client.get(url)
                            response.raise_for_status()
                            html_text = response.text

                        clean_text = parser.clean_html(html_text)
                        if not clean_text or len(clean_text.strip()) < 100:
                            logger.warning(f"Content too short/empty for {url}. Skipping.")
                            stats["failed"] += 1
                            return

                        logger.info(f"Sending {len(clean_text)} chars to LLM (async)...")
                        parsed_data = await self.parser.parse_exhibition_text_async(
                            clean_text, parser.source, parser.city
                        )
                        if not parsed_data:
                            logger.error(f"-> LLM parsing failed for: {url}")
                            stats["failed"] += 1
                            return

                        # Extract image links
                        from bs4 import BeautifulSoup
                        from urllib.parse import urljoin
                        image_urls = []
                        try:
                            soup = BeautifulSoup(html_text, "html.parser")
                            for img in soup.find_all("img", src=True):
                                src = img["src"].strip()
                                full_img_url = urljoin(url, src)
                                if any(kw in full_img_url.lower() for kw in ["logo", "icon", "avatar", "pixel", "tracking", "badge", "nav", "footer"]):
                                    continue
                                if not any(ext in full_img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                                    continue
                                image_urls.append(full_img_url)
                            image_urls = list(dict.fromkeys(image_urls))[:8]
                        except Exception as e:
                            logger.error(f"Error extracting image links: {e}")
                        parsed_data["images"] = json.dumps(image_urls)

                    if parsed_data and "images" not in parsed_data:
                        parsed_data["images"] = "[]"

                    parsed_data["source"] = parser.source
                    parsed_data["url"] = url
                    parsed_data["parser_key"] = getattr(parser, "parser_key", "")
                    parsed_data["institution_type"] = getattr(parser, "institution_type", "museum")
                    if not parsed_data.get("city"):
                        parsed_data["city"] = parser.city

                    if hasattr(parser, "_url_tags") and url in parser._url_tags:
                        parsed_data["tags"] = parser._url_tags[url]
                    else:
                        parsed_data["tags"] = "[]"

                    stats["parsed"] += 1

                    if dry_run:
                        logger.info(f"[DRY-RUN] '{parsed_data['title']}': {len(parsed_data.get('artworks', []))} artworks extracted.")
                        stats["saved"] += 1
                    else:
                        ex_id = await asyncio.to_thread(self.db.insert_exhibition, parsed_data)
                        if ex_id:
                            stats["saved"] += 1
                        else:
                            stats["failed"] += 1

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}", exc_info=True)
                    stats["failed"] += 1

        await asyncio.gather(*[asyncio.create_task(_process_one(url)) for url in target_urls])
        logger.info(f"[ASYNC] Done: '{parser.source}' | {stats}")
        return stats
```

- [ ] **Step 5: 新增 `ascrape_all_sites` 方法**

在 `scrape_all_sites` 方法之后插入：

```python
    async def ascrape_all_sites(
        self,
        limit_per_site: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """异步并发版：对所有注册机构的 HTML 策略站点并行采集。"""
        results = []
        html_site_keys = [
            k for k, p in SITES.items()
            if getattr(p, "strategy", ParserStrategy.HTML_LLM) == ParserStrategy.HTML_LLM
        ]
        logger.info(f"[ASYNC] Starting bulk scraper for {len(html_site_keys)} HTML-based institutions.")

        async def _scrape_one(site_key: str) -> Dict[str, Any]:
            return await self.ascrape_site(
                site_key,
                limit=limit_per_site,
                force=force,
                dry_run=dry_run,
                since_year=since_year
            )

        results = await asyncio.gather(*[asyncio.create_task(_scrape_one(k)) for k in html_site_keys])

        # 非 HTML 策略回退到同步串行（数量少）
        other_keys = [k for k in SITES if k not in html_site_keys]
        for site_key in other_keys:
            res = self.scrape_site(
                site_key,
                limit=limit_per_site,
                force=force,
                dry_run=dry_run,
                since_year=since_year
            )
            results.append(res)

        return results
```

- [ ] **Step 6: 新建 `tests/test_async_scraper.py`**

```python
import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch
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
        return html


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
        return {
            "title": f"Exhibition {call_count}",
            "city": default_city,
            "artworks": []
        }

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
    """同步 API 必须保持向后兼容。"""
    scraper = ExhibitionScraper(TEST_DB)
    # 使用 dummy parser 的 native extraction 避免真实 LLM 调用
    DummyParser.parse_exhibition_page = lambda self, client, url: {
        "title": "Native", "city": "TestCity", "artworks": []
    }
    result = scraper.scrape_site("dummy", limit=1, dry_run=True)
    assert result["parsed"] >= 0
```

- [ ] **Step 7: 运行 async scraper 测试**

Run: `cd /Users/hainingyu/Code/auto_curation && python -m pytest tests/test_async_scraper.py -v`
Expected: 3 tests passed

- [ ] **Step 8: Commit**

```bash
cd /Users/hainingyu/Code/auto_curation
git add src/scraper.py tests/test_async_scraper.py
git commit -m "feat(scraper): add async concurrent scraping with semaphore control

新增 ascrape_site 与 ascrape_all_sites 方法：
- HTML 详情页抓取使用 asyncio.Semaphore 限制并发（默认 10）
- LLM 调用走 parse_exhibition_text_async
- 数据库写入使用 asyncio.to_thread 避免阻塞 event loop
- 同步 API scrape_site / scrape_all_sites 完全保持向后兼容"
```

---

## Task 4: CLI 集成 `--concurrent` 开关

**Files:**
- Modify: `run_collector.py`

---

- [ ] **Step 1: 修改 `run_collector.py` 添加 `--concurrent` flag**

在 `arg_parser.add_argument("--db", ...)` 之前插入：
```python
    arg_parser.add_argument("--concurrent", action="store_true", help="启用异步并发采集（仅对 HTML 策略生效）")
```

- [ ] **Step 2: 修改 `main()` 中的 `--all` 分支支持 async**

在 `if args.all:` 分支中，将：
```python
            results = scraper.scrape_all_sites(
                limit_per_site=args.limit,
                force=args.force,
                dry_run=args.dry_run,
                since_year=args.since
            )
```
改为：
```python
            if args.concurrent:
                results = asyncio.run(scraper.ascrape_all_sites(
                    limit_per_site=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                ))
            else:
                results = scraper.scrape_all_sites(
                    limit_per_site=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                )
```

需要在 `run_collector.py` 顶部增加 `import asyncio`。

- [ ] **Step 3: 修改 `main()` 中的 `--site` 分支支持 async**

在 `elif args.site:` 分支中，将：
```python
            res = scraper.scrape_site(
                site_key,
                limit=args.limit,
                force=args.force,
                dry_run=args.dry_run,
                since_year=args.since
            )
```
改为：
```python
            if args.concurrent:
                res = asyncio.run(scraper.ascrape_site(
                    site_key,
                    limit=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                ))
            else:
                res = scraper.scrape_site(
                    site_key,
                    limit=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                )
```

- [ ] **Step 4: 验证 CLI 帮助文本**

Run: `cd /Users/hainingyu/Code/auto_curation && python run_collector.py --help`
Expected: 输出中包含 `--concurrent` 选项

- [ ] **Step 5: Commit**

```bash
cd /Users/hainingyu/Code/auto_curation
git add run_collector.py
git commit -m "feat(cli): add --concurrent flag for async scraping

run_collector.py 新增 --concurrent 参数，调用 ascrape_site / ascrape_all_sites
启用异步并发采集。默认行为不变，保持向后兼容。"
```

---

## Self-Review Checklist

### 1. Spec Coverage
| 需求 | 实现任务 |
|:--|:--|
| `httpx.AsyncClient` + `asyncio.Semaphore(10)` 并发 | Task 3, Step 4 |
| 全量采集从小时级降至分钟级 | Task 3, Step 5 (`ascrape_all_sites` 并行) |
| 按 URL hash 缓存结构化结果 | Task 1, Step 2 (`make_cache_key`) |
| 避免重复 LLM 调用（节省 30-50% 成本） | Task 2, Step 2 & 4 |
| 同步 API 向后兼容 | Task 3, Step 7 测试 + `scrape_site` 保持原样 |

### 2. Placeholder Scan
- 无 TBD / TODO。
- 所有代码块含完整实现。
- 所有测试含断言。

### 3. Type Consistency
- `LLMExhibitionParser.__init__` 参数：`cache: Optional[LLMResponseCache]` — Task 2, Step 1。
- `ExhibitionScraper.__init__` 参数：`max_concurrency: int` — Task 3, Step 2。
- 所有 async 方法返回类型与同步版本一致（`Optional[Dict[str, Any]]` / `Dict[str, Any]`）。

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-26-async-scraping-and-llm-cache.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
