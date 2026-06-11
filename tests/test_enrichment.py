"""Tests for src/enrichment.py — exhibition concept synthesis functions."""

from src.enrichment import (
    synthesize_concept_aic,
    synthesize_concept_generic,
    synthesize_concept_moma,
    synthesize_concept_whitney,
)

# ---------------------------------------------------------------------------
# synthesize_concept_moma
# ---------------------------------------------------------------------------


def test_moma_empty_title():
    assert synthesize_concept_moma("", []) == ""


def test_moma_no_artists():
    result = synthesize_concept_moma("Test Show", [])
    assert result == "展览《Test Show》"


def test_moma_single_artist():
    result = synthesize_concept_moma("Picasso", [{"artist_name": "Pablo Picasso"}])
    assert "Pablo Picasso" in result
    assert "展览《Picasso》" in result


def test_moma_multiple_artists():
    artworks = [
        {"artist_name": "Andy Warhol"},
        {"artist_name": "Roy Lichtenstein"},
        {"artist_name": "Andy Warhol"},  # duplicate
    ]
    result = synthesize_concept_moma("Pop Art", artworks)
    assert "Andy Warhol" in result
    assert "Roy Lichtenstein" in result
    assert result.count("Andy Warhol") == 1  # no duplicate
    assert "Pop Art" in result


def test_moma_over_15_artists():
    artworks = [{"artist_name": f"Artist {i}"} for i in range(20)]
    result = synthesize_concept_moma("Big Show", artworks)
    assert " 等" in result
    assert "Artist 15" not in result  # truncated
    assert "Artist 14" in result


def test_moma_empty_artist_names():
    artworks = [{"artist_name": ""}, {"artist_name": "  "}, {"artist_name": "Real Artist"}]
    result = synthesize_concept_moma("Mixed", artworks)
    assert "Real Artist" in result
    assert "展览《Mixed》" in result


# ---------------------------------------------------------------------------
# synthesize_concept_aic
# ---------------------------------------------------------------------------


def test_aic_empty_title():
    assert synthesize_concept_aic("", None, []) == ""


def test_aic_substantial_preface():
    long_preface = "X" * 100
    result = synthesize_concept_aic("Title", long_preface, ["Artist A"])
    assert result == long_preface.strip().replace("\n", " ")


def test_aic_preface_too_short():
    short_preface = "short"
    result = synthesize_concept_aic("Title", short_preface, ["Artist A"])
    assert "芝加哥艺术博物馆" in result
    assert "Artist A" in result


def test_aic_no_artists():
    result = synthesize_concept_aic("Masterpieces", None, [])
    assert "芝加哥艺术博物馆展览《Masterpieces》" in result


def test_aic_multiple_artists():
    result = synthesize_concept_aic("Modern Art", None, ["A", "B", "C"])
    assert "A" in result
    assert "B" in result
    assert "C" in result


def test_aic_over_15_artists():
    artists = [f"Artist {i}" for i in range(20)]
    result = synthesize_concept_aic("Large", None, artists)
    assert " 等" in result


def test_aic_preface_trimmed():
    long_preface = "This is a great exhibition." * 30  # >300 chars
    result = synthesize_concept_aic("T", long_preface, [])
    assert len(result) <= 300


# ---------------------------------------------------------------------------
# synthesize_concept_whitney
# ---------------------------------------------------------------------------


def test_whitney_empty_title():
    assert synthesize_concept_whitney("", None) == ""


def test_whitney_no_preface():
    result = synthesize_concept_whitney("Biennial", None)
    assert "Whitney Museum" in result
    assert "Biennial" in result


def test_whitney_short_preface():
    result = synthesize_concept_whitney("Show", "Too short")
    assert "Whitney Museum" in result


def test_whitney_long_preface():
    long_preface = "A" * 100
    result = synthesize_concept_whitney("Title", long_preface)
    assert result == long_preface.strip().replace("\n", " ")


def test_whitney_preface_with_newlines():
    preface = "Line1\nLine2\nLine3" * 30
    result = synthesize_concept_whitney("T", preface)
    assert " " in result  # newlines replaced
    assert len(result) <= 300


# ---------------------------------------------------------------------------
# synthesize_concept_generic
# ---------------------------------------------------------------------------


def test_generic_empty_title():
    assert synthesize_concept_generic("", "Source", []) == ""


def test_generic_no_artists():
    result = synthesize_concept_generic("Show", "Museum X", [])
    assert result == "Museum X 展览《Show》"


def test_generic_with_artists():
    result = synthesize_concept_generic("Group Show", "Tate", ["Alice", "Bob"])
    assert "Alice" in result
    assert "Bob" in result
    assert "Tate" in result


def test_generic_deduplicate():
    result = synthesize_concept_generic("Duplicates", "M", ["X", "X", "Y"])
    assert result.count("X") == 1


def test_generic_whitespace_artists():
    result = synthesize_concept_generic("T", "S", ["  ", "Real"])
    assert "Real" in result
    assert "  , " not in result


def test_generic_over_15():
    artists = [f"P{i}" for i in range(20)]
    result = synthesize_concept_generic("Big", "S", artists)
    assert " 等" in result
