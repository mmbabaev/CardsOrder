"""Public API for cart parsing. Uses SiteDetector to pick the right parser."""

from typing import List

from src.models import Card
from src.site_detector import SiteDetector


def parse_cart_html(html_path: str) -> List[Card]:
    """
    Parse an MTG cart HTML file from any supported website.

    Automatically detects the website and applies the correct parser.

    Args:
        html_path: Path to the saved cart HTML file.

    Returns:
        List of Card objects.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the site is not supported or HTML is invalid.
    """
    parser = SiteDetector.detect(html_path)
    return parser.parse()
