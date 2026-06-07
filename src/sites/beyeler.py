from src.sites.base import BaseSiteParser


class BeyelerParser(BaseSiteParser):
    """Fondation Beyeler - Basel.

    贝耶勒基金会，瑞士最著名的私人美术馆之一。
    """

    source = "Fondation Beyeler"
    city = "Basel"
    parser_key = "beyeler"
    institution_type = "museum"
    list_url = "https://www.fondationbeyeler.ch/en/exhibitions"
    extra_list_urls = ["https://www.fondationbeyeler.ch/en/exhibitions/past-exhibitions"]
    use_playwright = True
    link_patterns = [
        r"fondationbeyeler\.ch/en/exhibitions(?:/past-exhibitions)?/[^/]+",
    ]
