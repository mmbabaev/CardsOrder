"""Обработчики команд и сообщений для Telegram бота Card Kingdom Order Bot."""

from telegram import Update
from telegram.ext import ContextTypes
import os
import logging
import time
from pathlib import Path
from src.parsers.parser_service import parse_and_generate
from src.file_extractor import extract_html, SUPPORTED_EXTENSIONS
from src.telemetry import record_command, record_request, record_processing, record_error, is_debug_mode, BotCommand, InputType, RequestStatus

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - приветствие пользователя.
    
    Отправляет приветственное сообщение с инструкцией по использованию.
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")
    record_command(BotCommand.START)

    welcome_text = (
        "👋 Привет! Я MTG Cart Order Bot\n\n"
        "Я помогу тебе создать Excel файл заказа из корзины MTG сайтов.\n\n"
        "🎴 Что я умею:\n"
        "✅ Принимаю страницу корзины в любом формате: .html, .webarchive (Safari), .mhtml (Chrome/Edge) или текст\n"
        "✅ Генерирую готовый Excel файл заказа\n"
        "✅ Показываю статистику заказа\n\n"
        "📤 Как использовать:\n"
        "1. Откройте корзину на сайте (Card Kingdom или Star City Games)\n"
        "2. Сохраните страницу как HTML файл\n"
        "3. Отправьте мне этот файл\n"
        "4. Получите готовый Excel заказ!\n\n"
        "📝 Команды:\n"
        "/help - Подробная справка"
    )
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help - справка по использованию бота.
    
    Отправляет подробную инструкцию.
    """
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested help")
    record_command(BotCommand.HELP)

    help_text = (
        "📖 Инструкция\n"
        "👤 Автор: @mbabaev\n\n"
        "🌐 Поддерживаемые сайты:\n"
        "• Card Kingdom (cardkingdom.com)\n"
        "• Star City Games (starcitygames.com)\n\n"
        "💻 Как сохранить страницу корзины:\n"
        "1. Откройте корзину на сайте\n"
        "2. Нажмите Ctrl+S (Cmd+S на Mac)\n"
        "3. Выберите 'Веб-страница, только HTML'\n"
        "4. Отправьте сохранённый .html файл сюда\n\n"
        "📋 Альтернативный способ (через исходный код):\n"
        "1. Откройте корзину\n"
        "2. Нажмите Ctrl+U (Cmd+Option+U на Mac)\n"
        "3. Выделите всё (Ctrl+A) и скопируйте (Ctrl+C)\n"
        "4. Вставьте текст прямо в чат\n\n"
        "⚙️ Детали:\n"
        "• Форматы: .html, .txt или текст в чат\n"
        "• Максимальный размер файла: 25 MB\n"
        "• Результат: .xlsx (Excel)\n\n"
        "❌ Частые ошибки:\n\n"
        "❗️ 'Сайт не поддерживается'\n"
        "→ Убедитесь, что это корзина Card Kingdom или Star City Games\n\n"
        "❗️ 'В корзине не найдено карт'\n"
        "→ Корзина пустая или сохранена не та страница\n\n"
        "❗️ 'Ошибка парсинга HTML'\n"
        "→ Сохраните страницу заново, выбрав 'только HTML'\n"
        "→ Попробуйте другой браузер\n\n"
        "❗️ 'Файл слишком большой'\n"
        "→ Разделите заказ на несколько частей\n\n"
        "💡 Советы:\n"
        "• Сохраняйте 'только HTML' — без картинок, файл будет меньше\n"
        "• Не редактируйте HTML вручную\n\n"
        "🆘 Проблемы? Напишите /start или свяжитесь с автором @mbabaev"
    )
    
    await update.message.reply_text(help_text)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка HTML файлов корзины.
    
    Workflow:
    1. Проверить что это .html или .txt файл
    2. Проверить размер файла
    3. Отправить статус "🎴 Обрабатываю файл..."
    4. Скачать в TEMP_DIR
    5. Вызвать parse_and_generate()
    6. Отправить Excel файл пользователю
    7. Отправить статистику
    8. Удалить временные файлы
    """
    user_id = update.effective_user.id
    document = update.message.document
    logger.info(f"Received document from user {user_id}: {document.file_name}")
    
    file_path_obj = Path(document.file_name)
    if file_path_obj.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Invalid file type: {document.file_name}")
        record_request(InputType.DOCUMENT, RequestStatus.ERROR_INVALID_TYPE)
        await update.message.reply_text(
            "❌ Неправильный тип файла\n\n"
            "Отправьте страницу корзины в одном из форматов:\n"
            "• .html — любой браузер\n"
            "• .webarchive — Safari\n"
            "• .mhtml — Chrome или Edge\n\n"
            "Используйте /help для инструкций."
        )
        return

    # Проверка размера файла
    max_file_size = int(os.getenv('MAX_FILE_SIZE', '26214400'))  # 25 MB
    if document.file_size and document.file_size > max_file_size:
        logger.warning(f"File too large: {document.file_size} bytes")
        record_request(InputType.DOCUMENT, RequestStatus.ERROR_TOO_LARGE)
        await update.message.reply_text(
            "❌ Файл слишком большой\n\n"
            f"Максимальный размер: {max_file_size / 1024 / 1024:.0f} MB\n"
            f"Размер вашего файла: {document.file_size / 1024 / 1024:.1f} MB\n\n"
            "Попробуйте:\n"
            "• Сохранить страницу 'только HTML' без картинок\n"
            "• Разделить заказ на несколько частей"
        )
        return
    
    # Отправляем статус обработки
    status_msg = await update.message.reply_text("🎴 Обрабатываю файл...")
    
    temp_dir = os.getenv('TEMP_DIR', '/tmp/cards-order-bot')
    html_file_path = None
    excel_file_path = None
    
    try:
        # Скачиваем файл
        file = await context.bot.get_file(document.file_id)
        html_file_path = os.path.join(temp_dir, f"{document.file_unique_id}.html")
        
        logger.info(f"Downloading file to {html_file_path}")
        await file.download_to_drive(html_file_path)
        
        # Парсим и генерируем Excel
        start_time = time.time()
        excel_file_path, stats = parse_and_generate(html_file_path, temp_dir)
        processing_time = time.time() - start_time
        
        logger.info(f"Processing completed in {processing_time:.1f}s: {stats}")
        record_request(InputType.DOCUMENT, RequestStatus.SUCCESS, stats.get('site_name', ''))
        record_processing(
            processing_time,
            stats.get('site_name', ''),
            stats['total_cards'],
            float(stats['total_price']),
        )

        # Отправляем Excel файл
        await status_msg.edit_text("📊 Создаю Excel файл...")

        with open(excel_file_path, 'rb') as excel_file:
            site_slug = stats.get('site_name', 'order').lower().replace(' ', '_')
            await update.message.reply_document(
                document=excel_file,
                filename=f"order_{site_slug}.xlsx",
                caption="✅ Ваш заказ готов!"
            )

        # Форматируем и отправляем статистику
        stats_text = (
            f"📊 Статистика заказа:\n\n"
            f"• Всего карт: {stats['total_cards']}\n"
            f"• Общее количество: {stats['total_quantity']}\n"
            f"• Итоговая сумма: ${stats['total_price']:.2f}\n"
            f"• Фойлов: {stats['foil_count']}\n\n"
            f"⏱ Обработано за {processing_time:.1f} секунды"
        )

        await status_msg.edit_text(stats_text)

    except FileNotFoundError:
        logger.error(f"File not found: {html_file_path}")
        record_error('file_not_found', 'Temp file missing after download',
                     input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_UNKNOWN)
        await status_msg.edit_text(
            "❌ Файл не найден\n\n"
            "Попробуйте отправить файл заново."
        )

    except ValueError as e:
        error_msg = str(e)
        logger.error(f"ValueError while processing: {error_msg}")

        if "Could not determine the website" in error_msg:
            record_error('unsupported_site', error_msg,
                         input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_UNSUPPORTED_SITE)
            await status_msg.edit_text(
                "❌ Сайт не поддерживается\n\n"
                "Поддерживаемые сайты:\n"
                "• Card Kingdom (cardkingdom.com)\n"
                "• Star City Games (starcitygames.com)\n\n"
                "Убедитесь что отправили страницу корзины с одного из этих сайтов.\n\n"
                "Используйте /help для инструкций."
            )
        elif "пустой" in error_msg.lower() or "пустая" in error_msg.lower():
            record_error('empty_cart', error_msg,
                         input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_EMPTY_CART)
            await status_msg.edit_text(
                "❌ В корзине не найдено карт\n\n"
                "Убедитесь что:\n"
                "• Корзина не пустая на сайте\n"
                "• Вы сохранили именно страницу корзины (cart)\n"
                "• HTML файл сохранен корректно\n\n"
                "Используйте /help для подробных инструкций."
            )
        else:
            record_error('parse_error', error_msg,
                         input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_PARSE)
            await status_msg.edit_text(
                f"❌ Ошибка парсинга HTML\n\n"
                f"Детали: {error_msg}\n\n"
                "Попробуйте:\n"
                "• Сохранить страницу корзины заново\n"
                "• Использовать другой браузер\n"
                "• Убедиться что сохранили 'только HTML'\n\n"
                "Используйте /help для инструкций."
            )

    except OSError as e:
        logger.error(f"OSError while processing: {e}", exc_info=True)
        record_error('os_error', str(e),
                     input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_OS)
        await status_msg.edit_text(
            "❌ Ошибка создания файла заказа\n\n"
            "Попробуйте отправить файл заново.\n"
            "Если ошибка повторяется, обратитесь к администратору."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        record_error('unknown_error', str(e),
                     input_type=InputType.DOCUMENT, status=RequestStatus.ERROR_UNKNOWN)
        await status_msg.edit_text(
            "❌ Неожиданная ошибка\n\n"
            "Попробуйте позже или напишите /help для справки.\n"
            "Если проблема повторяется, обратитесь к администратору."
        )

    finally:
        # Удаляем временные файлы
        for file_path in [html_file_path, excel_file_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Temporary file removed: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove temporary file {file_path}: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка текстовых сообщений с HTML кодом.
    
    Проверяет что текст содержит HTML код, сохраняет в файл
    и обрабатывает как в handle_document.
    """
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"Received text message from user {user_id}, length: {len(text)}")

    # Easter egg: debug builds only — typing "error" triggers a test error in telemetry
    if is_debug_mode() and text.strip().lower() == 'error':
        record_error('easter_egg', 'Debug error triggered by user message',
                     user_id=str(user_id))
        await update.message.reply_text("💥 Test error sent to telemetry!")
        return

    # Проверка что текст содержит HTML
    if not ('<html' in text.lower() or '<!doctype' in text.lower()):
        logger.info(f"Text doesn't contain HTML tags")
        await update.message.reply_text(
            "❓ Это не похоже на HTML код корзины\n\n"
            "Чтобы отправить HTML код:\n"
            "1. Откройте корзину Card Kingdom\n"
            "2. Нажмите Ctrl+U (Cmd+Option+U на Mac)\n"
            "3. Скопируйте весь текст (Ctrl+A, Ctrl+C)\n"
            "4. Отправьте мне\n\n"
            "Или используйте /help для других способов."
        )
        return
    
    # Отправляем статус обработки
    status_msg = await update.message.reply_text("🎴 Обрабатываю HTML код...")
    
    temp_dir = os.getenv('TEMP_DIR', '/tmp/cards-order-bot')
    html_file_path = None
    excel_file_path = None
    
    try:
        # Создаем временную директорию если не существует
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Сохраняем текст в HTML файл
        import uuid
        unique_id = uuid.uuid4()
        html_file_path = os.path.join(temp_dir, f"text_{unique_id}.html")
        
        logger.info(f"Saving HTML text to {html_file_path}")
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Парсим и генерируем Excel
        start_time = time.time()
        excel_file_path, stats = parse_and_generate(html_file_path, temp_dir)
        processing_time = time.time() - start_time
        
        logger.info(f"Processing completed in {processing_time:.1f}s: {stats}")
        record_request(InputType.TEXT, RequestStatus.SUCCESS, stats.get('site_name', ''))
        record_processing(
            processing_time,
            stats.get('site_name', ''),
            stats['total_cards'],
            float(stats['total_price']),
        )

        # Отправляем Excel файл
        await status_msg.edit_text("📊 Создаю Excel файл...")

        with open(excel_file_path, 'rb') as excel_file:
            site_slug = stats.get('site_name', 'order').lower().replace(' ', '_')
            await update.message.reply_document(
                document=excel_file,
                filename=f"order_{site_slug}.xlsx",
                caption="✅ Ваш заказ готов!"
            )

        # Форматируем и отправляем статистику
        stats_text = (
            f"📊 Статистика заказа:\n\n"
            f"• Всего карт: {stats['total_cards']}\n"
            f"• Общее количество: {stats['total_quantity']}\n"
            f"• Итоговая сумма: ${stats['total_price']:.2f}\n"
            f"• Фойлов: {stats['foil_count']}\n\n"
            f"⏱ Обработано за {processing_time:.1f} секунды"
        )

        await status_msg.edit_text(stats_text)

    except FileNotFoundError:
        logger.error(f"File not found: {html_file_path}")
        record_error('file_not_found', 'Temp file missing after write',
                     input_type=InputType.TEXT, status=RequestStatus.ERROR_UNKNOWN)
        await status_msg.edit_text(
            "❌ Файл не найден\n\n"
            "Попробуйте отправить HTML код заново."
        )

    except ValueError as e:
        error_msg = str(e)
        logger.error(f"ValueError while processing: {error_msg}")

        if "пустой" in error_msg.lower() or "пустая" in error_msg.lower():
            record_error('empty_cart', error_msg,
                         input_type=InputType.TEXT, status=RequestStatus.ERROR_EMPTY_CART)
            await status_msg.edit_text(
                "❌ В корзине не найдено карт\n\n"
                "Убедитесь что:\n"
                "• Вы скопировали HTML код страницы корзины (cart)\n"
                "• Корзина не пустая на сайте Card Kingdom\n"
                "• Скопировали весь HTML код целиком\n\n"
                "Используйте /help для подробных инструкций."
            )
        else:
            record_error('parse_error', error_msg,
                         input_type=InputType.TEXT, status=RequestStatus.ERROR_PARSE)
            await status_msg.edit_text(
                f"❌ Ошибка парсинга HTML\n\n"
                f"Детали: {error_msg}\n\n"
                "Попробуйте:\n"
                "• Скопировать HTML код заново\n"
                "• Убедиться что скопировали весь код\n"
                "• Отправить файл вместо текста\n\n"
                "Используйте /help для инструкций."
            )

    except OSError as e:
        logger.error(f"OSError while processing: {e}", exc_info=True)
        record_error('os_error', str(e),
                     input_type=InputType.TEXT, status=RequestStatus.ERROR_OS)
        await status_msg.edit_text(
            "❌ Ошибка создания файла заказа\n\n"
            "Попробуйте отправить HTML код заново.\n"
            "Если ошибка повторяется, обратитесь к администратору."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        record_error('unknown_error', str(e),
                     input_type=InputType.TEXT, status=RequestStatus.ERROR_UNKNOWN)
        await status_msg.edit_text(
            "❌ Неожиданная ошибка\n\n"
            "Попробуйте позже или напишите /help для справки.\n"
            "Если проблема повторяется, обратитесь к администратору."
        )
        
    finally:
        # Удаляем временные файлы
        for file_path in [html_file_path, excel_file_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Temporary file removed: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove temporary file {file_path}: {e}")


async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Easter egg: /error — fires a test error in telemetry (debug builds only)."""
    if not is_debug_mode():
        return
    user_id = update.effective_user.id
    record_error('easter_egg_command', '/error command triggered by user',
                 user_id=str(user_id))
    await update.message.reply_text("💥 Test error sent to telemetry!")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Глобальный обработчик ошибок.
    
    Логирует ошибку и отправляет пользователю понятное сообщение.
    """
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    # Если есть update с сообщением, отправляем пользователю
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса.\n\n"
                "Попробуйте:\n"
                "• Отправить файл заново\n"
                "• Перезапустить бота командой /start\n"
                "• Использовать /help для справки\n\n"
                "Если проблема повторяется, обратитесь к администратору."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")