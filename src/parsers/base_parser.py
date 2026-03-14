"""Abstract base class for cart parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup

from src.models import Card


class BaseCartParser(ABC):
    """
    Abstract base class for MTG cart parsers.

    To add a new site:
    1. Subclass BaseCartParser
    2. Implement can_parse() to detect your site's HTML
    3. Implement parse() to extract Card objects
    4. Register the class in SiteDetector
    """

    def __init__(self, html_path: str):
        self.html_path = Path(html_path)
        self.soup = self._load_html()

    def _load_html(self) -> BeautifulSoup:
        if not self.html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {self.html_path}")
        with open(self.html_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f.read(), 'lxml')

    @property
    @abstractmethod
    def site_name(self) -> str:
        """Human-readable site name, e.g. 'Card Kingdom'."""
        ...

    @classmethod
    @abstractmethod
    def can_parse(cls, soup: BeautifulSoup) -> bool:
        """Return True if this parser can handle the given HTML."""
        ...

    @abstractmethod
    def parse(self) -> List[Card]:
        """Parse the cart and return a list of Card objects."""
        ...
