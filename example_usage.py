"""Пример использования HTML парсера для карточек Card Kingdom."""

from src.parser import parse_cart_html

def main():
    """Демонстрация использования парсера."""
    
    # Путь к тестовому HTML файлу
    html_file = "tests/fixtures/sample_cart.html"
    
    print("=" * 80)
    print("Парсинг HTML корзины Card Kingdom")
    print("=" * 80)
    print(f"\nФайл: {html_file}\n")
    
    try:
        # Парсинг HTML
        cards = parse_cart_html(html_file)
        
        # Вывод статистики
        print(f"✓ Успешно распарсено карточек: {len(cards)}")
        print(f"✓ Общее количество карт: {sum(card.quantity for card in cards)}")
        print(f"✓ Общая сумма: ${sum(card.total_price for card in cards):.2f}")
        
        # Вывод первых 5 карточек для примера
        print("\n" + "=" * 80)
        print("Примеры распарсенных карточек (первые 5):")
        print("=" * 80 + "\n")
        
        for i, card in enumerate(cards[:5], 1):
            print(f"{i}. {card}")
            print(f"   URL: {card.url}")
            print()
        
        # Статистика по редкости
        rarity_stats = {}
        for card in cards:
            rarity_stats[card.rarity] = rarity_stats.get(card.rarity, 0) + 1
        
        print("=" * 80)
        print("Статистика по редкости:")
        print("=" * 80)
        for rarity, count in sorted(rarity_stats.items()):
            print(f"  {rarity}: {count} карточек")
        
        # Статистика по фойлу
        foil_count = sum(1 for card in cards if card.is_foil)
        print(f"\n✨ Фойловых карт: {foil_count}")
        
        # Карты с вариациями
        variation_count = sum(1 for card in cards if card.variation)
        print(f"🎨 Карт с вариациями: {variation_count}")
        
        if variation_count > 0:
            print("\nПримеры вариаций:")
            for card in [c for c in cards if c.variation][:3]:
                print(f"  • {card.name} - {card.variation}")
        
    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}")
    except ValueError as e:
        print(f"❌ Ошибка парсинга: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()