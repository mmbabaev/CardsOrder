"""Card Kingdom cart parser (desktop and mobile)."""

import logging
import re
from decimal import Decimal
from typing import List, Literal

from bs4 import BeautifulSoup

from src.parsers.base_parser import BaseCartParser
from src.models import Card

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cardkingdom.com/"


class CardKingdomParser(BaseCartParser):
    """Parser for Card Kingdom shopping cart HTML (desktop and mobile)."""

    FORMAT_DESKTOP = "desktop"
    FORMAT_MOBILE = "mobile"
    FORMAT_DROPDOWN = "dropdown"

    def __init__(self, html_path: str):
        super().__init__(html_path)
        self.format_type = self._detect_format()

    @property
    def site_name(self) -> str:
        return "Card Kingdom"

    @classmethod
    def can_parse(cls, soup: BeautifulSoup) -> bool:
        """Detect Card Kingdom HTML by its unique markers."""
        html_str = str(soup)
        return (
            'cardkingdom.com' in html_str
            or 'cart-item-wrapper' in html_str
            or 'lineitem-quantity-selector' in html_str
        )

    def _detect_format(self) -> Literal["desktop", "mobile", "dropdown"]:
        html_str = str(self.soup)
        if 'lineitem-quantity-selector' in html_str:
            return self.FORMAT_DESKTOP
        elif 'Select quantity, current:' in html_str:
            return self.FORMAT_DROPDOWN
        elif '<input name="qty"' in html_str:
            return self.FORMAT_MOBILE
        return self.FORMAT_DESKTOP

    def parse(self) -> List[Card]:
        logger.info(f"CardKingdomParser: format={self.format_type}")
        cart_items = self.soup.find_all('div', class_='cart-item-wrapper')

        if not cart_items:
            logger.warning("No cart items found in HTML")
            return []

        logger.info(f"Found {len(cart_items)} cart items")

        cards = []
        for idx, item_div in enumerate(cart_items, 1):
            try:
                card = self._parse_item(item_div)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Skipped item #{idx}: {e}")

        logger.info(f"Parsed {len(cards)} cards")
        return cards

    def _parse_item(self, item_div) -> Card:
        product_link = item_div.find('a', class_='product-link')
        if not product_link:
            raise ValueError("product-link not found")

        # Name + variation
        title_span = product_link.find('span', class_='title')
        if not title_span:
            raise ValueError("title not found")
        full_title = title_span.get_text(strip=True)

        variation = None
        name = full_title
        variation_match = re.search(
            r'\(([^)]+(?:Foil|Non-Foil|Borderless|Showcase|Extended Art)[^)]*)\)\s*$',
            full_title
        )
        if variation_match:
            variation = variation_match.group(1)
            name = full_title[:variation_match.start()].strip()

        # Edition + rarity
        edition_span = product_link.find('span', class_='edition')
        if not edition_span:
            raise ValueError("edition not found")
        edition_text = edition_span.get_text(strip=True)
        edition_match = re.match(r'(.+?)\s*\(([CURMSL])\)\s*$', edition_text)
        if edition_match:
            edition = edition_match.group(1).strip()
            rarity = edition_match.group(2)
        else:
            edition = edition_text
            rarity = 'C'
            logger.warning(f"Could not extract rarity from '{edition_text}'")

        # Condition
        style_span = product_link.find('span', class_='style')
        if not style_span:
            raise ValueError("style not found")
        condition = style_span.get_text(strip=True)

        # Foil
        is_foil = product_link.find('div', class_='foil') is not None

        # Quantity — desktop vs mobile vs dropdown
        if self.format_type == self.FORMAT_DESKTOP:
            quantity_selector = item_div.find('lineitem-quantity-selector')
            if not quantity_selector:
                raise ValueError("lineitem-quantity-selector not found")
            quantity_str = quantity_selector.get(':quantity')
            if not quantity_str:
                raise ValueError(":quantity attribute not found")
        elif self.format_type == self.FORMAT_MOBILE:
            quantity_input = item_div.find('input', {'name': 'qty', 'class': 'quantity'})
            if not quantity_input:
                raise ValueError("input[name='qty'] not found")
            quantity_str = quantity_input.get('value')
            if not quantity_str:
                raise ValueError("value attribute not found in quantity input")
        else:
            dropdown_btn = item_div.find('a', attrs={'aria-label': re.compile(r'Select quantity, current: \d+')})
            if not dropdown_btn:
                raise ValueError("dropdown quantity button not found")
            match = re.search(r'current: (\d+)', dropdown_btn.get('aria-label', ''))
            if not match:
                raise ValueError("could not parse quantity from aria-label")
            quantity_str = match.group(1)

        try:
            quantity = int(quantity_str)
        except ValueError:
            raise ValueError(f"Invalid quantity value: {quantity_str}")

        # Price
        price_small = next(
            (s for s in item_div.find_all('small') if '/ea' in s.get_text()),
            None
        )
        if not price_small:
            raise ValueError("Price element not found")
        price_match = re.search(r'\$([0-9]+\.[0-9]{2})\s*/ea', price_small.get_text(strip=True))
        if not price_match:
            raise ValueError(f"Could not parse price from: {price_small.get_text(strip=True)}")
        price_per_unit = Decimal(price_match.group(1))

        # URL
        href = product_link.get('href')
        if not href:
            raise ValueError("href not found")
        url = href if href.startswith('http') else BASE_URL + href.lstrip('/')

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
            rarity=rarity,
            variation=variation,
        )
