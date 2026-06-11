import logging
import re
from datetime import date
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from src.sites.base import HEADERS, BaseSiteParser

logger = logging.getLogger("auto_curation.sites.serpentine")


class SerpentineParser(BaseSiteParser):
    """Serpentine Galleries - London.

    The archive section is paginated (/whats-on/archive/page/N/).
    We generate archive page URLs up to a defined limit and extract
    real exhibition links from each page.
    """

    source = "Serpentine Galleries"
    city = "London"
    list_url = "https://www.serpentinegalleries.org/whats-on/"

    # Max archive pages to crawl per run (each page ~10 exhibitions)
    # Limit to 20 pages to avoid timeout; use --since to limit further
    MAX_ARCHIVE_PAGES = 20

    link_patterns = [r"serpentinegalleries\.org/whats-on/[a-zA-Z0-9][a-zA-Z0-9_-]+/?$"]

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        """Generate current + archive pagination URLs.

        If since_year is provided and is recent, reduce the number of archive pages.
        Each archive page covers roughly one year, so we limit pages accordingly.
        """
        urls = [self.list_url]

        current_year = date.today().year
        if since_year:
            years_back = max(1, current_year - since_year)
            # Roughly 10 exhibitions/page, ~15 per year for Serpentine
            max_pages = min(years_back * 2, self.MAX_ARCHIVE_PAGES)
        else:
            max_pages = self.MAX_ARCHIVE_PAGES

        # Add archive pagination
        urls.append("https://www.serpentinegalleries.org/whats-on/archive/")
        for page_num in range(2, max_pages + 1):
            urls.append(f"https://www.serpentinegalleries.org/whats-on/archive/page/{page_num}/")

        logger.info(
            f"[Serpentine] Will crawl {len(urls)} pages (including {max_pages} archive pages)."
        )
        return urls

    EVENT_KEYWORDS = [
        "talk",
        "workshop",
        "symposium",
        "seminar",
        "conference",
        "lecture",
        "conversation",
        "screening",
        "film",
        "performance",
        "concert",
        "recital",
        "study-evening",
        "celebration",
        "launch",
        "reading",
        "discussion",
        "panel",
        "gala",
        "dinner",
        "salon",
        "tour",
        "school-visit",
        "podcast",
        "marathon",
        "park-nights",
        "saturday-talks",
        "book-club",
        "study-day",
    ]

    def get_exhibition_urls(self, client: httpx.Client, since_year: int | None = None) -> list[str]:
        """Fetch all pages and extract real exhibition detail URLs.

        Uses CSS card/teaser selectors to group entries, extracts their category type links
        (e.g., ?type=events), and filters out non-exhibition events, index, and archive pages.
        """
        if not hasattr(self, "_url_tags"):
            self._url_tags = {}

        list_urls = self.get_list_urls(since_year=since_year)
        all_found: set[str] = set()
        event_pattern = re.compile(
            r"\b("
            + "|".join(self.EVENT_KEYWORDS)
            + r")s?\b|(-talks|-nights|workshop|symposium|seminar|conference|lecture|conversation|screening|performance|concert|launch|reading|discussion|panel|tour|podcast|marathon)",
            re.IGNORECASE,
        )

        import json

        for list_url in list_urls:
            try:
                response = client.get(list_url, headers=HEADERS, follow_redirects=True)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                # 1. Group by card/teaser container for higher precision
                teasers = soup.find_all("section", class_="teaser")
                if not teasers:
                    teasers = soup.select(".card, .teaser, [class*='teaser'], [class*='card']")

                if teasers:
                    for teaser in teasers:
                        detail_url = None
                        is_event = False
                        card_tags = []

                        # Find the category / type links inside this card
                        for a_tag in teaser.find_all("a", href=True):
                            href = str(a_tag["href"]).strip()
                            full_url = urljoin(list_url, href)

                            # Check if the card is labeled as an event, live art, publication, etc.
                            if "?type=" in full_url:
                                for event_type in [
                                    "events",
                                    "live",
                                    "publication",
                                    "digital",
                                    "education",
                                    "research",
                                ]:
                                    if f"type={event_type}" in full_url:
                                        is_event = True
                                        break

                                # Extract type link text as tags (e.g. "Events", "Live", "Exhibitions")
                                text = a_tag.get_text(strip=True)
                                if text and text not in card_tags:
                                    card_tags.append(text)

                        # Also look for any italicized or meta tag elements directly inside the teaser
                        # (such as elements with classes like card__category, teaser__category, etc.)
                        meta_els = teaser.select(
                            "[class*='category'], [class*='type'], [class*='meta'], [class*='label'], [class*='tag']"
                        )
                        for meta_el in meta_els:
                            if meta_el.name in ["h3", "h4", "p"]:
                                continue
                            text = meta_el.get_text(strip=True)
                            # Split by commas if it has "Events, Live"
                            if text and len(text) < 40:
                                for part in re.split(r",\s*", text):
                                    part_clean = part.strip()
                                    if part_clean and part_clean not in card_tags:
                                        card_tags.append(part_clean)

                        # Clean up tags: remove any long descriptions or number values
                        card_tags = [
                            t
                            for t in card_tags
                            if t and len(t) < 25 and not any(char.isdigit() for char in t)
                        ]

                        # Find the actual detail page link
                        for a_tag in teaser.find_all("a", href=True):
                            href = str(a_tag["href"]).strip()
                            full_url = urljoin(list_url, href)

                            # Must match whats-on detail page pattern and not contain ? (query params) or index pages
                            if re.search(
                                r"serpentinegalleries\.org/whats-on/[a-zA-Z0-9][a-zA-Z0-9_-]+/?$",
                                full_url,
                            ):
                                if (
                                    "?" not in full_url
                                    and "/archive/" not in full_url
                                    and not full_url.endswith("/whats-on/")
                                ):
                                    detail_url = full_url.rstrip("/") + "/"
                                    break

                        # Double-check title or URL against event keyword filters
                        if detail_url:
                            title_el = teaser.find("h3")
                            title_text = title_el.get_text(strip=True) if title_el else ""
                            if event_pattern.search(detail_url) or event_pattern.search(title_text):
                                is_event = True

                            if not is_event:
                                all_found.add(detail_url)
                                # If no tags found, default to "Exhibitions" if not flagged as event
                                if not card_tags:
                                    card_tags = ["Exhibitions"]
                                self._url_tags[detail_url] = json.dumps(
                                    card_tags, ensure_ascii=False
                                )
                else:
                    # 2. Fallback to standard tag parsing if layout changes
                    for a_tag in soup.find_all("a", href=True):
                        href = str(a_tag["href"]).strip()
                        full_url = urljoin(list_url, href)

                        # Must match exhibition pattern
                        if not re.search(
                            r"serpentinegalleries\.org/whats-on/[a-zA-Z0-9][a-zA-Z0-9_-]+/?$",
                            full_url,
                        ):
                            continue



                        # Exclude by keyword
                        title_text = a_tag.get_text(strip=True)
                        if event_pattern.search(full_url) or event_pattern.search(title_text):
                            continue

                        detail_url = full_url.rstrip("/") + "/"
                        all_found.add(detail_url)

                        # Extract fallback tags from parent containers
                        card_tags = ["Exhibitions"]
                        parent = a_tag.find_parent(["div", "section", "article"])
                        if parent:
                            found_fallback = []
                            for tag_a in parent.find_all("a", href=True):
                                if "?type=" in str(tag_a["href"]):
                                    text = tag_a.get_text(strip=True)
                                    if text and text not in found_fallback:
                                        found_fallback.append(text)
                            if found_fallback:
                                card_tags = found_fallback

                        self._url_tags[detail_url] = json.dumps(card_tags, ensure_ascii=False)

            except Exception as e:
                logger.error(f"[Serpentine] Error fetching {list_url}: {e}")
                continue

        urls = sorted(list(all_found))
        logger.info(
            f"[Serpentine] Discovered {len(urls)} real, clean exhibition URLs (filtered out non-exhibition events)."
        )
        return urls
