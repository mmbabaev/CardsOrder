"""HTML парсер для извлечения данных о карточках Card Kingdom."""

import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from src.models import Card

# Настройка логирования
logger = logging.getLogger(__name__)

# Базовый URL Card Kingdom
BASE_URL = "https://www.cardkingdom.com/"


def parse_cart_html(html_path: str) -> List[Card]:
    """
    Парсит HTML файл корзины Card Kingdom и извлекает данные о карточках.
    
    Args:
        html_path: Путь к HTML файлу корзины Card Kingdom
        
    Returns:
        Список объектов Card с данными о карточках
        
    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если HTML невалидный или отсутствуют обязательные элементы
    """
    # Проверка существования файла
    file_path = Path(html_path)
    if not file_path.exists():
        raise FileNotFoundError(f"HTML файл не найден: {html_path}")
    
    # Чтение и парсинг HTML
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла {html_path}: {e}")
    
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except Exception as e:
        raise ValueError(f"Ошибка при парсинге HTML: {e}")
    
    # Поиск всех блоков с карточками
    cart_items = soup.find_all('div', class_='cart-item-wrapper')
    
    if not cart_items:
        logger.warning("В HTML не найдено блоков с карточками")
        return []
    
    logger.info(f"Найдено {len(cart_items)} карточек в корзине")
    
    # Парсинг каждой карточки
    cards = []
    for idx, item_div in enumerate(cart_items, 1):
        try:
            card = _parse_card_item(item_div)
            cards.append(card)
        except Exception as e:
            logger.warning(f"Пропущена карточка #{idx}: {e}")
            continue
    
    logger.info(f"Успешно распарсено {len(cards)} карточек")
    return cards


def _parse_card_item(item_div) -> Card:
    """
    Парсит один блок карточки из HTML и создает объект Card.
    
    Args:
        item_div: BeautifulSoup элемент div с классом 'cart-item-wrapper'
        
    Returns:
        Объект Card с данными о карточке
        
    Raises:
        ValueError: Если отсутствуют обязательные элементы
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
    variation_match = re.search(r'\(([^)]+(?:Foil|Non-Foil|Borderless|Showcase|Extended Art)[^)]*)\)\s*$', full_title)
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
        # Если формат не соответствует, берем весь текст как издание
        edition = edition_text
        rarity = 'C'  # По умолчанию Common
        logger.warning(f"Не удалось извлечь редкость для '{edition_text}', использована 'C'")
    
    # Извлечение состояния
    style_span = product_link.find('span', class_='style')
    if not style_span:
        raise ValueError("Не найден элемент style")
    condition = style_span.get_text(strip=True)
    
    # Проверка фойла
    foil_div = product_link.find('div', class_='foil')
    is_foil = foil_div is not None
    
    # Извлечение количества
    quantity_selector = item_div.find('lineitem-quantity-selector')
    if not quantity_selector:
        quantity_selector = item_div.find('lineitemQuantity')
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
    # Ищем все small элементы и находим тот, который содержит "/ea"
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
    
    # Добавляем базовый URL если это относительная ссылка
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
        edition_code=None,  # Будет заполнено позже через edition_fetcher
        price_per_unit=price_per_unit,
        total_price=total_price,
        rarity=rarity,
        variation=variation
    )
    
    return card