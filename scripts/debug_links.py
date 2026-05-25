#!/usr/bin/env python3
"""Debug script: fetch listing page and print all links for diagnosis."""

import sys
import httpx
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# Sites to diagnose with their listing URLs and current patterns
SITES = [
    ("met", "https://www.metmuseum.org/exhibitions", [r"/exhibitions/listings/"]),
    ("pompidou", "https://www.centrepompidou.fr/en/program/exhibitions", [r"/en/program/exhibitions/"]),
    ("gwangju_biennale", "https://gb.or.kr/en", [r"gb\.or\.kr/en/[^/]+"]),
    ("lyon_biennale", "https://www.biennalede-lyon.com", [r"biennalede-lyon\.com/[^/]+"]),
    ("palaistokyo", "https://palaisdetokyo.com/en/exhibitions/", [r"palaisdetokyo\.com/en/exhibitions/[^/]+"]),
    ("sharjah_biennale", "https://sharjahart.org/sharjah-biennial", [r"sharjahart\.org/sharjah-biennial/[^/]+"]),
    ("taipei_biennale", "https://www.tfam.museum/Exhibition/Exhibition.aspx?ddlLang=en", [r"tfam\.museum/Exhibition/ExhibitionDetail\.aspx"]),
    ("whitney_biennial", "https://whitney.org/whitney-biennial", [r"whitney\.org/[^/]+"]),
    ("mmcaseoul", "https://www.mmca.go.kr/exhibitions/progress.do", [r"mmca\.go\.kr/exhibitions/progress/[^/]+"]),
    ("leeum", "https://www.leeum.org/en/exhibitions", [r"leeum\.org/en/exhibitions/[^/]+"]),
    ("mca_australia", "https://www.mca.com.au/exhibitions/", [r"mca\.com\.au/exhibitions/[^/]+"]),
    ("pinakothek", "https://www.pinakothek.de/en/exhibitions", [r"pinakothek\.de/en/exhibitions/[^/]+"]),
    ("new_museum", "https://www.newmuseum.org/exhibitions", [r"newmuseum\.org/exhibitions/[^/]+"]),
    ("momat", "https://www.momat.go.jp/exhibitions", [r"momat\.go\.jp/exhibitions/[^/]+"]),
    ("flv", "https://www.fondationlouisvuitton.fr/en.html", [r"fondationlouisvuitton\.fr/en/exhibitions/[^/]+"]),
]


def diagnose(site: str, list_url: str, patterns: list):
    print(f"\n{'='*60}")
    print(f"SITE: {site}")
    print(f"URL:  {list_url}")
    print(f"Patterns: {patterns}")
    print("-" * 60)

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            resp = client.get(list_url)
            print(f"Status: {resp.status_code}")
            soup = BeautifulSoup(resp.text, "html.parser")

            links = []
            matched = []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                full = urljoin(list_url, href)
                links.append((href, full))
                for p in patterns:
                    if re.search(p, href) or re.search(p, full):
                        matched.append(full)

            print(f"Total <a> tags: {len(links)}")
            print(f"Matched: {len(set(matched))}")

            # Show first 15 links
            print("\nFirst 15 links:")
            for href, full in links[:15]:
                flag = "✓" if any(re.search(p, href) or re.search(p, full) for p in patterns) else " "
                print(f"  [{flag}] {href[:80]}")

            if matched:
                print("\nMatched URLs:")
                for m in list(set(matched))[:5]:
                    print(f"  -> {m}")
            else:
                # Try to suggest patterns from actual links
                print("\nNo matches. Looking for exhibition-like paths...")
                candidates = []
                for href, full in links:
                    path = full.replace(list_url, "").lstrip("/")
                    if any(k in href.lower() for k in ["exhib", "show", "event", "program"]):
                        candidates.append(href)
                for c in list(set(candidates))[:10]:
                    print(f"  ? {c[:80]}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    for site, url, patterns in SITES:
        diagnose(site, url, patterns)
