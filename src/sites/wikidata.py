"""
Wikidata SPARQL Parser for European Museum Exhibitions.

Uses Wikidata's public SPARQL endpoint to fetch structured exhibition data
from major European art institutions. No API key required.

Endpoint: https://query.wikidata.org/sparql
"""

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import List, Optional, Dict, Any

logger = logging.getLogger("auto_curation.sites.wikidata")

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/sparql-results+json",
}

# Major European art museums with Wikidata QIDs
EUROPEAN_MUSEUM_QIDS = [
    ("Q19675", "Louvre", "Paris"),
    ("Q178065", "Centre Pompidou", "Paris"),
    ("Q189826", "Tate Modern", "London"),
    ("Q190804", "Rijksmuseum", "Amsterdam"),
    ("Q2501625", "Stedelijk Museum Amsterdam", "Amsterdam"),
    ("Q224124", "Van Gogh Museum", "Amsterdam"),
    ("Q51252", "Uffizi", "Florence"),
    ("Q160112", "Museo del Prado", "Madrid"),
    ("Q180788", "National Gallery", "London"),
    ("Q23402", "Musée d'Orsay", "Paris"),
    ("Q28450", "Guggenheim Museum Bilbao", "Bilbao"),
    ("Q1474887", "Tate Britain", "London"),
    ("Q151849", "Serpentine Galleries", "London"),
    ("Q1052661", "Palais de Tokyo", "Paris"),
    ("Q1471477", "Mori Art Museum", "Tokyo"),
    ("Q89568", "M+ Museum", "Hong Kong"),
]


class WikidataParser:
    """Wikidata SPARQL Parser for global museum exhibitions.

    Fetches exhibition records from Wikidata's public SPARQL endpoint.
    Covers major European institutions and selected global museums.
    """
    source = "Wikidata"
    city = "Various"
    list_url = WIKIDATA_SPARQL_URL

    def get_exhibition_urls(self, client, since_year: Optional[int] = None) -> List[str]:
        """Compatibility stub — Wikidata uses get_api_exhibitions() directly."""
        return []

    def _build_sparql_query(self, since_year: Optional[int] = None, limit: Optional[int] = None) -> str:
        """Builds a SPARQL query to fetch exhibitions from configured museums."""
        museum_values = " ".join([f"wd:{qid}" for qid, _, _ in EUROPEAN_MUSEUM_QIDS])

        since_filter = ""
        if since_year:
            since_filter = f'FILTER(YEAR(?start) >= {since_year})'

        limit_clause = ""
        if limit:
            limit_clause = f"LIMIT {limit}"

        query = f"""
        SELECT ?exhibition ?exhibitionLabel ?museum ?museumLabel ?start ?end ?cityLabel
        WHERE {{
            VALUES ?museum {{ {museum_values} }}
            ?exhibition wdt:P31 wd:Q464980 .
            ?exhibition wdt:P276 ?museum .
            ?exhibition wdt:P580 ?start .
            OPTIONAL {{ ?exhibition wdt:P582 ?end }}
            OPTIONAL {{ ?museum wdt:P131 ?city }}
            {since_filter}
            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "en,fr,de,it,es,zh" .
            }}
        }}
        ORDER BY DESC(?start)
        {limit_clause}
        """
        return query

    def get_api_exhibitions(
        self,
        since_year: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetches exhibitions from Wikidata SPARQL endpoint.

        Args:
            since_year: Only return exhibitions from this year onwards.
            limit: Max number of exhibitions to fetch.

        Returns:
            List of structured exhibition dicts ready for DB insertion.
        """
        query = self._build_sparql_query(since_year=since_year, limit=limit)
        exhibitions = []

        logger.info(f"[Wikidata] Querying SPARQL (since_year={since_year}, limit={limit})")

        try:
            data = urllib.parse.urlencode({"query": query}).encode()
            req = urllib.request.Request(
                WIKIDATA_SPARQL_URL,
                data=data,
                headers={
                    "User-Agent": HEADERS["User-Agent"],
                    "Accept": HEADERS["Accept"],
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            bindings = data.get("results", {}).get("bindings", [])
            logger.info(f"[Wikidata] Received {len(bindings)} results")

            museum_map = {f"http://www.wikidata.org/entity/{qid}": (name, city)
                          for qid, name, city in EUROPEAN_MUSEUM_QIDS}

            for binding in bindings:
                ex_uri = binding.get("exhibition", {}).get("value", "")
                ex_id = ex_uri.split("/")[-1] if ex_uri else ""

                title = binding.get("exhibitionLabel", {}).get("value", "")
                if not title or title.startswith("Q"):
                    # Fallback to URI last segment if label missing
                    title = ex_id or "Untitled Exhibition"

                museum_uri = binding.get("museum", {}).get("value", "")
                museum_name = binding.get("museumLabel", {}).get("value", "")
                city_name = binding.get("cityLabel", {}).get("value", "")

                if not museum_name and museum_uri in museum_map:
                    museum_name = museum_map[museum_uri][0]
                if not city_name and museum_uri in museum_map:
                    city_name = museum_map[museum_uri][1]

                start_raw = binding.get("start", {}).get("value", "")
                end_raw = binding.get("end", {}).get("value", "")

                start_date = start_raw[:10] if start_raw else None
                end_date = end_raw[:10] if end_raw else None

                ex_url = f"https://www.wikidata.org/wiki/{ex_id}"

                exhibitions.append({
                    "source": museum_name or self.source,
                    "title": title,
                    "preface": None,
                    "concept": None,
                    "curators": [],
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": museum_name or self.source,
                    "city": city_name or "",
                    "url": ex_url,
                    "artworks": [],
                })

            time.sleep(0.5)  # Polite rate limiting for Wikidata

        except Exception as e:
            logger.error(f"[Wikidata] SPARQL query failed: {e}", exc_info=True)

        logger.info(f"[Wikidata] Done. Total exhibitions fetched: {len(exhibitions)}")
        return exhibitions

    def clean_html(self, html: str) -> str:
        return html
