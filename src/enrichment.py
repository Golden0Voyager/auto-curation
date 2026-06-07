"""Exhibition enrichment helpers for synthesizing missing fields from existing data.

Tier 2: CSV/API source synthesis — zero network requests, zero LLM cost.
"""

from typing import Any


def synthesize_concept_moma(title: str, artworks: list[dict[str, Any]]) -> str:
    """Synthesize a basic concept from MoMA exhibition title + artist list.

    Args:
        title: Exhibition title.
        artworks: List of artwork dicts with 'artist_name' keys.

    Returns:
        A synthesized concept string in Chinese.
    """
    if not title:
        return ""

    artists = []
    seen = set()
    for art in artworks:
        name = art.get("artist_name", "").strip()
        if name and name not in seen:
            artists.append(name)
            seen.add(name)

    if not artists:
        return f"展览《{title}》"

    artist_str = ", ".join(artists[:15])
    if len(artists) > 15:
        artist_str += " 等"

    return f"展览《{title}》展出艺术家包括 {artist_str} 的作品。"


def synthesize_concept_aic(
    title: str,
    preface: str | None,
    artist_titles: list[str],
) -> str:
    """Synthesize a basic concept from AIC exhibition data.

    Args:
        title: Exhibition title.
        preface: Existing preface/short_description (may be None or empty).
        artist_titles: List of artist names from the API.

    Returns:
        A synthesized concept string in Chinese.
    """
    if not title:
        return ""

    # If preface is substantial, use it as the basis for concept
    if preface and len(preface.strip()) >= 50:
        # Truncate and clean
        cleaned = preface.strip().replace("\n", " ")
        return cleaned[:300]

    artists = []
    seen = set()
    for name in artist_titles:
        name = name.strip()
        if name and name not in seen:
            artists.append(name)
            seen.add(name)

    if not artists:
        return f"芝加哥艺术博物馆展览《{title}》"

    artist_str = ", ".join(artists[:15])
    if len(artists) > 15:
        artist_str += " 等"

    return f"芝加哥艺术博物馆展览《{title}》展出艺术家包括 {artist_str} 的作品。"


def synthesize_concept_whitney(
    title: str,
    preface: str | None,
) -> str:
    """Synthesize concept for Whitney exhibitions from preface text.

    Args:
        title: Exhibition title.
        preface: Primary text from Whitney API (may be None).

    Returns:
        A synthesized concept string.
    """
    if not title:
        return ""

    if preface and len(preface.strip()) >= 50:
        cleaned = preface.strip().replace("\n", " ")
        return cleaned[:300]

    return f"Whitney Museum of American Art exhibition: {title}"


def synthesize_concept_generic(
    title: str,
    source: str,
    artist_names: list[str],
) -> str:
    """Generic concept synthesizer for any exhibition with title + artists.

    Args:
        title: Exhibition title.
        source: Institution name.
        artist_names: List of artist names.

    Returns:
        A synthesized concept string.
    """
    if not title:
        return ""

    artists = []
    seen = set()
    for name in artist_names:
        name = name.strip()
        if name and name not in seen:
            artists.append(name)
            seen.add(name)

    if not artists:
        return f"{source} 展览《{title}》"

    artist_str = ", ".join(artists[:15])
    if len(artists) > 15:
        artist_str += " 等"

    return f"{source} 展览《{title}》展出艺术家包括 {artist_str} 的作品。"
