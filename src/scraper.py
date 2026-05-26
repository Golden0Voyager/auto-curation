import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import date
from src.database import ExhibitionDatabase
from src.llm_parser import LLMExhibitionParser
from src.cache import LLMResponseCache
from src.sites import SITES
from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.scraper")


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
        self.client = httpx.Client(headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }, follow_redirects=True, timeout=30.0)
        self.max_concurrency = max_concurrency

    def scrape_site(
        self,
        site_key: str,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Scrapes exhibitions from a single registered institution.

        Routes to the appropriate pipeline based on the parser's strategy.
        """
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}

        parser = SITES[site_key]
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
        return handler(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

    async def ascrape_site(
        self,
        site_key: str,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Asynchronous version: concurrent scraping for a single institution."""
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}

        parser = SITES[site_key]
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
        return await self._scrape_html_async(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

    # ------------------------------------------------------------------
    # Strategy handlers
    # ------------------------------------------------------------------

    def _scrape_html(
        self,
        parser,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Standard HTML scraping pipeline: discover URLs, clean HTML, LLM parse.

        If a parser implements ``parse_exhibition_page(client, url)`` and returns
        a dict, that structured data is used directly and the LLM step is skipped.
        """
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

            try:
                parsed_data = None

                # 1. Try native structured extraction if available
                if has_native_parser:
                    parsed_data = parser.parse_exhibition_page(self.client, url)
                    if parsed_data:
                        logger.info(f"[{parser.source}] Native extraction succeeded for {url}")

                # 2. Fall back to LLM pipeline
                if not parsed_data:
                    response = self.client.get(url)
                    response.raise_for_status()

                    clean_text = parser.clean_html(response.text)

                    if not clean_text or len(clean_text.strip()) < 100:
                        logger.warning(f"Content too short/empty for {url}. Skipping.")
                        stats["failed"] += 1
                        continue

                    logger.info(f"Sending {len(clean_text)} chars to LLM...")
                    parsed_data = self.parser.parse_exhibition_text(clean_text, parser.source, parser.city)

                    if not parsed_data:
                        logger.error(f"-> LLM parsing failed for: {url}")
                        stats["failed"] += 1
                        continue

                # Enrich with parser metadata
                parsed_data["source"] = parser.source
                parsed_data["url"] = url
                parsed_data["parser_key"] = getattr(parser, "parser_key", "")
                parsed_data["institution_type"] = getattr(parser, "institution_type", "museum")
                if not parsed_data.get("city"):
                    parsed_data["city"] = parser.city

                stats["parsed"] += 1
                processed_count += 1

                if dry_run:
                    logger.info(f"[DRY-RUN] '{parsed_data['title']}': {len(parsed_data.get('artworks', []))} artworks extracted.")
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
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Async concurrent HTML scraping pipeline. URL discovery is synchronous;
        detail page fetching and LLM parsing run under asyncio.Semaphore."""
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

                    if has_native_parser:
                        parsed_data = parser.parse_exhibition_page(self.client, url)
                        if parsed_data:
                            logger.info(f"[{parser.source}] Native extraction succeeded for {url}")

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

                    parsed_data["source"] = parser.source
                    parsed_data["url"] = url
                    parsed_data["parser_key"] = getattr(parser, "parser_key", "")
                    parsed_data["institution_type"] = getattr(parser, "institution_type", "museum")
                    if not parsed_data.get("city"):
                        parsed_data["city"] = parser.city

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

    def _scrape_csv(
        self,
        parser,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generic CSV pipeline for parsers with get_csv_exhibitions()."""
        logger.info(f"[{parser.source}] Using CSV mode (no LLM required).")

        exhibitions = parser.get_csv_exhibitions(since_year=since_year)

        stats = {
            "site": parser.source,
            "discovered": len(exhibitions),
            "parsed": len(exhibitions),
            "saved": 0,
            "skipped": 0,
            "failed": 0
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
                logger.info(f"[{parser.source}][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})")
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
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generic pipeline for API/SPARQL parsers with get_api_exhibitions()."""
        logger.info(f"[{parser.source}] Using REST/API mode (no LLM required).")

        exhibitions = parser.get_api_exhibitions(since_year=since_year, limit=limit)

        stats = {
            "site": parser.source,
            "discovered": len(exhibitions),
            "parsed": len(exhibitions),
            "saved": 0,
            "skipped": 0,
            "failed": 0
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
                logger.info(f"[{parser.source}][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})")
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
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Pipeline for artwork-only parsers (NGA, etc.).

        Creates a synthetic 'Permanent Collection' exhibition record and attaches
        artworks as children, preserving the relational model.
        """
        logger.info(f"[{parser.source}] Using artwork-only mode (no exhibitions, collection only).")

        artworks = parser.get_csv_artworks(since_year=since_year, limit=limit)
        if not artworks:
            logger.warning(f"[{parser.source}] No artworks loaded.")
            return {"site": parser.source, "discovered": 0, "parsed": 0, "saved": 0, "skipped": 0, "failed": 0}

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
            "failed": 0
        }

        if not force and not dry_run:
            existing = self.db.get_exhibition_by_url(synthetic_url)
            if existing:
                logger.info(f"[{parser.source}] Synthetic collection already in DB (ID: {existing['id']}). Skipping.")
                stats["skipped"] = 1
                return stats

        if dry_run:
            logger.info(f"[{parser.source}][DRY-RUN] Would insert synthetic collection with {len(artworks)} artworks.")
            stats["saved"] = 1
        else:
            ex_id = self.db.insert_exhibition(synthetic_ex)
            if ex_id:
                stats["saved"] = 1
                logger.info(f"[{parser.source}] Inserted synthetic collection (ID: {ex_id}) with {len(artworks)} artworks.")
            else:
                stats["failed"] = 1

        return stats

    def scrape_all_sites(
        self,
        limit_per_site: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Runs the scraper for all registered contemporary art institutions."""
        results = []
        logger.info(f"Starting bulk scraper for all {len(SITES)} registered institutions.")
        for site_key in SITES.keys():
            res = self.scrape_site(
                site_key,
                limit=limit_per_site,
                force=force,
                dry_run=dry_run,
                since_year=since_year
            )
            results.append(res)
        return results

    async def ascrape_all_sites(
        self,
        limit_per_site: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Async concurrent version: scrapes all HTML-based institutions in parallel."""
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

    def close(self):
        """Closes any network resources."""
        self.client.close()
