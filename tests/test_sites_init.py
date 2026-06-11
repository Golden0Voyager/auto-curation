"""Tests for src/sites/__init__.py — parser auto-discovery logic."""


def test_sites_module_imports():
    """Verify SITES is a dict with expected keys."""
    from src.sites import SITES

    assert isinstance(SITES, dict)
    assert len(SITES) > 0


def test_known_parsers_are_present():
    """Key parsers should be registered."""
    from src.sites import SITES

    expected_keys = [
        "tate",
        "mplus",
        "moma",
        "serpentine",
        "mori",
        "aic",
        "nga",
        "met",
        "vam",
    ]
    for key in expected_keys:
        assert key in SITES, f"Expected parser '{key}' not found in SITES"


def test_parser_has_required_attributes():
    """Each parser must have source and city."""
    from src.sites import SITES

    for key, parser in SITES.items():
        assert hasattr(parser, "source"), f"{key} missing 'source'"
        assert hasattr(parser, "city"), f"{key} missing 'city'"
        assert parser.source, f"{key} has empty 'source'"
        assert parser.city, f"{key} has empty 'city'"


def test_kunsthaus_is_native_parser():
    """Kunsthaus has parse_exhibition_page native extraction."""
    from src.sites import SITES

    parser = SITES["kunsthaus"]
    assert hasattr(parser, "parse_exhibition_page")
    assert callable(parser.parse_exhibition_page)


def test_aic_and_whitney_use_rest_api():
    """AIC and Whitney should be REST_API strategy."""
    from src.sites import SITES
    from src.sites.base import ParserStrategy

    assert SITES["aic"].strategy == ParserStrategy.REST_API
    assert SITES["whitney"].strategy == ParserStrategy.REST_API


def test_moma_uses_csv_remote():
    """MoMA should be CSV_REMOTE strategy."""
    from src.sites import SITES
    from src.sites.base import ParserStrategy

    assert SITES["moma"].strategy == ParserStrategy.CSV_REMOTE


def test_nga_uses_artwork_only():
    """NGA should be ARTWORK_ONLY strategy."""
    from src.sites import SITES
    from src.sites.base import ParserStrategy

    assert SITES["nga"].strategy == ParserStrategy.ARTWORK_ONLY


def test_wikidata_uses_sparql():
    """Wikidata should be SPARQL strategy."""
    from src.sites import SITES
    from src.sites.base import ParserStrategy

    assert SITES["wikidata"].strategy == ParserStrategy.SPARQL


def test_hirshhorn_uses_rest_api():
    """Hirshhorn should be REST_API strategy."""
    from src.sites import SITES
    from src.sites.base import ParserStrategy

    assert SITES["hirshhorn"].strategy == ParserStrategy.REST_API


def test_psa_has_playwright_and_native_parser():
    """PSA uses Playwright and has parse_exhibition_page."""
    from src.sites import SITES

    parser = SITES["psa"]
    assert parser.use_playwright is True
    assert hasattr(parser, "parse_exhibition_page")


def test_parsers_have_institution_type():
    """All parsers should have institution_type attribute."""
    from src.sites import SITES

    for key, parser in SITES.items():
        assert hasattr(parser, "institution_type"), f"{key} missing institution_type"
        assert parser.institution_type in (
            "museum",
            "biennial",
            "triennial",
            "gallery",
            "quintennial",
        ), f"{key} has unexpected institution_type: {parser.institution_type}"


def test_biennale_parsers_have_biennial_type():
    """Selected biennial parsers should have correct institution_type."""
    from src.sites import SITES

    biennial_keys = [
        "venice_biennale",
        "documenta",
        "berlin_biennale",
        "saopaulo_biennial",
        "sharjah_biennale",
        "liverpool_biennale",
        "taipei_biennale",
        "sydney_biennale",
        "whitney_biennial",
    ]
    # documenta is quintennial (every 5 years), not biennial
    expected_types = {
        "documenta": "quintennial",
    }
    for key in biennial_keys:
        if key in SITES:
            expected = expected_types.get(key, "biennial")
            assert SITES[key].institution_type == expected, (
                f"{key} should be {expected}, got {SITES[key].institution_type}"
            )


def test_parser_key_matches_registration_key():
    """If parser_key is set, it should match the key in SITES."""
    from src.sites import SITES

    for key, parser in SITES.items():
        pk = getattr(parser, "parser_key", "")
        # parser_key may be empty (derived from class name) or matching
        if pk:
            assert pk == key, f"{key} has parser_key={pk}"


def test_serpentine_has_event_keywords():
    """Serpentine parser should have EVENT_KEYWORDS."""
    from src.sites import SITES

    parser = SITES["serpentine"]
    assert hasattr(parser, "EVENT_KEYWORDS")
    assert isinstance(parser.EVENT_KEYWORDS, list)
    assert len(parser.EVENT_KEYWORDS) > 0


def test_flv_has_scrapling_check():
    """FLV module should have HAS_SCRAPLING flag."""
    import src.sites.flv as flv_module

    assert hasattr(flv_module, "HAS_SCRAPLING")
    assert flv_module.HAS_SCRAPLING in (True, False)


__all__ = []  # Ensure no unintended exports
