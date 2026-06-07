import asyncio
import json
import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from src.cache import LLMResponseCache
from src.database import ExhibitionDatabase
from src.llm_parser import LLMExhibitionParser
from src.sites import SITES
from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.scraper")

# Security: max HTML response size to prevent OOM from malicious/large pages (5 MB)
MAX_HTML_SIZE = 5 * 1024 * 1024


def extract_images_from_html(html: str, base_url: str, max_images: int = 8) -> list[str]:
    """Deterministically extract image URLs from HTML using BeautifulSoup.

    Filters out logos, icons, tracking pixels, and non-image file types.
    Deduplicates and limits to max_images.

    Args:
        html: Raw HTML string.
        base_url: Base URL for resolving relative image paths.
        max_images: Maximum number of images to return.

    Returns:
        List of absolute image URLs.
    """
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        image_urls = []
        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            full_img_url = urljoin(base_url, src)
            if any(
                kw in full_img_url.lower()
                for kw in ["logo", "icon", "avatar", "pixel", "tracking", "badge", "nav", "footer"]
            ):
                continue
            if not any(ext in full_img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue
            image_urls.append(full_img_url)
        return list(dict.fromkeys(image_urls))[:max_images]
    except Exception as e:
        logger.error(f"Error extracting image links: {e}")
        return []


def _is_retryable_http_error(exc: BaseException) -> bool:
    """Determine if an HTTP exception warrants a retry."""
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 502, 503, 504)
    return False


class ExhibitionScraper:
    """Orchestrates the entire scraping pipeline: URL discovery, HTML cleaning,
    LLM metadata extraction, and database persistence.

    Supports pluggable scraping strategies determined by each parser's
    `strategy` class attribute:
    1. HTML + LLM (default)
    2. CSV local/remote ingestion
    3. REST API / SPARQL ingestion
    4. Artwork-only collection databases
    """

    STRATEGY_HANDLERS = {
        ParserStrategy.HTML_LLM: "_scrape_html",
        ParserStrategy.CSV_LOCAL: "_scrape_csv",
        ParserStrategy.CSV_REMOTE: "_scrape_csv",
        ParserStrategy.REST_API: "_scrape_api",
        ParserStrategy.SPARQL: "_scrape_api",
        ParserStrategy.ARTWORK_ONLY: "_scrape_artwork_only",
    }

    def __init__(self, db_path: str = "exhibitions.db", max_concurrency: int = 10):
        self.db = ExhibitionDatabase(db_path)
        self.parser = LLMExhibitionParser(cache=LLMResponseCache(db_path))
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            max_redirects=5,
            timeout=60.0,
        )
        self.max_concurrency = max_concurrency
        self._stats_lock = asyncio.Lock()
        self.async_client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            max_redirects=5,
            timeout=60.0,
        )

    def scrape_site(
        self,
        site_key: str,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Scrapes exhibitions from a single registered institution.

        Routes to the appropriate pipeline based on the parser's strategy.
        """
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}

        parser = SITES[site_key]
        if not parser.parser_key:
            parser.parser_key = site_key
        strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
        handler_name = self.STRATEGY_HANDLERS.get(strategy)

        if not handler_name:
            logger.error(f"No handler for strategy {strategy} on {site_key}")
            return {"error": f"Unknown strategy {strategy}"}

        handler = getattr(self, handler_name)
        logger.info(
            f"Starting scrape for '{parser.source}' (City: {parser.city}) "
            f"| strategy={strategy.value}{' | since=' + str(since_year) if since_year else ''}"
        )

        run_type = "dry_run" if dry_run else ("limit" if limit else "full")
        run_id = self.db.start_scraper_run(site_key, run_type)
        try:
            result = handler(
                parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year
            )
            self.db.finish_scraper_run(
                run_id,
                urls_discovered=result.get("discovered", 0),
                urls_parsed=result.get("parsed", 0),
                exhibitions_saved=result.get("saved", 0),
                exhibitions_failed=result.get("failed", 0),
                error_message=result.get("error"),
            )
            return result
        except Exception as e:
            self.db.finish_scraper_run(run_id, error_message=str(e)[:500])
            raise

    async def ascrape_site(
        self,
        site_key: str,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Asynchronous version: concurrent scraping for a single institution."""
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}

        parser = SITES[site_key]
        if not parser.parser_key:
            parser.parser_key = site_key
        strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
        handler_name = self.STRATEGY_HANDLERS.get(strategy)

        if not handler_name:
            logger.error(f"No handler for strategy {strategy} on {site_key}")
            return {"error": f"Unknown strategy {strategy}"}

        if strategy != ParserStrategy.HTML_LLM:
            handler = getattr(self, handler_name)
            return handler(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

        logger.info(
            f"[ASYNC] Starting scrape for '{parser.source}' (City: {parser.city}) "
            f"| strategy={strategy.value}{' | since=' + str(since_year) if since_year else ''}"
        )

        run_type = "dry_run" if dry_run else ("limit" if limit else "full")
        run_id = self.db.start_scraper_run(site_key, run_type)
        try:
            result = await self._scrape_html_async(
                parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year
            )
            await asyncio.to_thread(
                self.db.finish_scraper_run,
                run_id,
                urls_discovered=result.get("discovered", 0),
                urls_parsed=result.get("parsed", 0),
                exhibitions_saved=result.get("saved", 0),
                exhibitions_failed=result.get("failed", 0),
                error_message=result.get("error"),
            )
            return result
        except Exception as e:
            await asyncio.to_thread(self.db.finish_scraper_run, run_id, error_message=str(e)[:500])
            raise

    # ------------------------------------------------------------------
    # Strategy handlers
    # ------------------------------------------------------------------

    def _scrape_html(
        self,
        parser,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Standard HTML scraping pipeline: discover URLs, clean HTML, LLM parse.

        If a parser implements ``parse_exhibition_page(client, url)`` and returns
        a dict, that structured data is used directly and the LLM step is skipped.
        """
        urls = parser.get_exhibition_urls(self.client, since_year=since_year)
        if not urls:
            logger.warning(f"No exhibition URLs discovered for {parser.source}.")
            return {
                "site": parser.source,
                "discovered": 0,
                "parsed": 0,
                "saved": 0,
                "skipped": 0,
                "failed": 0,
            }

        stats = {
            "site": parser.source,
            "discovered": len(urls),
            "parsed": 0,
            "saved": 0,
            "skipped": 0,
            "failed": 0,
        }

        has_native_parser = hasattr(parser, "parse_exhibition_page") and callable(
            parser.parse_exhibition_page
        )
        if has_native_parser:
            logger.info(
                f"[{parser.source}] Parser provides native page extraction; LLM step will be skipped."
            )

        processed_count = 0
        for url in urls:
            if limit is not None and processed_count >= limit:
                logger.info(f"Reached limit of {limit} pages. Stopping.")
                break

            logger.info(f"Processing: {url}")

            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    logger.info(f"-> Skip: already in DB (ID: {existing['id']})")
                    stats["skipped"] += 1
                    continue
            elif force and not dry_run:
                logger.info(
                    f"-> Force active: Deleting existing DB entry for URL to ensure clean overwrite: {url}"
                )
                self.db.delete_exhibition_by_url(url)

            try:
                parsed_data = None

                # 1. Try native structured extraction if available
                if has_native_parser:
                    parsed_data = parser.parse_exhibition_page(self.client, url)
                    if parsed_data:
                        logger.info(f"[{parser.source}] Native extraction succeeded for {url}")

                # 2. Fall back to LLM pipeline
                if not parsed_data:
                    if getattr(parser, "use_curl_cffi", False):
                        from curl_cffi import requests as curl_requests

                        response = curl_requests.get(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                                "Accept-Language": "en-US,en;q=0.9",
                            },
                            impersonate="chrome124",
                            timeout=30,
                        )
                        response.raise_for_status()
                        page_html = response.text
                    else:
                        try:
                            for attempt in Retrying(
                                stop=stop_after_attempt(3),
                                wait=wait_exponential(multiplier=1, min=1, max=10),
                                retry=retry_if_exception(_is_retryable_http_error),
                                reraise=True,
                            ):
                                with attempt:
                                    response = self.client.get(
                                        url, timeout=getattr(parser, "request_timeout", 60.0)
                                    )
                                    response.raise_for_status()
                            page_html = response.text
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == 403:
                                logger.warning(f"HTTP 403 for {url}, trying Scrapling fallback...")
                                try:
                                    from scrapling import Fetcher

                                    scrapling_resp = Fetcher().get(url, timeout=30)
                                    page_html = scrapling_resp.html_content
                                except Exception as se:
                                    logger.error(f"Scrapling fallback failed for {url}: {se}")
                                    raise
                            else:
                                raise

                    if len(page_html) > MAX_HTML_SIZE:
                        logger.warning(
                            f"HTML response for {url} exceeds {MAX_HTML_SIZE} bytes ({len(page_html)}). Skipping."
                        )
                        stats["failed"] += 1
                        continue

                    clean_text = parser.clean_html(page_html)

                    if not clean_text or len(clean_text.strip()) < 100:
                        logger.warning(f"Content too short/empty for {url}. Skipping.")
                        stats["failed"] += 1
                        continue

                    logger.info(f"Sending {len(clean_text)} chars to LLM...")
                    parsed_data = self.parser.parse_exhibition_text(
                        clean_text, parser.source, parser.city
                    )

                    if not parsed_data:
                        logger.error(f"-> LLM parsing failed for: {url}")
                        stats["failed"] += 1
                        continue

                    # Extract and attach image links deterministically (saves disk & tokens)
                    image_urls = extract_images_from_html(response.text, url, max_images=8)
                    parsed_data["images"] = json.dumps(image_urls)

                if parsed_data and "images" not in parsed_data:
                    parsed_data["images"] = "[]"

                # Enrich with parser metadata
                parsed_data["source"] = parser.source
                parsed_data["url"] = url
                parsed_data["parser_key"] = getattr(parser, "parser_key", "")
                parsed_data["institution_type"] = getattr(parser, "institution_type", "museum")
                if not parsed_data.get("city"):
                    parsed_data["city"] = parser.city

                # Attach category tags if cached in parser
                if hasattr(parser, "_url_tags") and url in parser._url_tags:
                    parsed_data["tags"] = parser._url_tags[url]
                else:
                    parsed_data["tags"] = "[]"

                stats["parsed"] += 1
                processed_count += 1

                if dry_run:
                    logger.info(
                        f"[DRY-RUN] '{parsed_data['title']}': {len(parsed_data.get('artworks', []))} artworks extracted."
                    )
                    stats["saved"] += 1
                else:
                    ex_id = self.db.insert_exhibition(parsed_data)
                    if ex_id:
                        stats["saved"] += 1
                    else:
                        stats["failed"] += 1

            except Exception as e:
                logger.error(f"Error processing {url}: {e}", exc_info=True)
                stats["failed"] += 1

        logger.info(f"Done: '{parser.source}' | {stats}")
        return stats

    async def _scrape_html_async(
        self,
        parser,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Async concurrent HTML scraping pipeline. URL discovery is synchronous;
        detail page fetching and LLM parsing run under asyncio.Semaphore."""
        # Playwright Sync API cannot run inside asyncio loop — use thread pool
        if getattr(parser, "use_playwright", False):
            urls = await asyncio.to_thread(
                parser.get_exhibition_urls, self.client, since_year=since_year
            )
        else:
            urls = parser.get_exhibition_urls(self.client, since_year=since_year)
        if not urls:
            logger.warning(f"No exhibition URLs discovered for {parser.source}.")
            return {
                "site": parser.source,
                "discovered": 0,
                "parsed": 0,
                "saved": 0,
                "skipped": 0,
                "failed": 0,
            }

        stats = {
            "site": parser.source,
            "discovered": len(urls),
            "parsed": 0,
            "saved": 0,
            "skipped": 0,
            "failed": 0,
        }

        has_native_parser = hasattr(parser, "parse_exhibition_page") and callable(
            parser.parse_exhibition_page
        )
        if has_native_parser:
            logger.info(
                f"[{parser.source}] Parser provides native page extraction; LLM step will be skipped."
            )

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
                            async with self._stats_lock:
                                stats["skipped"] += 1
                            return
                    elif force and not dry_run:
                        logger.info(
                            f"-> Force active: Deleting existing DB entry for URL to ensure clean overwrite: {url}"
                        )
                        await asyncio.to_thread(self.db.delete_exhibition_by_url, url)

                    parsed_data = None

                    if has_native_parser:
                        if getattr(parser, "use_playwright", False):
                            parsed_data = await asyncio.to_thread(
                                parser.parse_exhibition_page, self.client, url
                            )
                        else:
                            parsed_data = parser.parse_exhibition_page(self.client, url)
                        if parsed_data:
                            logger.info(f"[{parser.source}] Native extraction succeeded for {url}")

                    if not parsed_data:
                        async for attempt in AsyncRetrying(
                            stop=stop_after_attempt(3),
                            wait=wait_exponential(multiplier=1, min=1, max=10),
                            retry=retry_if_exception(_is_retryable_http_error),
                            reraise=True,
                        ):
                            with attempt:
                                response = await self.async_client.get(
                                    url, timeout=getattr(parser, "request_timeout", 60.0)
                                )
                                response.raise_for_status()
                        html_text = response.text

                        if len(html_text) > MAX_HTML_SIZE:
                            logger.warning(
                                f"HTML response for {url} exceeds {MAX_HTML_SIZE} bytes ({len(html_text)}). Skipping."
                            )
                            async with self._stats_lock:
                                stats["failed"] += 1
                            return

                        clean_text = parser.clean_html(html_text)
                        if not clean_text or len(clean_text.strip()) < 100:
                            logger.warning(f"Content too short/empty for {url}. Skipping.")
                            async with self._stats_lock:
                                stats["failed"] += 1
                            return

                        logger.info(f"Sending {len(clean_text)} chars to LLM (async)...")
                        parsed_data = await self.parser.parse_exhibition_text_async(
                            clean_text, parser.source, parser.city
                        )
                        if not parsed_data:
                            logger.error(f"-> LLM parsing failed for: {url}")
                            async with self._stats_lock:
                                stats["failed"] += 1
                            return

                    parsed_data["source"] = parser.source
                    parsed_data["url"] = url
                    parsed_data["parser_key"] = getattr(parser, "parser_key", "")
                    parsed_data["institution_type"] = getattr(parser, "institution_type", "museum")
                    if not parsed_data.get("city"):
                        parsed_data["city"] = parser.city

                    async with self._stats_lock:
                        stats["parsed"] += 1

                    if dry_run:
                        logger.info(
                            f"[DRY-RUN] '{parsed_data['title']}': {len(parsed_data.get('artworks', []))} artworks extracted."
                        )
                        async with self._stats_lock:
                            stats["saved"] += 1
                    else:
                        ex_id = await asyncio.to_thread(self.db.insert_exhibition, parsed_data)
                        if ex_id:
                            async with self._stats_lock:
                                stats["saved"] += 1
                        else:
                            async with self._stats_lock:
                                stats["failed"] += 1

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}", exc_info=True)
                    async with self._stats_lock:
                        stats["failed"] += 1

        await asyncio.gather(*[asyncio.create_task(_process_one(url)) for url in target_urls])
        logger.info(f"[ASYNC] Done: '{parser.source}' | {stats}")
        return stats

    def _scrape_csv(
        self,
        parser,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Generic CSV pipeline for parsers with get_csv_exhibitions()."""
        logger.info(f"[{parser.source}] Using CSV mode (no LLM required).")

        exhibitions = parser.get_csv_exhibitions(since_year=since_year)

        stats = {
            "site": parser.source,
            "discovered": len(exhibitions),
            "parsed": len(exhibitions),
            "saved": 0,
            "skipped": 0,
            "failed": 0,
        }

        processed_count = 0
        for ex_data in exhibitions:
            if limit is not None and processed_count >= limit:
                logger.info(f"[{parser.source}] Reached limit of {limit} records. Stopping.")
                break

            url = ex_data.get("url", "")
            ex_data["parser_key"] = getattr(parser, "parser_key", "")
            ex_data["institution_type"] = getattr(parser, "institution_type", "museum")

            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    stats["skipped"] += 1
                    continue

            if dry_run:
                logger.info(
                    f"[{parser.source}][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})"
                )
                stats["saved"] += 1
            else:
                ex_id = self.db.insert_exhibition(ex_data)
                if ex_id:
                    stats["saved"] += 1
                else:
                    stats["failed"] += 1

            processed_count += 1

        logger.info(f"[{parser.source}] Done | {stats}")
        return stats

    def _scrape_api(
        self,
        parser,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Generic pipeline for API/SPARQL parsers with get_api_exhibitions()."""
        logger.info(f"[{parser.source}] Using REST/API mode (no LLM required).")

        exhibitions = parser.get_api_exhibitions(since_year=since_year, limit=limit)

        stats = {
            "site": parser.source,
            "discovered": len(exhibitions),
            "parsed": len(exhibitions),
            "saved": 0,
            "skipped": 0,
            "failed": 0,
        }

        for ex_data in exhibitions:
            url = ex_data.get("url", "")
            ex_data["parser_key"] = getattr(parser, "parser_key", "")
            ex_data["institution_type"] = getattr(parser, "institution_type", "museum")

            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    stats["skipped"] += 1
                    continue

            if dry_run:
                logger.info(
                    f"[{parser.source}][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})"
                )
                stats["saved"] += 1
            else:
                ex_id = self.db.insert_exhibition(ex_data)
                if ex_id:
                    stats["saved"] += 1
                else:
                    stats["failed"] += 1

        logger.info(f"[{parser.source}] Done | {stats}")
        return stats

    def _scrape_artwork_only(
        self,
        parser,
        limit: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> dict[str, Any]:
        """Pipeline for artwork-only parsers (NGA, etc.).

        Creates a synthetic 'Permanent Collection' exhibition record and attaches
        artworks as children, preserving the relational model.
        """
        logger.info(f"[{parser.source}] Using artwork-only mode (no exhibitions, collection only).")

        artworks = parser.get_csv_artworks(since_year=since_year, limit=limit)
        if not artworks:
            logger.warning(f"[{parser.source}] No artworks loaded.")
            return {
                "site": parser.source,
                "discovered": 0,
                "parsed": 0,
                "saved": 0,
                "skipped": 0,
                "failed": 0,
            }

        synthetic_url = f"https://auto-curation.internal/collection/{getattr(parser, 'parser_key', parser.source.lower().replace(' ', '-'))}"

        synthetic_ex = {
            "source": parser.source,
            "title": f"{parser.source} Permanent Collection",
            "preface": f"Selected works from the {parser.source} collection.",
            "concept": None,
            "curators": [],
            "start_date": None,
            "end_date": None,
            "location": parser.source,
            "city": parser.city,
            "url": synthetic_url,
            "parser_key": getattr(parser, "parser_key", ""),
            "institution_type": getattr(parser, "institution_type", "museum"),
            "artworks": artworks,
        }

        stats = {
            "site": parser.source,
            "discovered": len(artworks),
            "parsed": len(artworks),
            "saved": 0,
            "skipped": 0,
            "failed": 0,
        }

        if not force and not dry_run:
            existing = self.db.get_exhibition_by_url(synthetic_url)
            if existing:
                logger.info(
                    f"[{parser.source}] Synthetic collection already in DB (ID: {existing['id']}). Skipping."
                )
                stats["skipped"] = 1
                return stats

        if dry_run:
            logger.info(
                f"[{parser.source}][DRY-RUN] Would insert synthetic collection with {len(artworks)} artworks."
            )
            stats["saved"] = 1
        else:
            ex_id = self.db.insert_exhibition(synthetic_ex)
            if ex_id:
                stats["saved"] = 1
                logger.info(
                    f"[{parser.source}] Inserted synthetic collection (ID: {ex_id}) with {len(artworks)} artworks."
                )
            else:
                stats["failed"] = 1

        return stats

    def scrape_all_sites(
        self,
        limit_per_site: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Runs the scraper for all registered contemporary art institutions."""
        results = []
        logger.info(f"Starting bulk scraper for all {len(SITES)} registered institutions.")
        for site_key in SITES.keys():
            res = self.scrape_site(
                site_key, limit=limit_per_site, force=force, dry_run=dry_run, since_year=since_year
            )
            results.append(res)
        return results

    async def ascrape_all_sites(
        self,
        limit_per_site: int | None = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Async concurrent version: scrapes all HTML-based institutions in parallel."""
        html_site_keys = [
            k
            for k, p in SITES.items()
            if getattr(p, "strategy", ParserStrategy.HTML_LLM) == ParserStrategy.HTML_LLM
        ]
        logger.info(
            f"[ASYNC] Starting bulk scraper for {len(html_site_keys)} HTML-based institutions."
        )

        async def _scrape_one(site_key: str) -> dict[str, Any]:
            return await self.ascrape_site(
                site_key, limit=limit_per_site, force=force, dry_run=dry_run, since_year=since_year
            )

        results = await asyncio.gather(
            *[asyncio.create_task(_scrape_one(k)) for k in html_site_keys]
        )

        other_keys = [k for k in SITES if k not in html_site_keys]
        for site_key in other_keys:
            res = self.scrape_site(
                site_key, limit=limit_per_site, force=force, dry_run=dry_run, since_year=since_year
            )
            results.append(res)

        return results

    def close(self):
        """Closes any network resources (sync and async clients)."""
        self.client.close()
        try:
            # Close async client synchronously using a temporary event loop
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.async_client.aclose())
            loop.close()
        except Exception:
            pass

    async def aclose(self):
        """Async close: shuts down both sync and async HTTP clients."""
        self.client.close()
        await self.async_client.aclose()
