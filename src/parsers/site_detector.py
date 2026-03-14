"""Detects which site an HTML cart file belongs to and returns the right parser."""

import logging
from pathlib import Path
from typing import List, Type

from bs4 import BeautifulSoup

from src.parsers.base_parser import BaseCartParser
from src.parsers.card_kingdom_parser import CardKingdomParser
from src.parsers.starcitygames_parser import StarCityGamesParser

logger = logging.getLogger(__name__)

# All registered parsers, tried in order
_PARSERS: List[Type[BaseCartParser]] = [
    CardKingdomParser,
    StarCityGamesParser,
]


class SiteDetector:
    """
    Identifies the website from an HTML cart file and returns
    the appropriate parser instance.

    To support a new site:
    1. Create a parser in src/parsers/
    2. Add it to _PARSERS above
    """

    @staticmethod
    def detect(html_path: str) -> BaseCartParser:
        """
        Load the HTML file, try all registered parsers, and return
        an instance of the first one that can handle it.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If no registered parser recognizes the HTML.
        """
        path = Path(html_path)
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')

        for parser_class in _PARSERS:
            if parser_class.can_parse(soup):
                logger.info(f"Detected site parser: {parser_class.__name__}")
                return parser_class(html_path)

        raise ValueError(
            f"Could not determine the website for file: {html_path}. "
            f"Supported parsers: {[p.__name__ for p in _PARSERS]}"
        )
