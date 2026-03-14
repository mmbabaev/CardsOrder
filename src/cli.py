"""CLI интерфейс для MTG Card Kingdom Order Parser."""

import logging
import sys
from pathlib import Path
from decimal import Decimal

import click

from src.parsers.parser import parse_cart_html
from src.excel_generator import generate_excel


# Настройка логирования
def setup_logging(verbose: bool) -> None:
    """Настраивает уровень логирования в зависимости от флага verbose."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


@click.group()
def cli():
    """MTG Card Kingdom Order Parser - парсинг корзины и генерация Excel заказа."""
    pass


@cli.command()
@click.argument('input_html', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    default='order.xlsx',
    help='Путь к выходному XLSX файлу (по умолчанию: order.xlsx)'
)
@click.option(
    '--fetch-codes', '-f',
    is_flag=True,
    help='Получить коды изданий с сайта (функция в разработке)'
)
@click.option(
    '--no-formulas',
    is_flag=True,
    help='Не использовать формулы, вычислить значения'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Подробный вывод'
)
@click.pass_context
def parse(ctx, input_html: str, output: str, fetch_codes: bool, no_formulas: bool, verbose: bool):
    """
    Парсит HTML файл корзины Card Kingdom и генерирует Excel заказ.
    
    INPUT_HTML - путь к HTML файлу корзины Card Kingdom
    
    Примеры использования:
    
        python main.py parse cart.html
        
        python main.py parse cart.html -o my_order.xlsx
        
        python main.py parse cart.html -o order.xlsx -v
    """
    # Настройка логирования
    setup_logging(verbose)
    
    try:
        # Валидация входного файла
        input_path = Path(input_html)
        if not input_path.exists():
            click.secho(f'✗ Ошибка: Файл не найден: {input_html}', fg='red', err=True)
            sys.exit(1)
        
        click.echo(f'Парсинг HTML файла: {input_html}')
        
        # Парсинг HTML
        try:
            cards = parse_cart_html(input_html)
        except Exception as e:
            click.secho(f'✗ Ошибка при парсинге HTML: {e}', fg='red', err=True)
            sys.exit(1)
        
        if not cards:
            click.secho('✗ Ошибка: В корзине не найдено карт', fg='red', err=True)
            sys.exit(1)
        
        click.echo(f'Найдено карт в корзине: {len(cards)}')
        
        # Предупреждение о --fetch-codes
        if fetch_codes:
            click.secho(
                '⚠ Предупреждение: Функция получения кодов изданий пока не реализована',
                fg='yellow'
            )
        
        # Генерация Excel
        click.echo(f'\nГенерация Excel файла: {output}')
        
        try:
            use_formulas = not no_formulas
            generate_excel(cards, output, use_formulas=use_formulas)
        except Exception as e:
            click.secho(f'✗ Ошибка при генерации Excel: {e}', fg='red', err=True)
            sys.exit(1)
        
        click.secho(f'✓ Excel файл успешно создан: {output}', fg='green')
        
        # Статистика
        total_quantity = sum(card.quantity for card in cards)
        total_sum = sum(card.total_price for card in cards)
        foil_count = sum(1 for card in cards if card.is_foil)
        
        click.echo('\n' + '=' * 50)
        click.echo('Статистика заказа:')
        click.echo('=' * 50)
        click.echo(f'  Всего карт:        {len(cards)}')
        click.echo(f'  Общее количество:  {total_quantity}')
        click.echo(f'  Итоговая сумма:    ${total_sum:.2f}')
        click.echo(f'  Фойлов:            {foil_count}')
        click.echo('=' * 50)
        
    except KeyboardInterrupt:
        click.echo('\n\nПрервано пользователем', err=True)
        sys.exit(130)
    except Exception as e:
        click.secho(f'\n✗ Неожиданная ошибка: {e}', fg='red', err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()