# 🎴 MTG Card Kingdom Order Parser

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Python-приложение для автоматического парсинга корзины Card Kingdom (MTG карточки) и генерации заказа в формате Excel (.xlsx).

## ✨ Основные возможности

- 📄 **Парсинг HTML** - Извлечение данных о карточках из сохраненной HTML-страницы корзины Card Kingdom
- 📊 **Генерация Excel** - Создание отформатированного файла заказа с формулами и гиперссылками
- 🎯 **Точность данных** - Корректное извлечение количества, цен, состояния, изданий и других атрибутов
- 🔗 **Гиперссылки** - Автоматическое создание кликабельных ссылок на страницы товаров
- 📈 **Формулы Excel** - Автоматический расчет итоговых сумм для каждой позиции
- 📋 **Статистика** - Вывод детальной статистики заказа (количество, сумма, фойлы)
- 💎 **Поддержка фойла** - Корректная обработка фойловых и обычных карт
- 🎨 **Форматирование** - Профессиональное оформление таблицы (жирные заголовки, авто-ширина колонок)

## 📋 Требования

- **Python 3.9+**
- Зависимости указаны в [`requirements.txt`](requirements.txt:1)

### Основные зависимости

```
beautifulsoup4==4.12.2    # HTML парсинг
lxml==4.9.3               # XML/HTML парсер
openpyxl==3.1.2           # Работа с Excel
click==8.1.7              # CLI интерфейс
```

## 🚀 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd CardsOrder
```

### 2. Создание виртуального окружения (рекомендуется)

```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. (Опционально) Установка зависимостей для разработки

```bash
pip install -r requirements-dev.txt
```

## ⚡ Быстрый старт

### Базовое использование

1. **Сохраните HTML-страницу корзины Card Kingdom**
   - Откройте корзину на сайте Card Kingdom
   - Сохраните страницу как HTML (Ctrl+S / Cmd+S)
   - Назовите файл, например, `cart.html`

2. **Запустите парсер**

```bash
python main.py parse cart.html
```

3. **Получите результат** - Файл `order.xlsx` будет создан в текущей директории

### Пример вывода

```
Парсинг HTML файла: cart.html
Найдено карт в корзине: 21

Генерация Excel файла: order.xlsx
✓ Excel файл успешно создан: order.xlsx

==================================================
Статистика заказа:
==================================================
  Всего карт:        21
  Общее количество:  41
  Итоговая сумма:    $104.89
  Фойлов:            2
==================================================
```

## 🖥️ Использование CLI

### Основная команда: `parse`

Парсит HTML файл корзины и создает Excel заказ.

```bash
python main.py parse <input_html> [OPTIONS]
```

#### Опции

| Опция | Короткая форма | Описание | По умолчанию |
|-------|----------------|----------|--------------|
| `--output` | `-o` | Путь к выходному XLSX файлу | `order.xlsx` |
| `--fetch-codes` | `-f` | Получить коды изданий с сайта | `False` (в разработке) |
| `--no-formulas` | - | Вычислить значения вместо формул | `False` |
| `--verbose` | `-v` | Подробный вывод | `False` |
| `--help` | - | Показать справку | - |

#### Примеры использования

**Простейший вариант:**
```bash
python main.py parse cart.html
```

**С указанием выходного файла:**
```bash
python main.py parse cart.html -o my_order.xlsx
```

**С подробным выводом:**
```bash
python main.py parse cart.html -o order.xlsx -v
```

**Без использования формул (вычисленные значения):**
```bash
python main.py parse cart.html --no-formulas
```

## 🎨 GUI Интерфейс

### Запуск графического интерфейса

```bash
python3 main_gui.py
```

### Возможности GUI

Приложение предоставляет удобный графический интерфейс на базе Tkinter:

#### 📂 Панель файлов
- **Выбор входного HTML** - Browse кнопка для выбора файла корзины Card Kingdom
- **Выбор выходного XLSX** - Browse кнопка для указания пути сохранения заказа
- Автоматическое предложение имени выходного файла

#### ⚙️ Панель опций
- **Use formulas in Excel** - Использовать формулы для расчета итогов (по умолчанию: ✓)
- **Verbose output** - Подробный вывод в лог-панели

#### 📋 Таблица превью
- Отображение всех распарсенных карточек в удобной таблице
- Колонки: Количество, Название, Издание, Состояние, Фойл, Цена/ед., Итого
- Прокрутка и сортировка по колонкам
- Обновляется автоматически после парсинга

#### 📊 Панель статистики
- **Total Cards** - Общее количество карточек в заказе
- **Total Price** - Итоговая сумма заказа в USD
- **Foils** - Количество фойловых карт

#### 🎯 Кнопки действий
- **📄 Parse HTML** - Парсить выбранный HTML файл и показать превью
- **📊 Generate Excel** - Создать Excel файл из распарсенных данных
- **🗑️ Clear** - Очистить все данные и начать заново

#### 📝 Лог-панель
- Отображение текущих операций и их результатов
- Подробный вывод ошибок в verbose режиме
- Автоматическая прокрутка к последним сообщениям

### Рабочий процесс в GUI

1. **Запустите приложение:** `python3 main_gui.py`
2. **Выберите HTML файл:** Нажмите "Browse..." рядом с "Input HTML"
3. **Укажите выходной файл:** Нажмите "Browse..." рядом с "Output XLSX" (опционально)
4. **Настройте опции:** Отметьте нужные чекбоксы
5. **Парсите HTML:** Нажмите "📄 Parse HTML" для предпросмотра
6. **Проверьте данные:** Просмотрите карточки в таблице и статистику
7. **Создайте Excel:** Нажмите "📊 Generate Excel"
8. **Откройте файл:** После успешного создания можно сразу открыть файл

### Скриншот интерфейса

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎴 MTG Card Kingdom Order Parser                                │
├─────────────────────────────────────────────────────────────────┤
│ ╔═══════════ Files ═══════════╗                                 │
│ ║ Input HTML:  [cart.html        ] [Browse...]                ║ │
│ ║ Output XLSX: [order.xlsx       ] [Browse...]                ║ │
│ ╚═════════════════════════════════╝                             │
│                                                                  │
│ ╔═════════ Options ═══════════╗                                 │
│ ║ ☑ Use formulas in Excel   ☐ Verbose output                 ║ │
│ ╚═════════════════════════════════╝                             │
│                                                                  │
│ ╔════════════════ Card Preview ═══════════════════════════════╗│
│ ║ Qty │ Card Name      │ Edition  │ Cond │ Foil │ Price │ Total ║│
│ ║─────┼────────────────┼──────────┼──────┼──────┼───────┼────────║│
│ ║  4  │ Lightning Bolt │ Mystery  │  NM  │ НЕТ  │ $7.99 │$31.96 ║│
│ ║  1  │ Campfire       │ CLB      │  NM  │ НЕТ  │ $0.99 │ $0.99 ║│
│ ║  2  │ Thought Scour  │ 2X2      │  NM  │ НЕТ  │ $1.49 │ $2.98 ║│
│ ╚═════════════════════════════════════════════════════════════════╝│
│                                                                  │
│ ╔════════ Order Statistics ════════╗                            │
│ ║ Total Cards: 21  Total Price: $104.89  Foils: 2            ║ │
│ ╚══════════════════════════════════╝                            │
│                                                                  │
│ [📄 Parse HTML] [📊 Generate Excel] [🗑️ Clear] [████░░] 65%    │
│                                                                  │
│ ╔══════════════════ Log ════════════════════╗                   │
│ ║ Welcome to MTG Card Kingdom Order Parser!                  ║ │
│ ║ Selected input: cart.html                                  ║ │
│ ║ Parsing cart.html...                                       ║ │
│ ║ ✓ Successfully parsed 21 cards                             ║ │
│ ║ Generating Excel file: order.xlsx...                       ║ │
│ ║ ✓ Excel file created successfully!                         ║ │
│ ╚═══════════════════════════════════════════╝                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Структура проекта

```
CardsOrder/
├── src/                          # Исходный код
│   ├── __init__.py              # Инициализация пакета
│   ├── models.py                # Модели данных (Card)
│   ├── parser.py                # HTML парсер
│   ├── excel_generator.py       # Генератор Excel
│   ├── edition_fetcher.py       # Получение кодов изданий (в разработке)
│   ├── cli.py                   # CLI интерфейс
│   └── gui/                     # GUI модуль
│       ├── __init__.py          # Инициализация GUI
│       └── app.py               # Tkinter приложение
├── tests/                        # Тесты
│   ├── test_parser.py           # Unit-тесты парсера
│   ├── test_excel_generator.py  # Unit-тесты генератора
│   ├── fixtures/                # Тестовые данные
│   │   └── sample_cart.html
│   └── e2e/                     # End-to-end тесты
│       ├── TESTING_REPORT.md    # Отчет о тестировании
│       ├── validate_output.py   # Валидация выходных файлов
│       └── validation_report.json
├── main.py                       # Точка входа CLI
├── main_gui.py                   # Точка входа GUI
├── requirements.txt              # Основные зависимости
├── requirements-dev.txt          # Зависимости для разработки
├── plan.md                       # Детальный план разработки
├── TODO.md                       # Список задач
├── .gitignore                    # Игнорируемые файлы
└── README.md                     # Документация (этот файл)
```

### Описание ключевых модулей

| Модуль | Описание | Ключевые функции |
|--------|----------|------------------|
| [`models.py`](src/models.py:1) | Модель данных `Card` с валидацией | `Card.to_excel_row()`, `Card.__str__()` |
| [`parser.py`](src/parser.py:1) | Парсинг HTML корзины Card Kingdom | `parse_cart_html()` |
| [`excel_generator.py`](src/excel_generator.py:1) | Генерация форматированного Excel | `generate_excel()` |
| [`cli.py`](src/cli.py:1) | CLI интерфейс на базе Click | `parse()` команда |
| [`gui/app.py`](src/gui/app.py:1) | GUI приложение на Tkinter | `MTGOrderParserGUI` класс |

## 📝 Примеры использования

### Пример 1: Базовый парсинг

```bash
# Сохраните страницу корзины как cart.html
python main.py parse cart.html

# Результат: order.xlsx с полным форматированием
```

**Структура выходного Excel файла:**

| Количество | Название карты | Ссылка | Фойл | Состояние | Издание | Цена за штуку (USD) | Итого: |
|-----------|----------------|--------|------|-----------|---------|---------------------|--------|
| 4 | Lightning Bolt | [ссылка] | НЕТ | NM | Mystery Booster | $7.99 | =A2*G2 |
| 1 | Campfire | [ссылка] | НЕТ | NM | Outlaws of Thunder Junction | $0.99 | =A3*G3 |
| 2 | Thought Scour | [ссылка] | НЕТ | NM | Secret Lair | $17.99 | =A4*G4 |

### Пример 2: Программное использование

```python
from src.parser import parse_cart_html
from src.excel_generator import generate_excel

# Парсинг HTML
cards = parse_cart_html('cart.html')

# Вывод информации
for card in cards:
    print(f"{card.quantity}x {card.name} - ${card.total_price}")

# Генерация Excel
generate_excel(cards, 'output.xlsx')
```

### Пример 3: Обработка данных карты

```python
from src.models import Card
from decimal import Decimal

# Создание карты вручную
card = Card(
    quantity=4,
    name="Lightning Bolt",
    url="https://www.cardkingdom.com/mtg/mystery-booster/lightning-bolt",
    is_foil=False,
    condition="NM",
    edition="Mystery Booster",
    edition_code=None,
    price_per_unit=Decimal("7.99"),
    total_price=Decimal("31.96"),
    rarity="C",
    variation=None
)

# Вывод информации
print(card)  # 4x Lightning Bolt - Mystery Booster (C) - NM - $7.99/ea (Total: $31.96)

# Конвертация в строку Excel
excel_row = card.to_excel_row()
# [4, "Lightning Bolt", "https://...", "НЕТ", "NM", "Mystery Booster", Decimal("7.99"), Decimal("31.96")]
```

## 🧪 Разработка

### Запуск unit-тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=src

# Конкретный тестовый файл
pytest tests/test_parser.py

# С подробным выводом
pytest -v
```

### Запуск e2e тестов

```bash
# Парсинг тестового файла
python main.py parse cardkingdom_card_page.html -o test_output.xlsx -v

# Валидация выходного файла
python tests/e2e/validate_output.py test_output.xlsx
```

### Покрытие тестами

По результатам тестирования ([`tests/e2e/TESTING_REPORT.md`](tests/e2e/TESTING_REPORT.md:1)):

- ✅ **Парсинг HTML:** 95.5% (21 из 22 карточек)
- ✅ **Генерация Excel:** 100%
- ✅ **Формулы:** 100% (21 из 21)
- ✅ **Гиперссылки:** 100% (21 из 21)
- ✅ **Форматирование:** 100%

### Форматирование кода

```bash
# Форматирование с Black
black src/ tests/

# Проверка типов с mypy
mypy src/
```

## ⚠️ Известные ограничения

1. **HTML-структура** - Парсер зависит от текущей структуры HTML Card Kingdom. Изменения на сайте могут потребовать обновления парсера.

2. **Коды изданий** - Функция автоматического получения короткий кодов изданий (BRO, MH3, и т.д.) пока в разработке. В текущей версии используются полные названия изданий.

3. **Динамический контент** - Требуется сохранение HTML-страницы вручную. Автоматическое извлечение через браузер (Selenium) планируется в будущих версиях.

4. **Специальные карты** - Некоторые карточки без элемента `product-link` могут быть пропущены (~4.5% согласно тестам).

5. **Offline режим** - Парсер работает только с сохраненными HTML файлами. Прямое подключение к сайту Card Kingdom не поддерживается.

## 📌 TODO (Будущие улучшения)

### Ближайшие планы

- [ ] **Получение кодов изданий** - Автоматическое извлечение коротких кодов (BRO, MH3) со страниц карточек
- [ ] **Кэширование** - Сохранение кодов изданий в `edition_codes_cache.json` для повторного использования
- [ ] **Команда update-editions** - Обновление кодов изданий в существующем Excel файле
- [ ] **Обработка токенов** - Улучшенная поддержка токенов (например, "Radiation Token // Treasure Token")

### Расширенные функции

- [x] **GUI интерфейс** - Графический интерфейс на Tkinter ✅
- [ ] **Selenium автоматизация** - Автоматическое извлечение HTML из браузера
- [ ] **Экспорт в CSV** - Дополнительный формат вывода данных
- [ ] **Группировка** - Группировка карт по изданиям в Excel
- [ ] **Статистика изданий** - Детальная аналитика по изданиям и редкости
- [ ] **Темная тема GUI** - Поддержка темной темы в интерфейсе
- [ ] **Drag & Drop** - Перетаскивание HTML файлов в GUI

Полный список задач см. в [`TODO.md`](TODO.md:1)

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 👨‍💻 Авторы

- **Разработчик:** Maksim Babaev
- **Дата создания:** Ноябрь 2025
- **Версия:** 1.0

---

## 🔗 Полезные ссылки

- [Card Kingdom](https://www.cardkingdom.com/) - Официальный сайт магазина
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - Документация парсера HTML
- [OpenPyXL Documentation](https://openpyxl.readthedocs.io/) - Документация работы с Excel
- [Click Documentation](https://click.palletsprojects.com/) - Документация CLI фреймворка

---

**📬 Вопросы и предложения:** Создайте Issue в репозитории проекта

**⭐ Нравится проект?** Поставьте звезду на GitHub!