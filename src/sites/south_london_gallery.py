from src.sites.base import BaseSiteParser


class SouthLondonGalleryParser(BaseSiteParser):
    """South London Gallery.

    南伦敦画廊，英国历史最悠久的当代艺术空间之一。
    """

    source = "South London Gallery"
    city = "London"
    parser_key = "south_london_gallery"
    institution_type = "museum"
    list_url = "https://www.southlondongallery.org/whats-on/exhibitions/"
    # NOTE: The site lists only current exhibitions (~4 at any time).
    # No dedicated past-exhibitions archive page exists.
    link_patterns = [
        r"southlondongallery\.org/(?:exhibitions|whats-on/exhibitions)/[^/#]+/?$",
    ]
