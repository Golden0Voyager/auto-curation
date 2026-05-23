from src.sites.moma import MoMAParser
from src.sites.tate import TateParser
from src.sites.met import MetParser
from src.sites.palais_tokyo import PalaisTokyoParser
from src.sites.biennale import BiennaleParser
from src.sites.pompidou import PompidouParser
from src.sites.guggenheim import GuggenheimParser
from src.sites.serpentine import SerpentineParser
from src.sites.mori import MoriParser
from src.sites.mplus import MPlusParser

SITES = {
    "moma": MoMAParser(),
    "tate": TateParser(),
    "met": MetParser(),
    "palais_tokyo": PalaisTokyoParser(),
    "biennale": BiennaleParser(),
    "pompidou": PompidouParser(),
    "guggenheim": GuggenheimParser(),
    "serpentine": SerpentineParser(),
    "mori": MoriParser(),
    "mplus": MPlusParser()
}
