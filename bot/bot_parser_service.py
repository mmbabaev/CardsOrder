"""Сервис для парсинга HTML корзины и генерации Excel файлов."""

import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple

from src.excel_generator import generate_excel
from src.models import Card
from src.parser import parse_cart_html

# Настройка логирования
logger = logging.getLogger(__name__)


def parse_and_generate(html_path: str, output_dir: str) -> Tuple[str, Dict[str, any]]:
    """
    Парсит HTML корзины Card Kingdom и генерирует Excel файл с заказом.
    
    Выполняет полный цикл обработки:
    1. Парсинг HTML файла корзины
    2. Генерация Excel файла с уникальным именем
    3. Вычисление статистики заказа
    
    Args:
        html_path: Путь к HTML файлу корзины Card Kingdom
        output_dir: Директория для сохранения сгенерированного Excel файла
        
    Returns:
        Tuple[str, Dict]: Кортеж из двух элементов:
            - str: Полный путь к сгенерированному Excel файлу
            - Dict: Словарь со статистикой заказа:
                - total_cards (int): Количество уникальных карт
                - total_quantity (int): Общее количество карт
                - total_price (Decimal): Итоговая сумма заказа
                - foil_count (int): Количество фойловых карт
                
    Raises:
        FileNotFoundError: Если HTML файл не найден
        ValueError: Если HTML невалидный или список карт пустой
        OSError: Если не удалось создать директорию или записать Excel файл
        
    Example:
        >>> excel_path, stats = parse_and_generate('/tmp/cart.html', '/tmp/output')
        >>> print(f"Cards: {stats['total_cards']}, Total: ${stats['total_price']}")
        Cards: 21, Total: $104.89
    """
    logger.info(f"Начинается обработка HTML файла: {html_path}")
    logger.info(f"Директория для вывода: {output_dir}")
    
    # Парсинг HTML корзины
    try:
        cards = parse_cart_html(html_path)
        logger.info(f"Успешно распарсено {len(cards)} карт")
    except FileNotFoundError as e:
        logger.error(f"HTML файл не найден: {e}")
        raise
    except ValueError as e:
        logger.error(f"Ошибка при парсинге HTML: {e}")
        raise
    
    if not cards:
        error_msg = "Список карт пустой после парсинга"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Подготовка директории для вывода
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Директория для вывода подготовлена: {output_path}")
    except OSError as e:
        logger.error(f"Не удалось создать директорию {output_dir}: {e}")
        raise
    
    # Генерация уникального имени для Excel файла
    unique_id = uuid.uuid4()
    excel_filename = f"order_{unique_id}.xlsx"
    excel_path = output_path / excel_filename
    logger.info(f"Имя Excel файла: {excel_filename}")
    
    # Генерация Excel файла
    try:
        generate_excel(cards, str(excel_path), use_formulas=True)
        logger.info(f"Excel файл успешно создан: {excel_path}")
    except (ValueError, OSError) as e:
        logger.error(f"Ошибка при генерации Excel файла: {e}")
        raise
    
    # Вычисление статистики заказа
    stats = _calculate_statistics(cards)
    logger.info(f"Статистика заказа: {stats}")
    
    return str(excel_path), stats


def _calculate_statistics(cards: List[Card]) -> Dict[str, any]:
    """
    Вычисляет статистику заказа на основе списка карт.
    
    Args:
        cards: Список объектов Card
        
    Returns:
        Dict: Словарь со статистикой:
            - total_cards (int): Количество уникальных карт
            - total_quantity (int): Общее количество карт
            - total_price (Decimal): Итоговая сумма заказа
            - foil_count (int): Количество фойловых карт
    """
    logger.debug("Вычисление статистики заказа")
    
    total_cards = len(cards)
    total_quantity = sum(card.quantity for card in cards)
    total_price = sum(card.total_price for card in cards)
    foil_count = sum(card.quantity for card in cards if card.is_foil)
    
    stats = {
        'total_cards': total_cards,
        'total_quantity': total_quantity,
        'total_price': total_price,
        'foil_count': foil_count
    }
    
    logger.debug(f"Статистика: уникальных карт={total_cards}, "
                 f"всего карт={total_quantity}, "
                 f"сумма=${total_price}, "
                 f"фойловых={foil_count}")
    
    return stats