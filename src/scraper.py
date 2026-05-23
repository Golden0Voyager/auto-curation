import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import date
from src.database import ExhibitionDatabase
from src.llm_parser import LLMExhibitionParser
from src.sites import SITES
from src.sites.moma import MoMAParser
from src.sites.aic import AICParser
from src.sites.nga import NGAParser

logger = logging.getLogger("auto_curation.scraper")


class ExhibitionScraper:
    """Orchestrates the entire scraping pipeline: URL discovery, HTML cleaning,
    LLM metadata extraction, and database persistence.
    
    Supports three scraping strategies:
    1. Standard HTML scraping (most sites)
    2. Multi-URL archive scraping (M+, Serpentine, Mori with historical URLs)
    3. GitHub CSV dataset ingestion (MoMA open data)
    """
    
    def __init__(self, db_path: str = "exhibitions.db"):
        self.db = ExhibitionDatabase(db_path)
        self.parser = LLMExhibitionParser()
        self.client = httpx.Client(headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }, follow_redirects=True, timeout=30.0)

    def scrape_site(
        self,
        site_key: str,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Scrapes contemporary art exhibitions from a single registered institution.
        
        Args:
            site_key: Identifier key in SITES (e.g. 'moma', 'tate')
            limit: Maximum number of detail pages to parse for this run
            force: Parse and update even if URL already exists in database
            dry_run: Fetch and parse but do not write to database
            since_year: Only collect exhibitions from this year onwards (where supported)
            
        Returns:
            Dictionary containing run summary statistics.
        """
        if site_key not in SITES:
            logger.error(f"Site key '{site_key}' is not registered.")
            return {"error": f"Site '{site_key}' not found"}
            
        parser = SITES[site_key]
        logger.info(f"Starting scrape for '{parser.source}' (City: {parser.city}){' | since=' + str(since_year) if since_year else ''}")

        # === Special handling: MoMA uses GitHub CSV dataset ===
        if isinstance(parser, MoMAParser):
            return self._scrape_moma_csv(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

        # === Special handling: AIC uses REST API (no LLM, no HTML) ===
        if isinstance(parser, AICParser):
            return self._scrape_aic_api(parser, limit=limit, force=force, dry_run=dry_run, since_year=since_year)

        # === Standard HTML scraping for all other sites ===
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
        
        processed_count = 0
        for url in urls:
            if limit is not None and processed_count >= limit:
                logger.info(f"Reached limit of {limit} pages. Stopping.")
                break
                
            logger.info(f"Processing: {url}")
            
            # Smart token saver: skip already-scraped URLs
            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    logger.info(f"-> Skip: already in DB (ID: {existing['id']})")
                    stats["skipped"] += 1
                    continue
            
            try:
                response = self.client.get(url)
                response.raise_for_status()
                
                clean_text = parser.clean_html(response.text)
                
                if not clean_text or len(clean_text.strip()) < 100:
                    logger.warning(f"Content too short/empty for {url}. Skipping.")
                    stats["failed"] += 1
                    continue
                
                logger.info(f"Sending {len(clean_text)} chars to Gemini...")
                parsed_data = self.parser.parse_exhibition_text(clean_text, parser.source, parser.city)
                
                if not parsed_data:
                    logger.error(f"-> LLM parsing failed for: {url}")
                    stats["failed"] += 1
                    continue
                
                parsed_data["source"] = parser.source
                parsed_data["url"] = url
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

    def _scrape_moma_csv(
        self,
        parser: MoMAParser,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Special pipeline for MoMA GitHub open dataset (CSV-based, no LLM needed).
        
        MoMA's CSV data is already structured, so we skip the LLM parsing step entirely.
        This saves significant API costs for historical data ingestion.
        """
        logger.info(f"[MoMA] Using GitHub open dataset mode (no LLM required).")
        
        exhibitions = parser.get_csv_exhibitions(since_year=since_year)
        
        stats = {
            "site": parser.source,
            "discovered": len(exhibitions),
            "parsed": len(exhibitions),  # CSV is already structured
            "saved": 0,
            "skipped": 0,
            "failed": 0
        }
        
        processed_count = 0
        for ex_data in exhibitions:
            if limit is not None and processed_count >= limit:
                logger.info(f"[MoMA] Reached limit of {limit} records. Stopping.")
                break
            
            url = ex_data.get("url", "")
            
            # Deduplication check
            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    stats["skipped"] += 1
                    continue
            
            if dry_run:
                logger.info(f"[MoMA][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})")
                stats["saved"] += 1
            else:
                ex_id = self.db.insert_exhibition(ex_data)
                if ex_id:
                    stats["saved"] += 1
                else:
                    stats["failed"] += 1
            
            processed_count += 1
        
        logger.info(f"[MoMA] Done | {stats}")
        return stats

    def _scrape_aic_api(
        self,
        parser: AICParser,
        limit: Optional[int] = None,
        force: bool = False,
        dry_run: bool = False,
        since_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Special pipeline for AIC REST API (JSON-based, no LLM needed).

        AIC's API returns structured JSON, so we skip the LLM parsing step entirely.
        """
        logger.info(f"[AIC] Using REST API mode (no LLM required).")

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

            # Deduplication check
            if not force and not dry_run:
                existing = self.db.get_exhibition_by_url(url)
                if existing:
                    stats["skipped"] += 1
                    continue

            if dry_run:
                logger.info(f"[AIC][DRY-RUN] Would insert: '{ex_data['title']}' ({ex_data['start_date']})")
                stats["saved"] += 1
            else:
                ex_id = self.db.insert_exhibition(ex_data)
                if ex_id:
                    stats["saved"] += 1
                else:
                    stats["failed"] += 1

        logger.info(f"[AIC] Done | {stats}")
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

    def close(self):
        """Closes any network resources."""
        self.client.close()
