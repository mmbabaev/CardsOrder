"""Тесты для HTML парсера карточек Card Kingdom."""

import pytest
from decimal import Decimal
from pathlib import Path

from src.parser import parse_cart_html
from src.models import Card


class TestParseCartHtml:
    """Тесты для функции parse_cart_html."""
    
    def test_parse_sample_cart(self):
        """Тест парсинга примера HTML корзины."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        # Проверяем, что карточки были распарсены
        assert len(cards) > 0
        assert isinstance(cards, list)
        assert all(isinstance(card, Card) for card in cards)
    
    def test_correct_total_count(self):
        """Тест правильного общего количества карт."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        total_quantity = sum(card.quantity for card in cards)
        # В sample_cart.html должно быть 41 карта
        assert total_quantity == 41
    
    def test_correct_total_price(self):
        """Тест правильного расчета общей суммы."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        total_price = sum(card.total_price for card in cards)
        # Проверяем, что общая сумма близка к ожидаемой
        assert abs(total_price - Decimal('104.89')) < Decimal('0.01')
    
    def test_card_fields_populated(self):
        """Тест заполнения всех обязательных полей карточки."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        for card in cards:
            # Проверяем обязательные поля
            assert card.quantity > 0
            assert card.name
            assert card.url
            assert card.condition
            assert card.edition
            assert card.price_per_unit > 0
            assert card.total_price > 0
            assert card.rarity in ['C', 'U', 'R', 'M', 'S', 'L']
            assert isinstance(card.is_foil, bool)
    
    def test_foil_cards_detected(self):
        """Тест обнаружения фойловых карт."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        foil_cards = [card for card in cards if card.is_foil]
        # Проверяем, что есть хотя бы одна фойловая карта
        assert len(foil_cards) > 0
        
        # Проверяем, что фойловые карты имеют правильный формат
        for card in foil_cards:
            assert card.is_foil is True
    
    def test_variation_extraction(self):
        """Тест извлечения вариаций из названий."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        variation_cards = [card for card in cards if card.variation]
        # Должны быть карты с вариациями
        assert len(variation_cards) > 0
        
        # Проверяем формат вариаций
        for card in variation_cards:
            assert card.variation is not None
            assert len(card.variation) > 0
    
    def test_url_formatting(self):
        """Тест правильного формирования URL."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        for card in cards:
            # Все URL должны начинаться с базового URL
            assert card.url.startswith("https://www.cardkingdom.com/")
            # URL не должен иметь двойных слешей (кроме после https://)
            assert "//" not in card.url.replace("https://", "")
    
    def test_total_price_calculation(self):
        """Тест правильности расчета итоговой цены."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        for card in cards:
            expected_total = card.price_per_unit * card.quantity
            assert card.total_price == expected_total
    
    def test_rarity_extraction(self):
        """Тест извлечения редкости."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        # Проверяем, что у всех карт есть редкость
        for card in cards:
            assert card.rarity in ['C', 'U', 'R', 'M', 'S', 'L']
        
        # Проверяем, что есть карты разной редкости
        rarities = set(card.rarity for card in cards)
        assert len(rarities) > 1
    
    def test_edition_extraction(self):
        """Тест извлечения названия издания."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        for card in cards:
            # Издание не должно быть пустым
            assert card.edition
            # Издание не должно содержать редкость в скобках
            assert not card.edition.endswith(')')
    
    def test_condition_extraction(self):
        """Тест извлечения состояния карт."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        # Проверяем валидные состояния
        valid_conditions = ['NM', 'EX', 'LP', 'MP', 'HP', 'DMG']
        for card in cards:
            assert card.condition in valid_conditions
    
    def test_file_not_found(self):
        """Тест обработки отсутствующего файла."""
        with pytest.raises(FileNotFoundError):
            parse_cart_html("nonexistent_file.html")
    
    def test_empty_cart_handling(self):
        """Тест обработки пустой корзины."""
        # Создаем временный HTML файл с пустой корзиной
        empty_html = """<!doctype html>
<html>
<body>
    <div class="cartItemList">
        <div class="container-fluid cart-product-list cart-item-wrapper">
        </div>
    </div>
</body>
</html>"""
        
        temp_file = Path("tests/fixtures/empty_cart.html")
        temp_file.write_text(empty_html)
        
        try:
            cards = parse_cart_html(str(temp_file))
            assert cards == []
        finally:
            temp_file.unlink()
    
    def test_specific_cards(self):
        """Тест конкретных карт из примера."""
        html_path = "tests/fixtures/sample_cart.html"
        cards = parse_cart_html(html_path)
        
        # Проверяем наличие конкретных карт
        card_names = [card.name for card in cards]
        
        # Должны быть карты Campfire
        assert any("Campfire" in name for name in card_names)
        
        # Должны быть карты с большим количеством
        multi_quantity_cards = [card for card in cards if card.quantity > 1]
        assert len(multi_quantity_cards) > 0


class TestCardModel:
    """Тесты для модели Card."""
    
    def test_card_creation(self):
        """Тест создания объекта Card."""
        card = Card(
            quantity=2,
            name="Lightning Bolt",
            url="https://www.cardkingdom.com/mtg/secret-lair/lightning-bolt",
            is_foil=True,
            condition="NM",
            edition="Secret Lair",
            edition_code=None,
            price_per_unit=Decimal("4.99"),
            total_price=Decimal("9.98"),
            rarity="R",
            variation="1743 - Foil"
        )
        
        assert card.quantity == 2
        assert card.name == "Lightning Bolt"
        assert card.is_foil is True
        assert card.variation == "1743 - Foil"
    
    def test_card_str_representation(self):
        """Тест строкового представления карточки."""
        card = Card(
            quantity=1,
            name="Test Card",
            url="https://example.com",
            is_foil=False,
            condition="NM",
            edition="Test Edition",
            edition_code="TST",
            price_per_unit=Decimal("1.00"),
            total_price=Decimal("1.00"),
            rarity="C",
            variation=None
        )
        
        str_repr = str(card)
        assert "Test Card" in str_repr
        assert "TST" in str_repr
        assert "NM" in str_repr
    
    def test_to_excel_row(self):
        """Тест конвертации в строку Excel."""
        card = Card(
            quantity=1,
            name="Test Card",
            url="https://example.com",
            is_foil=True,
            condition="NM",
            edition="Test Edition",
            edition_code=None,
            price_per_unit=Decimal("1.00"),
            total_price=Decimal("1.00"),
            rarity="C",
            variation=None
        )
        
        row = card.to_excel_row()
        assert len(row) == 8
        assert row[0] == 1  # quantity
        assert row[1] == "Test Card"  # name
        assert row[3] == "ДА"  # foil
        assert row[4] == "NM"  # condition


if __name__ == "__main__":
    pytest.main([__file__, "-v"])