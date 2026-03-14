"""Tests for Star City Games cart parser."""

import pytest
from decimal import Decimal
from pathlib import Path

from src.parsers.starcitygames_parser import StarCityGamesParser
from src.site_detector import SiteDetector
from src.models import Card

FIXTURE = "tests/fixtures/sample_cart_scg.html"


class TestStarCityGamesParserDetection:

    def test_can_parse_scg_html(self):
        from bs4 import BeautifulSoup
        with open(FIXTURE) as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        assert StarCityGamesParser.can_parse(soup) is True

    def test_cannot_parse_card_kingdom_html(self):
        from bs4 import BeautifulSoup
        with open("tests/fixtures/sample_cart.html") as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        assert StarCityGamesParser.can_parse(soup) is False

    def test_site_detector_returns_scg_parser(self):
        parser = SiteDetector.detect(FIXTURE)
        assert isinstance(parser, StarCityGamesParser)


class TestStarCityGamesParserParsing:

    @pytest.fixture
    def cards(self):
        return StarCityGamesParser(FIXTURE).parse()

    def test_returns_correct_count(self, cards):
        assert len(cards) == 3

    def test_all_cards_are_card_instances(self, cards):
        assert all(isinstance(c, Card) for c in cards)

    def test_card_names(self, cards):
        names = [c.name for c in cards]
        assert "Abundant Growth" in names
        assert "Snuff Out" in names
        assert "Lightning Bolt" in names

    def test_urls_are_full_scg_urls(self, cards):
        for card in cards:
            assert card.url.startswith("https://starcitygames.com/")

    def test_editions(self, cards):
        editions = {c.name: c.edition for c in cards}
        assert editions["Abundant Growth"] == "Fallout Commander"
        assert editions["Snuff Out"] == "Mystery Booster 2"
        assert editions["Lightning Bolt"] == "Magic 2011"

    def test_prices(self, cards):
        prices = {c.name: c.price_per_unit for c in cards}
        assert prices["Abundant Growth"] == Decimal("0.39")
        assert prices["Snuff Out"] == Decimal("9.99")
        assert prices["Lightning Bolt"] == Decimal("4.99")

    def test_quantities(self, cards):
        quantities = {c.name: c.quantity for c in cards}
        assert quantities["Abundant Growth"] == 1
        assert quantities["Snuff Out"] == 2
        assert quantities["Lightning Bolt"] == 1

    def test_total_price_equals_quantity_times_price(self, cards):
        for card in cards:
            assert card.total_price == card.price_per_unit * card.quantity

    def test_foil_detection(self, cards):
        by_name = {c.name: c for c in cards}
        assert by_name["Abundant Growth"].is_foil is False
        assert by_name["Snuff Out"].is_foil is False
        assert by_name["Lightning Bolt"].is_foil is True

    def test_condition_mapping(self, cards):
        by_name = {c.name: c for c in cards}
        assert by_name["Abundant Growth"].condition == "NM"
        assert by_name["Snuff Out"].condition == "NM"
        assert by_name["Lightning Bolt"].condition == "LP"

    def test_total_quantity(self, cards):
        assert sum(c.quantity for c in cards) == 4

    def test_total_price(self, cards):
        total = sum(c.total_price for c in cards)
        # 0.39*1 + 9.99*2 + 4.99*1 = 0.39 + 19.98 + 4.99 = 25.36
        assert abs(total - Decimal("25.36")) < Decimal("0.01")


class TestStarCityGamesParserEdgeCases:

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            StarCityGamesParser("nonexistent.html").parse()

    def test_empty_cart_returns_empty_list(self):
        from pathlib import Path
        empty_html = """<!DOCTYPE html>
<html><body>
  <div data-cart-content>
    <table class="cart" data-cart-quantity="0">
      <tbody class="cart-list"></tbody>
    </table>
  </div>
  starcitygames.com
</body></html>"""
        temp = Path("tests/fixtures/empty_cart_scg.html")
        temp.write_text(empty_html)
        try:
            cards = StarCityGamesParser(str(temp)).parse()
            assert cards == []
        finally:
            temp.unlink()
