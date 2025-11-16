"""Модели данных для карточек MTG."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Card:
    """
    Модель данных для карточки Magic: The Gathering.
    
    Attributes:
        quantity (int): Количество карт.
        name (str): Название карты.
        url (str): Полная ссылка на карточку на сайте Card Kingdom.
        is_foil (bool): Является ли карта фойловой (foil).
        condition (str): Состояние карты (NM, EX, LP, MP, HP, DMG).
        edition (str): Полное название издания.
        edition_code (str | None): Короткий код издания (например, BRO, MH3). Опционально.
        price_per_unit (Decimal): Цена за одну карту в USD.
        total_price (Decimal): Итоговая сумма (quantity * price_per_unit).
        rarity (str): Редкость карты (C - Common, U - Uncommon, R - Rare, M - Mythic, S - Special).
        variation (str | None): Вариация карты (например, "1743 - Foil", "Borderless"). Опционально.
    """
    
    quantity: int
    name: str
    url: str
    is_foil: bool
    condition: str
    edition: str
    edition_code: str | None
    price_per_unit: Decimal
    total_price: Decimal
    rarity: str
    variation: str | None

    def to_excel_row(self) -> list:
        """
        Возвращает данные карты в виде списка значений для записи в Excel.
        
        Порядок столбцов:
        [Количество, Название, Ссылка, Фойл, Состояние, Издание, Цена за штуку, Итого]
        
        Returns:
            list: Список значений для строки Excel.
        """
        foil_text = "ДА" if self.is_foil else "НЕТ"
        edition_display = self.edition_code if self.edition_code else self.edition
        
        return [
            self.quantity,
            self.name,
            self.url,
            foil_text,
            self.condition,
            edition_display,
            self.price_per_unit,
            self.total_price
        ]

    def __str__(self) -> str:
        """
        Возвращает строковое представление карты для удобного вывода.
        
        Returns:
            str: Форматированная строка с информацией о карте.
        """
        foil_marker = " (FOIL)" if self.is_foil else ""
        edition_display = self.edition_code if self.edition_code else self.edition
        variation_info = f" [{self.variation}]" if self.variation else ""
        
        return (
            f"{self.quantity}x {self.name}{foil_marker} - "
            f"{edition_display} ({self.rarity}) - "
            f"{self.condition} - "
            f"${self.price_per_unit}/ea (Total: ${self.total_price})"
            f"{variation_info}"
        )