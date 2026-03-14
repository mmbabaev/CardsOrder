"""Tests for SiteDetector."""

import pytest
from pathlib import Path

from src.parsers.site_detector import SiteDetector
from src.parsers.card_kingdom_parser import CardKingdomParser
from src.parsers.starcitygames_parser import StarCityGamesParser


class TestSiteDetectorDetect:

    def test_detects_card_kingdom(self):
        parser = SiteDetector.detect("tests/fixtures/sample_cart.html")
        assert isinstance(parser, CardKingdomParser)

    def test_detects_card_kingdom_mobile(self):
        parser = SiteDetector.detect("tests/fixtures/sample_cart_ios.html")
        assert isinstance(parser, CardKingdomParser)

    def test_detects_starcitygames(self):
        parser = SiteDetector.detect("tests/fixtures/sample_cart_scg.html")
        assert isinstance(parser, StarCityGamesParser)

    def test_raises_for_unknown_site(self):
        temp = Path("tests/fixtures/unknown_site.html")
        temp.write_text("<html><body><p>Some random website</p></body></html>")
        try:
            with pytest.raises(ValueError, match="Could not determine the website"):
                SiteDetector.detect(str(temp))
        finally:
            temp.unlink()

    def test_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            SiteDetector.detect("nonexistent.html")


class TestSiteDetectorSiteName:

    def test_card_kingdom_site_name(self):
        parser = SiteDetector.detect("tests/fixtures/sample_cart.html")
        assert parser.site_name == "Card Kingdom"

    def test_starcitygames_site_name(self):
        parser = SiteDetector.detect("tests/fixtures/sample_cart_scg.html")
        assert parser.site_name == "Star City Games"
