"""Демонстрация работы генератора Excel файлов."""

from decimal import Decimal
from src.models import Card
from src.excel_generator import generate_excel


def main():
    """Демонстрация создания Excel файла с тестовыми данными."""
    
    # Создаем тестовые карты
    demo_cards = [
        Card(
            quantity=2,
            name="Flare of Denial (0400 - Retro Frame)",
            url="https://www.cardkingdom.com/mtg/modern-horizons-3/flare-of-denial",
            is_foil=False,
            condition="NM",
            edition="Modern Horizons 3",
            edition_code="MH3",
            price_per_unit=Decimal("59.99"),
            total_price=Decimal("119.98"),
            rarity="R",
            variation="0400 - Retro Frame"
        ),
        Card(
            quantity=2,
            name="Sorin of House Markov (0444 - Borderless)",
            url="https://www.cardkingdom.com/mtg/modern-horizons-3-variants/sorin-of-house-markov-0444-borderless-foil",
            is_foil=True,
            condition="NM",
            edition="Modern Horizons 3",
            edition_code="MH3",
            price_per_unit=Decimal("49.99"),
            total_price=Decimal("99.98"),
            rarity="M",
            variation="0444 - Borderless"
        ),
        Card(
            quantity=4,
            name="Journey to Nowhere (0003 - Showcase)",
            url="https://www.cardkingdom.com/mtg/outlaws-of-thunder-junction-breaking-news/journey-to-nowhere-0003-showcase-foil",
            is_foil=True,
            condition="NM",
            edition="Outlaws of Thunder Junction: Breaking News",
            edition_code="OTP",
            price_per_unit=Decimal("0.49"),
            total_price=Decimal("1.96"),
            rarity="U",
            variation="0003 - Showcase"
        ),
    ]
    
    # Генерируем Excel файл с формулами
    output_file = "demo_order.xlsx"
    generate_excel(demo_cards, output_file, use_formulas=True)
    
    print(f"✓ Excel файл создан: {output_file}")
    print(f"  Количество карт: {len(demo_cards)}")
    print(f"  Использованы формулы: Да")
    print("\nСодержимое файла:")
    print("-" * 80)
    for card in demo_cards:
        print(card)
    print("-" * 80)
    print(f"\nОбщая стоимость: ${sum(card.total_price for card in demo_cards)}")


if __name__ == "__main__":
    main()