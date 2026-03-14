# MTG Cart Order Parser

Parses MTG shopping cart HTML pages and generates a formatted Excel order file.

Supported sites: **Card Kingdom**, **Star City Games**

## Usage

### CLI

```bash
python src/main.py parse cart.html
python src/main.py parse cart.html -o my_order.xlsx -v
```

### GUI

```bash
python src/main_gui.py
```

### Telegram Bot

Send an `.html` cart file (or paste HTML text) to the bot. It auto-detects the site, parses the cart, and replies with an Excel file and order summary.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
pytest
```

## Project Structure

```
src/
  main.py               # CLI entry point
  main_gui.py           # GUI entry point
  base_parser.py        # Abstract parser base class
  site_detector.py      # Detects site and returns correct parser
  parser.py             # Public parse_cart_html() wrapper
  parser_service.py     # Orchestrates parse → Excel → stats
  excel_generator.py
  models.py
  parsers/
    card_kingdom_parser.py
    starcitygames_parser.py
  bot/
    bot.py              # Telegram bot entry point
    bot_handlers.py
  gui/
    app.py

bot/                    # Deployment artifacts
  deploy_bot_debug.sh   # Deploy debug (default) or --release
  systemd/
  requirements-bot.txt

tests/
docs/
  ARCHITECTURE.md       # Full architecture reference
```

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for component diagrams, multi-site parser design, deployment setup, and error handling.

## Adding a New Site

1. Create `src/parsers/<site>_parser.py` extending `BaseCartParser`
2. Implement `site_name`, `can_parse()`, and `parse()`
3. Register in `src/site_detector._PARSERS`
