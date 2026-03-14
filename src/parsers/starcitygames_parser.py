"""Star City Games cart parser."""

import logging
import re
from decimal import Decimal
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from src.base_parser import BaseCartParser
from src.models import Card

logger = logging.getLogger(__name__)

# Maps SCG condition strings to our standard codes
_CONDITION_MAP = {
    "Near Mint": "NM",
    "Lightly Played": "LP",
    "Moderately Played": "MP",
    "Heavily Played": "HP",
    "Damaged": "DMG",
}


class StarCityGamesParser(BaseCartParser):
    """Parser for Star City Games shopping cart HTML."""

    @classmethod
    def can_parse(cls, soup: BeautifulSoup) -> bool:
        html_str = str(soup)
        return (
            'starcitygames.com' in html_str
            and 'data-item-row' in html_str
            and 'cart-item-qty-input' in html_str
        )

    def parse(self) -> List[Card]:
        items = self.soup.find_all('tr', class_='cart-item')

        if not items:
            logger.warning("No cart items found in SCG HTML")
            return []

        logger.info(f"Found {len(items)} cart items")

        cards = []
        for idx, row in enumerate(items, 1):
            try:
                cards.append(self._parse_item(row))
            except Exception as e:
                logger.warning(f"Skipped item #{idx}: {e}")

        logger.info(f"Parsed {len(cards)} cards")
        return cards

    def _parse_item(self, row: Tag) -> Card:
        # URL — prefer data-url attribute, fall back to href
        url = row.get('data-url')
        if not url:
            link = row.select_one('h4.cart-item-name a')
            if not link:
                raise ValueError("Card URL not found")
            url = link['href']

        # Name — text of the <a> inside cart-item-name
        name_link = row.select_one('h4.cart-item-name a')
        if not name_link:
            raise ValueError("Card name not found")
        name = name_link.get_text(strip=True)

        # Edition — cart-item-value inside cart-item-category
        category_cell = row.find('td', class_='cart-item-category')
        if not category_cell:
            raise ValueError("Edition (category) not found")
        edition = category_cell.select_one('span.cart-item-value').get_text(strip=True)

        # Price — data-price attribute on row
        price_str = row.get('data-price', '')
        price_match = re.search(r'([0-9]+\.[0-9]{2})', price_str)
        if not price_match:
            # fall back to price cell
            price_cell = row.find('td', class_='cart-item-price')
            if not price_cell:
                raise ValueError("Price not found")
            price_text = price_cell.select_one('span.cart-item-value').get_text(strip=True)
            price_match = re.search(r'([0-9]+\.[0-9]{2})', price_text)
            if not price_match:
                raise ValueError(f"Could not parse price from: {price_text}")
        price_per_unit = Decimal(price_match.group(1))

        # Quantity
        qty_input = row.select_one('input.cart-item-qty-input')
        if not qty_input:
            raise ValueError("Quantity input not found")
        try:
            quantity = int(qty_input['value'])
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid quantity: {e}")

        # Foil — check finish-tag class
        finish_div = row.select_one('div.finish-tag')
        if finish_div:
            classes = finish_div.get('class', [])
            is_foil = 'foil' in classes and 'non-foil' not in classes
        else:
            is_foil = False

        # Condition
        condition_raw = self._get_definition_value(row, 'Condition:')
        condition = _CONDITION_MAP.get(condition_raw, condition_raw)

        return Card(
            quantity=quantity,
            name=name,
            url=url,
            is_foil=is_foil,
            condition=condition,
            edition=edition,
            edition_code=None,
            price_per_unit=price_per_unit,
            total_price=price_per_unit * quantity,
            rarity='C',  # Rarity is not present in SCG cart HTML
            variation=None,
        )

    @staticmethod
    def _get_definition_value(row: Tag, key: str) -> str:
        """Find the <dd> value following a <dt> with the given text."""
        for dt in row.find_all('dt', class_='definitionList-key'):
            if dt.get_text(strip=True) == key:
                dd = dt.find_next_sibling('dd')
                if dd:
                    return dd.get_text(strip=True)
        return ''
