import importlib
import inspect
import logging
import pkgutil
import sys

from src.sites.base import BaseSiteParser as BaseSiteParser

logger = logging.getLogger("auto_curation.sites")


def _discover_parsers():
    """Auto-discover all parser classes in src.sites package.

    Scans every module in src.sites/, imports it, and collects concrete
    classes that define both `source` and `city` class attributes.
    Registration key is taken from `parser_key` if set; otherwise derived
    from the class name.
    """
    parsers = {}
    package_dir = __path__[0]

    # Step 1: import all modules to trigger class registration
    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name.startswith("_"):
            continue
        try:
            importlib.import_module(f"src.sites.{module_name}")
        except Exception as e:
            logger.warning(f"Failed to import src.sites.{module_name}: {e}")

    # Step 2: collect classes with source + city attributes
    for module_name in list(sys.modules.keys()):
        if not module_name.startswith("src.sites.") or module_name == "src.sites":
            continue
        mod = sys.modules[module_name]
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            # Skip BaseSiteParser itself and helper/model classes
            if name in ("BaseSiteParser",):
                continue
            # Skip classes without the required institutional attributes
            if not (hasattr(obj, "source") and hasattr(obj, "city")):
                continue
            # Skip base classes that have default/generic values
            if getattr(obj, "source", "") in ("", "Generic"):
                continue
            # Derive registration key
            key = getattr(obj, "parser_key", None)
            if not key:
                key = name.replace("Parser", "").lower()
                # Handle multi-word class names: e.g. PalaisTokyo -> palais_tokyo
                import re

                key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
            if key in parsers:
                logger.warning(
                    f"Parser key collision: '{key}' already registered. Skipping {name}."
                )
                continue
            try:
                parsers[key] = obj()
                logger.debug(f"Registered parser '{key}' -> {obj.__name__} ({obj.source})")
            except Exception as e:
                logger.error(f"Failed to instantiate {name} for key '{key}': {e}")

    return parsers


SITES = _discover_parsers()
logger.info(f"Auto-discovered {len(SITES)} site parsers: {list(SITES.keys())}")
