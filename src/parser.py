"""Универсальный HTML парсер для Card Kingdom (desktop и mobile)."""

import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import List, Literal

from bs4 import BeautifulSoup

from src.models import Card

# Настройка логирования
logger = logging.getLogger(__name__)

# Базовый URL Card Kingdom
BASE_URL = "https://www.cardkingdom.com/"


class CartParser:
    """Универсальный парсер корзин Card Kingdom для разных форматов."""
    
    FORMAT_DESKTOP = "desktop"
    FORMAT_MOBILE = "mobile"
    
    def __init__(self, html_path: str):
        """
        Инициализация парсера.
        
        Args:
            html_path: Путь к HTML файлу корзины
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если HTML невалидный
        """
        self.html_path = Path(html_path)
        self.soup = self._load_html()
        self.format_type = self._detect_format()
        
    def _load_html(self) -> BeautifulSoup:
        """Загружает и парсит HTML файл."""
        if not self.html_path.exists():
            raise FileNotFoundError(f"HTML файл не найден: {self.html_path}")
        
        try:
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            raise ValueError(f"Ошибка при чтении/парсинге файла: {e}")
    
    def _detect_format(self) -> Literal["desktop", "mobile"]:
        """
        Определяет формат HTML (desktop или mobile).
        
        Desktop сигналы:
        - наличие компонента 'lineitem-quantity-selector'
        - классы типа 'hidden-xs hidden-sm'
        
        Mobile сигналы:
        - отсутствие 'lineitem-quantity-selector'
        - наличие формы с 'input[name="qty"]'
        - классы типа 'col-sm-', 'col-xs-12'
        """
        html_str = str(self.soup)
        
        # Более точное определение: ищем компонент Angular
        if 'lineitem-quantity-selector' in html_str:
            format_type = self.FORMAT_DESKTOP
        elif '<input name="qty"' in html_str or 'class="quantity"' in html_str:
            format_type = self.FORMAT_MOBILE
        else:
            # Fallback: пробуем desktop по умолчанию
            format_type = self.FORMAT_DESKTOP
        
        logger.info(f"Формат определен как: {format_type}")
        return format_type
    
    def parse(self) -> List[Card]:
        """
        Парсит корзину и возвращает список карточек.
        
        Returns:
            Список объектов Card
        """
        logger.info(f"Парсинг в режиме: {self.format_type}")
        
        if self.format_type == self.FORMAT_DESKTOP:
            return self._parse_desktop()
        elif self.format_type == self.FORMAT_MOBILE:
            return self._parse_mobile()
        else:
            raise ValueError(f"Неизвестный формат: {self.format_type}")
    
    def _parse_desktop(self) -> List[Card]:
        """Парсит desktop версию (Angular компоненты)."""
        cart_items = self.soup.find_all('div', class_='cart-item-wrapper')
        
        if not cart_items:
            logger.warning("В HTML не найдено блоков с карточками")
            return []
        
        logger.info(f"Найдено {len(cart_items)} карточек в корзине")
        
        cards = []
        for idx, item_div in enumerate(cart_items, 1):
            try:
                card = self._parse_card_item_desktop(item_div)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Пропущена карточка #{idx}: {e}")
                continue
        
        logger.info(f"Успешно распарсено {len(cards)} карточек (desktop)")
        return cards
    
    def _parse_mobile(self) -> List[Card]:
        """Парсит мобильную версию (обычные HTML элементы)."""
        cart_items = self.soup.find_all('div', class_='cart-item-wrapper')
        
        if not cart_items:
            logger.warning("В HTML не найдено блоков с карточками")
            return []
        
        logger.info(f"Найдено {len(cart_items)} карточек в корзине")
        
        cards = []
        for idx, item_div in enumerate(cart_items, 1):
            try:
                card = self._parse_card_item_mobile(item_div)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Пропущена карточка #{idx}: {e}")
                continue
        
        logger.info(f"Успешно распарсено {len(cards)} карточек (mobile)")
        return cards
    
    def _parse_card_item_desktop(self, item_div) -> Card:
        """
        Парсит одну карточку desktop версии.
        
        Desktop: использует Angular компонент lineitem-quantity-selector
        """
        # Поиск основной ссылки на карточку
        product_link = item_div.find('a', class_='product-link')
        if not product_link:
            raise ValueError("Не найден элемент product-link")
        
        # Извлечение названия
        title_span = product_link.find('span', class_='title')
        if not title_span:
            raise ValueError("Не найден элемент title")
        
        full_title = title_span.get_text(strip=True)
        
        # Извлечение вариации из названия (например, "(1743 - Foil)")
        variation = None
        name = full_title
        variation_match = re.search(
            r'\(([^)]+(?:Foil|Non-Foil|Borderless|Showcase|Extended Art)[^)]*)\)\s*$',
            full_title
        )
        if variation_match:
            variation = variation_match.group(1)
            name = full_title[:variation_match.start()].strip()
        
        # Извлечение издания и редкости
        edition_span = product_link.find('span', class_='edition')
        if not edition_span:
            raise ValueError("Не найден элемент edition")
        
        edition_text = edition_span.get_text(strip=True)
        
        # Парсинг редкости из формата "Edition Name (R)"
        edition_match = re.match(r'(.+?)\s*\(([CURMSL])\)\s*$', edition_text)
        if edition_match:
            edition = edition_match.group(1).strip()
            rarity = edition_match.group(2)
        else:
            edition = edition_text
            rarity = 'C'
            logger.warning(f"Не удалось извлечь редкость для '{edition_text}'")
        
        # Извлечение состояния
        style_span = product_link.find('span', class_='style')
        if not style_span:
            raise ValueError("Не найден элемент style")
        condition = style_span.get_text(strip=True)
        
        # Проверка фойла
        foil_div = product_link.find('div', class_='foil')
        is_foil = foil_div is not None
        
        # Извлечение количества (desktop: Angular компонент)
        quantity_selector = item_div.find('lineitem-quantity-selector')
        if not quantity_selector:
            raise ValueError("Не найден элемент lineitem-quantity-selector")
        
        quantity_str = quantity_selector.get(':quantity')
        if not quantity_str:
            raise ValueError("Не найден атрибут :quantity")
        
        try:
            quantity = int(quantity_str)
        except ValueError:
            raise ValueError(f"Невалидное значение quantity: {quantity_str}")
        
        # Извлечение цены за единицу
        price_small = None
        for small in item_div.find_all('small'):
            text = small.get_text(strip=True)
            if '/ea' in text:
                price_small = small
                break
        
        if not price_small:
            raise ValueError("Не найден элемент small с ценой")
        
        price_text = price_small.get_text(strip=True)
        price_match = re.search(r'\$([0-9]+\.[0-9]{2})\s*/ea', price_text)
        if not price_match:
            raise ValueError(f"Не удалось извлечь цену из: {price_text}")
        
        price_per_unit = Decimal(price_match.group(1))
        
        # Формирование полного URL
        href = product_link.get('href')
        if not href:
            raise ValueError("Не найден атрибут href")
        
        if not href.startswith('http'):
            url = BASE_URL + href.lstrip('/')
        else:
            url = href
        
        # Вычисление итоговой цены
        total_price = price_per_unit * quantity
        
        # Создание объекта Card
        card = Card(
            quantity=quantity,
            name=name,
            url=url,
            is_foil=is_foil,
            condition=condition,
            edition=edition,
            edition_code=None,
            price_per_unit=price_per_unit,
            total_price=total_price,
            rarity=rarity,
            variation=variation
        )
        
        return card
    
    def _parse_card_item_mobile(self, item_div) -> Card:
        """
        Парсит одну карточку мобильной версии.
        
        Mobile: использует обычный HTML input для количества
        Структура отличается только в способе получения количества
        """
        # Все остальное идентично desktop версии!
        # Поиск основной ссылки на карточку
        product_link = item_div.find('a', class_='product-link')
        if not product_link:
            raise ValueError("Не найден элемент product-link")
        
        # Извлечение названия
        title_span = product_link.find('span', class_='title')
        if not title_span:
            raise ValueError("Не найден элемент title")
        
        full_title = title_span.get_text(strip=True)
        
        # Извлечение вариации
        variation = None
        name = full_title
        variation_match = re.search(
            r'\(([^)]+(?:Foil|Non-Foil|Borderless|Showcase|Extended Art)[^)]*)\)\s*$',
            full_title
        )
        if variation_match:
            variation = variation_match.group(1)
            name = full_title[:variation_match.start()].strip()
        
        # Извлечение издания и редкости
        edition_span = product_link.find('span', class_='edition')
        if not edition_span:
            raise ValueError("Не найден элемент edition")
        
        edition_text = edition_span.get_text(strip=True)
        
        edition_match = re.match(r'(.+?)\s*\(([CURMSL])\)\s*$', edition_text)
        if edition_match:
            edition = edition_match.group(1).strip()
            rarity = edition_match.group(2)
        else:
            edition = edition_text
            rarity = 'C'
            logger.warning(f"Не удалось извлечь редкость для '{edition_text}'")
        
        # Извлечение состояния
        style_span = product_link.find('span', class_='style')
        if not style_span:
            raise ValueError("Не найден элемент style")
        condition = style_span.get_text(strip=True)
        
        # Проверка фойла
        foil_div = product_link.find('div', class_='foil')
        is_foil = foil_div is not None
        
        # ⭐ ОТЛИЧИЕ: Извлечение количества (mobile: обычный input)
        quantity_input = item_div.find('input', {'name': 'qty', 'class': 'quantity'})
        if not quantity_input:
            raise ValueError("Не найден элемент input[name='qty']")
        
        quantity_str = quantity_input.get('value')
        if not quantity_str:
            raise ValueError("Не найден атрибут value в input quantity")
        
        try:
            quantity = int(quantity_str)
        except ValueError:
            raise ValueError(f"Невалидное значение quantity: {quantity_str}")
        
        # Извлечение цены за единицу
        price_small = None
        for small in item_div.find_all('small'):
            text = small.get_text(strip=True)
            if '/ea' in text:
                price_small = small
                break
        
        if not price_small:
            raise ValueError("Не найден элемент small с ценой")
        
        price_text = price_small.get_text(strip=True)
        price_match = re.search(r'\$([0-9]+\.[0-9]{2})\s*/ea', price_text)
        if not price_match:
            raise ValueError(f"Не удалось извлечь цену из: {price_text}")
        
        price_per_unit = Decimal(price_match.group(1))
        
        # Формирование полного URL
        href = product_link.get('href')
        if not href:
            raise ValueError("Не найден атрибут href")
        
        if not href.startswith('http'):
            url = BASE_URL + href.lstrip('/')
        else:
            url = href
        
        # Вычисление итоговой цены
        total_price = price_per_unit * quantity
        
        # Создание объекта Card
        card = Card(
            quantity=quantity,
            name=name,
            url=url,
            is_foil=is_foil,
            condition=condition,
            edition=edition,
            edition_code=None,
            price_per_unit=price_per_unit,
            total_price=total_price,
            rarity=rarity,
            variation=variation
        )
        
        return card


def parse_cart_html(html_path: str) -> List[Card]:
    """
    Парсит HTML файл корзины Card Kingdom и извлекает данные о карточках.
    
    Автоматически определяет формат (desktop или mobile) и применяет
    соответствующий парсер.
    
    Args:
        html_path: Путь к HTML файлу корзины Card Kingdom
        
    Returns:
        Список объектов Card с данными о карточках
        
    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если HTML невалидный или отсутствуют обязательные элементы
    """
    parser = CartParser(html_path)
    return parser.parse()
