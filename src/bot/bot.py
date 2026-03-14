import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.bot.bot_handlers import start_command, help_command, handle_document, handle_text, error_handler
from src.telemetry import init_telemetry


def main():
    """
    Главная функция запуска Telegram бота Card Kingdom Order Bot.
    
    Выполняет следующие этапы инициализации:
    1. Загрузка переменных окружения из .env файла
    2. Настройка системы логирования
    3. Создание временной директории для обработки файлов
    4. Получение и валидация токена бота
    5. Инициализация Telegram Application
    6. Регистрация обработчиков команд и сообщений
    7. Вывод информации о конфигурации
    8. Запуск polling для получения обновлений
    
    Raises:
        SystemExit: При отсутствии BOT_TOKEN в переменных окружения
        Exception: При критических ошибках инициализации
    """
    # Загрузка переменных окружения (bot/.env или .env в корне)
    load_dotenv(Path(__file__).parent.parent.parent / 'bot' / '.env')
    load_dotenv()  # fallback: .env в cwd

    # Настройка логирования
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level.upper())
    )
    logger = logging.getLogger(__name__)

    # Инициализация телеметрии Monium (graceful no-op если MONIUM_API_KEY не задан)
    init_telemetry()
    
    # Создание временной директории
    temp_dir = os.getenv('TEMP_DIR', '/tmp/cards-order-bot')
    try:
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Temporary directory created: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to create temporary directory {temp_dir}: {e}")
        raise
    
    # Получение токена бота
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Инициализация Application
    logger.info("Initializing Telegram bot...")
    application = Application.builder().token(token).build()
    
    # Регистрация handlers
    logger.info("Registering handlers...")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Регистрация error handler
    application.add_error_handler(error_handler)
    
    # Вывод информации о запуске
    logger.info("=" * 40)
    logger.info("Card Kingdom Order Bot started!")
    logger.info(f"Temp directory: {temp_dir}")
    logger.info(f"Log level: {log_level}")
    logger.info("=" * 40)
    
    # Запуск polling
    application.run_polling(allowed_updates=["message"])


if __name__ == '__main__':
    main()